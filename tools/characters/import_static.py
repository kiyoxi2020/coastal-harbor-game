#!/usr/bin/env python3
"""Import the audited static selection from immutable Git blobs.

This moves stored resources, not character capability or visual acceptance. The
small selection file is a durable input; the original audit is optional.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import html
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess

ROOT = 'art/characters'
SELECTION = Path(__file__).with_name('static-selection.json')
CATALOG_DEST = ROOT + '/reviews/static-candidates/catalog.json'
SKIP = {'regenerate_after_migration', 'tool_intermediate_optional_after_import'}
PATH_SUFFIX = re.compile(r'\.(?:png|json|txt|py|gd|tscn|html|md|zip|uid)$', re.I)
SHA = re.compile(r'^[0-9a-f]{64}$')
OMIT = object()


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _safe_path(value):
    path = PurePosixPath(value)
    if not value or path.is_absolute() or '..' in path.parts or '\\' in value:
        raise ValueError(f'unsafe path: {value}')
    return path.as_posix()


def _read_baseline(repo_root, baseline_ref, records):
    requests = ''.join(f'{baseline_ref}:{r["old_path"]}\n' for r in records).encode()
    result = subprocess.run(['git', '-C', str(repo_root), 'cat-file', '--batch'], input=requests, capture_output=True, check=True)
    data, offset, blobs = result.stdout, 0, {}
    for record in records:
        stop = data.index(b'\n', offset)
        header = data[offset:stop].decode()
        if header.endswith(' missing'):
            raise ValueError(f'missing baseline blob: {record["old_path"]}')
        _, kind, length = header.split()
        if kind != 'blob':
            raise ValueError(f'baseline path is not a blob: {record["old_path"]}')
        size = int(length)
        payload = data[stop + 1:stop + 1 + size]
        offset = stop + size + 2
        if _sha(payload) != record['sha256']:
            raise ValueError(f'SHA mismatch: {record["old_path"]}')
        if len(payload) != record['bytes']:
            raise ValueError(f'byte length mismatch: {record["old_path"]}')
        blobs[record['old_path']] = payload
    return blobs


def import_static(repo_root: Path, destination: Path, baseline_ref='379a9bc', inventory_path=Path('/private/tmp/coastal-static-character-inventory.json')) -> dict:
    """Copy verified static bytes and rewrite active JSON references to ROOT.

    Old JSON paths/digests that describe scripts or prior production history are
    recorded under ``historical_provenance``. They are not resolver inputs. SHA
    dictionaries that refer to retained resources bind the newly emitted bytes.
    """
    repo_root, destination = Path(repo_root), Path(destination)
    inventory_path = Path(inventory_path) if inventory_path is not None else SELECTION
    if not inventory_path.exists():
        inventory_path = SELECTION
    inventory = json.loads(inventory_path.read_text())
    records = [r for r in inventory['files'] if (r.get('proposed_destination') or '').startswith(ROOT + '/') and r['disposition'] not in SKIP]
    path_map, destinations = {}, {}
    for record in records:
        old = _safe_path(record['old_path'])
        dest = _safe_path(record['proposed_destination'])
        if not SHA.fullmatch(record.get('sha256', '')):
            raise ValueError(f'missing or invalid SHA: {old}')
        if dest in destinations and destinations[dest]['sha256'] != record['sha256']:
            raise ValueError(f'destination collision: {dest}')
        destinations.setdefault(dest, record)
        path_map[old] = dest
    blobs = _read_baseline(repo_root, baseline_ref, records)
    baseline_commit = subprocess.check_output(['git', '-C', str(repo_root), 'rev-parse', baseline_ref]).decode().strip()
    relative_map = {old: new[len(ROOT) + 1:] for old, new in path_map.items()}
    emitted, documents, processing = {}, {}, set()

    def resolve(value, old_file, pointer=""):
        if not isinstance(value, str):
            return None
        # Audit generation records used an absolute path in the original repo.
        if '/art/' in value and value.startswith('/'):
            value = 'art/' + value.split('/art/', 1)[1]
        if value in path_map:
            return value
        parent = posixpath.dirname(old_file)
        scope = pointer.rsplit('/', 1)[-1]
        scoped = 'parts' if scope == 'parts' else 'proof' if scope == 'frames' else ''
        prefixes = [posixpath.join(parent, scoped)] if scoped else []
        for prefix in prefixes + [parent, posixpath.join(parent, 'proof')]:
            candidate = posixpath.normpath(posixpath.join(prefix, value))
            if candidate in path_map:
                return candidate
        return None

    def is_path(value):
        return isinstance(value, str) and (value.startswith(('/', 'art/', 'godot2d/', '../')) or (bool(PATH_SUFFIX.search(value)) and ' ' not in value and '\n' not in value))

    def emit(old_file):
        dest = path_map[old_file]
        if dest in emitted:
            return emitted[dest]
        if old_file in processing:
            raise ValueError(f'cyclic static JSON hash dependency: {old_file}')
        processing.add(old_file)
        data = blobs[old_file]
        if old_file.endswith('.json'):
            original = json.loads(data)
            history = []

            def remember(pointer, value, reason):
                history.append({'pointer': pointer, 'value': value, 'reason': reason})

            def rewrite(value, pointer=''):
                if isinstance(value, dict):
                    out = {}
                    for key, child in value.items():
                        point = pointer + '/' + key
                        if key in ('artifact_digest', 'build_artifact_digest', 'candidate_digest', 'generated_path', 'directory', 'script', 'builder', 'head_proof', 'generation_input_backup'):
                            remember(point, child, 'original production identity; not an active library input')
                            continue
                        target = resolve(key, old_file, pointer)
                        if target:
                            new_key = relative_map[target]
                            if isinstance(child, str) and SHA.fullmatch(child):
                                # A source assertion cannot silently change during a move.
                                if child != _sha(blobs[target]):
                                    raise ValueError(f'SHA mismatch in {old_file}: {key}')
                                out[new_key] = _sha(emit(target))
                            else:
                                transformed = rewrite(child, point)
                                if transformed is not OMIT:
                                    out[new_key] = transformed
                        elif is_path(key):
                            remember(point, child, 'historical file or tool outside retained static resources')
                        else:
                            transformed = rewrite(child, point)
                            if transformed is not OMIT:
                                out[key] = transformed
                    return out
                if isinstance(value, list):
                    return [new for i, child in enumerate(value) if (new := rewrite(child, pointer + '/' + str(i))) is not OMIT]
                if isinstance(value, str):
                    target = resolve(value, old_file, pointer)
                    if target:
                        return relative_map[target]
                    if is_path(value):
                        active = {'source', 'prompt', 'body_template', 'previews', 'components', 'owners', 'semantics', 'protected', 'reference_images', 'registered_file', 'mask', 'file'}
                        if any(piece in active for piece in pointer.split('/')) and not old_file.startswith('art/design/character-library-v1/'):
                            raise ValueError(f'unmapped resource in {old_file}: {value}')
                        remember(pointer, value, 'historical external/output path; no active resolution')
                        return OMIT
                return value

            # Small original review records are evidence, never active manifests.
            if destinations[dest]['disposition'] == 'keep_original_scope_record':
                document = {'kind': 'historical-scope-record', 'historical_provenance': {'original_document': original}}
            else:
                document = rewrite(original)
                if not isinstance(document, dict):
                    document = {'kind': 'generation-instructions', 'jobs': document}
                document['resource_root'] = ROOT
            document.setdefault('historical_provenance', {}).update({'baseline_commit': baseline_commit, 'old_path': old_file, 'old_sha256': _sha(data)})
            if history:
                document['historical_provenance']['references'] = history
            if dest == CATALOG_DEST:
                for category, entries in document['categories'].items():
                    for entry in entries:
                        entry['resource_kind'] = 'static-candidate'
                        entry['motion_compatible'] = False
                        entry['category'] = category
                document['kind'] = 'static-candidate-catalog'
                document['scope'] = original.get('scope', '')
            documents[dest] = document
            data = _json_bytes(document)
        processing.remove(old_file)
        emitted[dest] = data
        return data

    for old in path_map:
        emit(old)
    catalog = documents.get(CATALOG_DEST)
    if catalog is None:
        raise ValueError('static catalog missing from selection')
    candidates = [entry for group in catalog['categories'].values() for entry in group]
    expected_count = inventory.get('candidate_count', inventory.get('summary', {}).get('candidate_count', len(candidates)))
    if len(candidates) != expected_count or len({entry['design_id'] for entry in candidates}) != expected_count:
        raise ValueError('static candidate identity/count mismatch')
    if any(entry['status'] != 'candidate' for entry in candidates):
        raise ValueError('static candidate status changed')
    aliases = defaultdict(list)
    files = []
    for record in records:
        old, new = record['old_path'], record['proposed_destination']
        aliases[new].append(old)
        files.append({'old_path': old, 'new_path': new, 'old_sha256': record['sha256'], 'new_sha256': _sha(emitted[new]), 'old_bytes': record['bytes'], 'new_bytes': len(emitted[new]), 'disposition': record['disposition'], 'classification': 'rewritten-metadata' if old.endswith('.json') else 'unchanged-resource'})
    result = {'path_map': path_map, 'files': files, 'candidates': candidates, 'catalog': catalog, 'aliases': {new: paths for new, paths in aliases.items() if len(paths) > 1}}
    # Build all output in memory before writing, so invalid inputs leave no import.
    for new, payload in emitted.items():
        path = destination / new[len(ROOT) + 1:]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    index = {'schema_version': 1, 'resource_root': ROOT, 'kind': 'static-import-index', 'baseline_commit': baseline_commit, 'candidate_count': len(candidates), 'categories': {key: len(group) for key, group in catalog['categories'].items()}, 'selected_template': {'template_id': 'adult-standard-v1', 'active_revision': 'directional-brows-v3'}, 'candidates': [{'id': e['id'], 'design_id': e['design_id'], 'category': e['category'], 'resource_kind': 'static-candidate', 'status': e['status'], 'compatibility': e['compatibility'], 'source': e.get('source')} for e in candidates], 'historical_provenance': {'aliases': result['aliases']}, 'scope': 'storage migration only; complete static frames are not hidden bodies or motion adaptations'}
    (destination / 'static-index.json').write_bytes(_json_bytes(index))
    # Self-contained gallery: paths are relative to its physical location.
    cards = []
    for entry in candidates:
        images = ''.join(f'<img loading="lazy" src="../../{html.escape(path, quote=True)}" alt="{html.escape(direction)}">' for direction, path in entry.get('previews', {}).items())
        cards.append(f'<article><h2>{html.escape(entry["id"])} {html.escape(entry.get("label", ""))}</h2><p>candidate · standing_0 · static only</p>{images}</article>')
    gallery = '<!doctype html><meta charset="utf-8"><title>Static candidates</title><style>body{background:#17232d;color:#eee;font:16px sans-serif}article{margin:16px;padding:12px;background:#263843}img{width:180px;image-rendering:pixelated}h2{font-size:18px}</style><h1>Static candidates</h1><p>Existing static candidates. This gallery does not grant motion compatibility or visual acceptance.</p>' + ''.join(cards)
    (destination / 'reviews/static-candidates/gallery.html').write_text(gallery)
    derived = ['static-index.json', 'reviews/static-candidates/gallery.html']
    source_groups = defaultdict(list)
    for new, payload in emitted.items():
        relative = new[len(ROOT) + 1:]
        parts = PurePosixPath(relative).parts
        if len(parts) >= 3 and parts[0] == 'sources':
            source_groups[parts[1]].append({'file': relative, 'sha256': _sha(payload), 'bytes': len(payload)})
    for identity, assets in source_groups.items():
        relative = f'sources/{identity}/source.json'
        (destination / relative).write_bytes(_json_bytes({'resource_root': ROOT, 'source_id': identity, 'assets': sorted(assets, key=lambda a: a['file']), 'scope': 'retained static generation/reference inputs; not additional designs or motion capability'}))
        derived.append(relative)
    migration = destination / 'migrations/2026-10-resource-layout/static-inventory.json'
    migration.parent.mkdir(parents=True, exist_ok=True)
    migration.write_bytes(_json_bytes({'schema_version': 1, 'kind': 'static-resource-migration', 'baseline_commit': baseline_commit, 'resource_root': ROOT, 'candidate_count': len(candidates), 'path_map': path_map, 'files': files, 'aliases': result['aliases'], 'derived_files': [{'new_path': ROOT + '/' + path, 'new_sha256': _sha((destination / path).read_bytes())} for path in sorted(derived)]}))
    return result


def verify_static(repo_root: Path, destination: Path | None = None) -> dict:
    """Verify imported bytes, active root-relative references and static scope."""
    current_library = destination is None
    destination = Path(destination) if destination is not None else Path(repo_root) / ROOT
    manifest = json.loads((destination / 'migrations/2026-10-resource-layout/static-inventory.json').read_text())
    if current_library:
        from organize_library import historical_binding
    verified = set()
    for record in manifest['files'] + manifest.get('derived_files', []):
        new = _safe_path(record['new_path'])
        if not new.startswith(ROOT + '/'):
            raise ValueError('resource path outside library: ' + new)
        expected = record['new_sha256']
        if current_library:
            new, expected = historical_binding(repo_root, new, expected)
        path = destination / new[len(ROOT) + 1:]
        if not path.is_file() or _sha(path.read_bytes()) != expected:
            raise ValueError('imported resource SHA mismatch: ' + new)
        verified.add(path)
    references = 0
    prefixes = ('sources/', 'templates/', 'parts/', 'builds/', 'reviews/', 'evidence/')

    def resource(value):
        nonlocal references
        _safe_path(value)
        path = destination / value
        if not path.is_file():
            raise ValueError('missing active static resource: ' + value)
        references += 1
        return path

    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key == 'historical_provenance':
                    continue
                if isinstance(key, str) and key.startswith(prefixes):
                    path = resource(key)
                    if isinstance(child, str) and SHA.fullmatch(child) and _sha(path.read_bytes()) != child:
                        raise ValueError('active static input SHA mismatch: ' + key)
                if key == 'file' and isinstance(child, str) and child.startswith(prefixes) and 'sha256' in value:
                    if _sha(resource(child).read_bytes()) != value['sha256']:
                        raise ValueError('active static input SHA mismatch: ' + child)
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, str) and value.startswith(prefixes):
            resource(value)

    for path in verified:
        if path.suffix == '.json':
            document = json.loads(path.read_text())
            if document.get('resource_root', ROOT) != ROOT:
                raise ValueError('unknown static resource root')
            walk(document)
    catalog = json.loads((destination / 'reviews/static-candidates/catalog.json').read_text())
    entries = [entry for group in catalog['categories'].values() for entry in group]
    if len(entries) != manifest['candidate_count'] or any(e['status'] != 'candidate' or e['resource_kind'] != 'static-candidate' or e['motion_compatible'] for e in entries):
        raise ValueError('static candidate scope changed')
    return {'passed': True, 'mapped_files': len(manifest['files']), 'physical_files': len({r['new_path'] for r in manifest['files']}), 'derived_files': len(manifest.get('derived_files', [])), 'candidates': len(entries), 'active_references': references}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    parser.add_argument('--repo-root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--destination', type=Path)
    parser.add_argument('--baseline-ref', default='379a9bc')
    parser.add_argument('--inventory', type=Path, default=SELECTION)
    args = parser.parse_args()
    if args.verify:
        print(json.dumps(verify_static(args.repo_root, args.destination)))
        return
    result = import_static(args.repo_root, args.destination or args.repo_root / ROOT, args.baseline_ref, args.inventory)
    print(json.dumps({'candidates': len(result['candidates']), 'mapped_files': len(result['files']), 'physical_files': len(set(result['path_map'].values()))}))


if __name__ == '__main__':
    main()
