"""Content-preserving library relocation and explicit historical receipt bridge.

This is a path migration, never a source repair or a production-baseline refresh.
Historical reports and executable-source snapshots are deliberately opaque.
"""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess

RECEIPT = 'art/characters/migrations/2026-10-30-organization.json'
SHA = re.compile(r'^[0-9a-f]{64}$')


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def replace_path(value, mappings):
    for prefix in ('art/characters/', ''):
        for old, new in sorted(mappings.items(), key=lambda item: -len(item[0])):
            if value.startswith(prefix + old):
                return prefix + new + value[len(prefix + old):]
    return value


def opaque(path):
    return (path.startswith(('evidence/', 'migrations/')) or
            path.endswith(('.snapshot.json', '.authoring-code.json')))


def rewrite_documents(files, mappings, hash_updates=None, identities=None):
    """Return a new file map; resolve SHA edges before serializing their owners.

    Only exact digest tokens and root-relative paths change. Binary payloads,
    prose, historical provenance and code snapshots are never transformed.
    """
    hash_updates = dict(hash_updates or {})
    identities = identities or {}
    destinations = {}
    for path in files:
        target = replace_path(path, mappings)
        if target in destinations:
            raise ValueError('Migration destination collision: ' + target)
        destinations[target] = path
    hashes = defaultdict(list)
    for path, payload in files.items():
        hashes[digest(payload)].append(path)
    emitted, visiting, resolved_hashes, mapped_paths = {}, set(), {}, {}
    roots = tuple({prefix + key.split('/')[0] + '/' for key in mappings for prefix in ('', 'art/characters/')})

    def mapped(value):
        if not value.startswith(roots):
            return value
        if value not in mapped_paths:
            mapped_paths[value] = replace_path(value, mappings)
        return mapped_paths[value]

    def new_hash(old):
        if old in resolved_hashes:
            return resolved_hashes[old]
        if old in hash_updates:
            return hash_updates[old]
        if old in identities:
            marker = 'identity:' + old
            if marker in visiting:
                raise ValueError('Cyclic source identity: ' + old)
            visiting.add(marker)
            resolved_hashes[old] = digest(json.dumps(walk(identities[old]), sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode())
            visiting.remove(marker)
            return resolved_hashes[old]
        if old not in hashes:
            return old
        values = {digest(emit(path)) for path in hashes[old]}
        if len(values) != 1:
            raise ValueError('Ambiguous shared source hash: ' + old)
        resolved_hashes[old] = values.pop()
        return resolved_hashes[old]

    def walk(value):
        if isinstance(value, dict):
            return {mapped(key): child if key == 'historical_provenance' else walk(child)
                    for key, child in value.items()}
        if isinstance(value, list):
            return [walk(child) for child in value]
        if isinstance(value, str):
            return new_hash(value) if SHA.fullmatch(value) else mapped(value)
        return value

    def emit(path):
        if path in emitted:
            return emitted[path]
        if path in visiting:
            raise ValueError('Cyclic migration digest dependency: ' + path)
        visiting.add(path)
        payload = files[path]
        if path.endswith('.json') and not opaque(path):
            original = json.loads(payload)
            historical = isinstance(original, dict) and original.get('kind') in {'coastal-recipe-authoring-snapshot-v1', 'coastal-registered-recipe-assembly-provenance-v1'}
            updated = original if historical else walk(original)
            if updated != original:
                payload = encoded(updated)
        visiting.remove(path)
        emitted[path] = payload
        return payload

    return {replace_path(path, mappings): emit(path) for path in files}


ENGINE_PATHS = tuple('tools/characters/' + name for name in
                     ('build.py', 'build_contract.py', 'composition_contract.py'))
_RECEIPT_CACHE = {}


def _library_path(path):
    if (not isinstance(path, str) or not path.startswith('art/characters/') or
            any(part in {'', '.', '..'} for part in path.split('/')) or
            '\\' in path or ':' in path):
        raise ValueError('Invalid relocation library path: ' + str(path))
    return path


def _current_bytes(repo, path):
    target = repo / path
    if any(node.is_symlink() for node in [target, *target.parents]):
        raise ValueError('Relocation symlink forbidden: ' + path)
    if not target.is_file():
        raise ValueError('Frozen legacy relocation differs: ' + path)
    return target.read_bytes()


class _ReceiptState:
    """Cache immutable origin bytes, never the validity of mutable outputs."""
    def __init__(self, repo, data):
        self.repo, self.data, self.origins = repo, data, {}
        self.prepared = False

    def prepare(self):
        if self.prepared:
            return
        data = self.data
        self.by_sha = defaultdict(list)
        for path, row in data['files'].items():
            _library_path(path); _library_path(row['new_path'])
            if not SHA.fullmatch(row['old_sha256']) or not SHA.fullmatch(row['new_sha256']):
                raise ValueError('Invalid relocation SHA: ' + path)
            relative = path.removeprefix('art/characters/')
            if row['new_path'] != 'art/characters/' + replace_path(relative, data['path_prefixes']):
                raise ValueError('Relocation destination does not match declared mapping: ' + path)
            self.by_sha[row['old_sha256']].append(path)
        if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', data['baseline_commit']):
            raise ValueError('Relocation Git origin must be an immutable commit')
        # One batched Git read amortizes all legacy checks. Binary origins are
        # loaded lazily; unchanged PNGs never need to be read from Git.
        self._read_origins([path for path in data['files'] if path.endswith('.json')] + list(ENGINE_PATHS))
        self.engines = {}
        for path in ENGINE_PATHS:
            old = self.origins.get(path)
            if old is not None:
                self.engines.setdefault(digest(old), []).append(path)
        for old, new in data['hash_updates'].items():
            if not SHA.fullmatch(old) or not isinstance(new, str) or not SHA.fullmatch(new):
                raise ValueError('Invalid relocation hash update')
            candidates = self.by_sha.get(old, [])
            if not candidates and old not in self.engines:
                raise ValueError('Unknown unproven relocation hash update: ' + old)
            if candidates and any(data['files'][path]['new_sha256'] != new for path in candidates):
                raise ValueError('Relocation hash update disagrees with recorded file: ' + old)
        self.prepared = True

    def _read_origins(self, paths):
        paths = [path for path in paths if path not in self.origins]
        if not paths:
            return
        request = ''.join(self.data['baseline_commit'] + ':' + path + '\n' for path in paths).encode()
        output = subprocess.check_output(['git', 'cat-file', '--batch'], input=request, cwd=self.repo)
        offset = 0
        for path in paths:
            end = output.index(b'\n', offset)
            header = output[offset:end].split(); offset = end + 1
            if header[-1] == b'missing':
                self.origins[path] = None
                continue
            if len(header) != 3 or header[1] != b'blob':
                raise ValueError('Relocation Git origin is not a blob: ' + path)
            size = int(header[2])
            self.origins[path] = output[offset:offset + size]; offset += size + 1

    def origin(self, path):
        self._read_origins([path])
        value = self.origins[path]
        if value is None:
            raise ValueError('Missing frozen legacy Git origin: ' + path)
        return value


def _receipt_state(repo):
    repo = Path(repo).resolve()
    path = repo / RECEIPT
    if not path.exists():
        return None
    payload = path.read_bytes()
    key = (str(repo), digest(payload))
    if key not in _RECEIPT_CACHE:
        state = _ReceiptState(repo, json.loads(payload))
        if len(_RECEIPT_CACHE) >= 8:
            _RECEIPT_CACHE.clear()
        _RECEIPT_CACHE[key] = state
    return _RECEIPT_CACHE[key]


def receipt(repo):
    state = _receipt_state(repo)
    return state.data if state is not None else None


def _historical_binding(state, path, sha):
    if state is None:
        return path, sha
    row = state.data['files'].get(path)
    if row is None:
        return path, sha
    if row['old_sha256'] != sha:
        raise ValueError('Historical SHA does not match relocation origin: ' + path)
    _library_path(row['new_path'])
    return row['new_path'], row['new_sha256']


def historical_binding(repo, path, sha):
    """Resolve only an explicitly recorded old path+SHA, never a loose alias."""
    return _historical_binding(_receipt_state(repo), path, sha)


def verify_legacy_binding(repo, path, expected):
    """Prove a frozen legacy file and every changed SHA dependency equivalent.

    Receipt SHA substitutions are claims. A referenced substitution must be
    justified by the actual Git origin and current file, recursively. Only the
    three explicit construction-engine paths may change executable content.
    """
    repo = Path(repo).resolve()
    state = _receipt_state(repo)
    if state is not None:
        state.prepare()
        for old, paths in state.engines.items():
            if old in state.data['hash_updates']:
                for engine_path in paths:
                    if digest(_current_bytes(repo, engine_path)) != state.data['hash_updates'][old]:
                        raise ValueError('Relocation engine SHA differs: ' + engine_path)
    checked, visiting = {}, set()

    def tokens(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key != 'historical_provenance':
                    yield from tokens(child)
        elif isinstance(value, list):
            for child in value: yield from tokens(child)
        elif isinstance(value, str) and SHA.fullmatch(value):
            yield value

    def prove_hash(old):
        new = state.data['hash_updates'][old]
        if old in state.by_sha:
            for original_path in state.by_sha[old]:
                if prove_file(original_path, old)[1] != new:
                    raise ValueError('Unproven relocation dependency hash: ' + old)
        elif old in state.engines:
            for engine_path in state.engines[old]:
                if digest(_current_bytes(repo, engine_path)) != new:
                    raise ValueError('Relocation engine SHA differs: ' + engine_path)
        else:
            raise ValueError('Unknown unproven relocation hash update: ' + old)
        return new

    def prove_file(original_path, original_sha):
        if original_path in checked:
            return checked[original_path]
        if original_path in visiting:
            raise ValueError('Cyclic legacy relocation dependency: ' + original_path)
        new_path, new_sha = _historical_binding(state, original_path, original_sha)
        payload = _current_bytes(repo, new_path)
        if digest(payload) != new_sha:
            raise ValueError('Frozen legacy relocation SHA differs: ' + original_path)
        if (new_path, new_sha) == (original_path, original_sha):
            checked[original_path] = (new_path, new_sha)
            return checked[original_path]
        visiting.add(original_path)
        old = state.origin(original_path)
        if digest(old) != original_sha:
            raise ValueError('Frozen legacy Git origin differs: ' + original_path)
        if not original_path.endswith('.json'):
            if payload != old:
                raise ValueError('Legacy binary changed during relocation: ' + original_path)
        else:
            original = json.loads(old)
            relative = original_path.removeprefix('art/characters/')
            historical = (opaque(relative) or isinstance(original, dict) and original.get('kind') in
                          {'coastal-recipe-authoring-snapshot-v1', 'coastal-registered-recipe-assembly-provenance-v1'})
            if historical:
                if payload != old:
                    raise ValueError('Legacy historical snapshot changed: ' + original_path)
            else:
                updates = {token: prove_hash(token) for token in set(tokens(original))
                           if token in state.data['hash_updates']}
                rewritten = rewrite_documents({relative: old}, state.data['path_prefixes'], updates)
                canonical = lambda value: json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)
                if canonical(json.loads(next(iter(rewritten.values())))) != canonical(json.loads(payload)):
                    raise ValueError('Legacy semantic change is not a relocation: ' + original_path)
        visiting.remove(original_path)
        checked[original_path] = (new_path, new_sha)
        return checked[original_path]

    return prove_file(path, expected)


def source_identities(files):
    """Expose virtual SHA nodes from typed source identities, checking the origin."""
    docs = {path: json.loads(payload) for path, payload in files.items() if path.endswith('.json')}
    result = {}
    def add(basis, expected):
        actual = digest(json.dumps(basis, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode())
        if actual != expected:
            raise ValueError('Original source identity is not valid: ' + expected)
        result[expected] = basis
    for path, recipe in docs.items():
        if not path.startswith('recipes/') or not isinstance(recipe,dict) or recipe.get('schema_version') != 2 or 'adaptations' not in recipe:
            continue
        catalogs = {slot: {view['view_id']:view for view in docs[ref['file']]['views']}
                    for slot, ref in recipe['adaptations'].items()}
        for clip in recipe['clips']:
            for frame in clip['frames']:
                selected = {layer['id']: catalogs[layer['slot']][layer['view_binding']['view_id']] for layer in frame['layers']}
                near, far, under = selected['near_hat'], selected.get('far_hat'), selected['under_hat_hair']
                basis = {key:near[key] for key in ('source','source_bundle','source_pose','canvas_px','root_anchor_px','extraction')}
                basis.update(kind='coastal-hat-source-identity-v1', whole_ownership=frame['compatibility']['hat_ownership'], near_ownership=near['source_ownership'], far_ownership=far['source_ownership'] if far else None)
                add(basis, frame['compatibility']['hat_identity_sha256'])
                claim = docs[under['compatibility']['file']]
                basis = {key:under[key] for key in ('source','source_bundle','source_pose','canvas_px','root_anchor_px','source_ownership','extraction')}
                basis['kind'] = 'coastal-component-source-identity-v1'
                add(basis, claim['hair_identity_sha256'])
    return result
