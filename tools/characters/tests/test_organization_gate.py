"""A relocation receipt proves dependency equivalence, rather than grants it."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import organize_library as organization


class OrganizationGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='coastal-organization-gate-', dir='/private/tmp')
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.mapping = {'parts/top03/': 'parts/top/top03/'}
        self.original = {
            'art/characters/parts/top03/source.json': organization.encoded({'file': 'parts/top03/image.png', 'enabled': True}),
            'art/characters/parts/top03/image.png': b'original image',
        }
        self.source_sha = organization.digest(self.original['art/characters/parts/top03/source.json'])
        self.recipe = 'art/characters/recipes/legacy/r001.json'
        self.original[self.recipe] = organization.encoded({'inputs': {'parts/top03/source.json': self.source_sha}, 'enabled': True})
        for path, payload in self.original.items():
            self.write(path, payload)
        self.engine_path = 'tools/characters/build_contract.py'
        self.engine_old = b'original construction engine'
        self.write(self.engine_path, self.engine_old)
        self.git('init', '-q')
        self.git('add', '.')
        self.git('-c', 'user.name=Gate Test', '-c', 'user.email=gate@example.invalid', 'commit', '-qm', 'original')
        self.commit = self.git('rev-parse', 'HEAD').decode().strip()

    def git(self, *arguments):
        return subprocess.check_output(['git', '-C', str(self.repo), *arguments], stderr=subprocess.STDOUT)

    def write(self, path, payload):
        destination = self.repo / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)

    def migrate(self, source_change=None, recipe_change=None, extra_hashes=None):
        source = json.loads(self.original['art/characters/parts/top03/source.json'])
        source['file'] = 'parts/top/top03/image.png'
        if source_change: source_change(source)
        source_bytes = organization.encoded(source)
        hashes = {self.source_sha: organization.digest(source_bytes), **(extra_hashes or {})}
        recipe = {'inputs': {'parts/top/top03/source.json': organization.digest(source_bytes)}, 'enabled': True}
        if recipe_change: recipe_change(recipe)
        current = {
            'art/characters/parts/top/top03/source.json': source_bytes,
            'art/characters/parts/top/top03/image.png': b'original image',
            self.recipe: organization.encoded(recipe),
        }
        rows = {}
        for old, payload in self.original.items():
            new = organization.replace_path(old, self.mapping)
            self.write(new, current[new])
            rows[old] = {'old_sha256': organization.digest(payload), 'new_path': new,
                         'new_sha256': organization.digest(current[new])}
            if rows[old]['new_sha256'] != rows[old]['old_sha256']:
                hashes[rows[old]['old_sha256']] = rows[old]['new_sha256']
        data = {'baseline_commit': self.commit, 'files': rows, 'path_prefixes': self.mapping, 'hash_updates': hashes}
        self.write(organization.RECEIPT, organization.encoded(data))
        return data

    def verify(self):
        return organization.verify_legacy_binding(self.repo, self.recipe, organization.digest(self.original[self.recipe]))

    def test_valid_transitive_path_and_sha_relocation_is_accepted(self):
        self.migrate()
        self.assertEqual(self.verify()[0], self.recipe)

    def test_changed_source_semantics_cannot_be_laundered_through_its_sha(self):
        self.migrate(source_change=lambda value: value.update(enabled=False))
        with self.assertRaisesRegex(ValueError, 'semantic|relocation'):
            self.verify()

    def test_unknown_sha_update_is_rejected(self):
        old, new = '1' * 64, '2' * 64
        original = json.loads(self.original[self.recipe]); original['identity'] = old
        self.original[self.recipe] = organization.encoded(original)
        self.write(self.recipe, self.original[self.recipe])
        self.git('add', '.'); self.git('-c', 'user.name=Gate Test', '-c', 'user.email=gate@example.invalid', 'commit', '-qm', 'identity')
        self.commit = self.git('rev-parse', 'HEAD').decode().strip()
        self.migrate(recipe_change=lambda value: value.update(identity=new), extra_hashes={old: new})
        with self.assertRaisesRegex(ValueError, 'Unknown|unproven|Unproven'):
            self.verify()

    def test_dependency_change_after_cached_verification_is_detected(self):
        self.migrate(); self.verify()
        self.write('art/characters/parts/top/top03/source.json', b'{}')
        with self.assertRaisesRegex(ValueError, 'differs|SHA|hash'):
            self.verify()

    def test_recorded_destination_must_match_declared_path_mapping(self):
        data = self.migrate()
        row = data['files']['art/characters/parts/top03/source.json']
        alternate = 'art/characters/parts/pants/top03/source.json'
        self.write(alternate, (self.repo / row['new_path']).read_bytes())
        row['new_path'] = alternate
        self.write(organization.RECEIPT, organization.encoded(data))
        with self.assertRaisesRegex(ValueError, 'destination|mapping'):
            self.verify()

    def test_explicit_engine_hash_is_bound_to_its_actual_git_and_current_bytes(self):
        old, current = organization.digest(self.engine_old), b'reviewed construction engine'
        original = json.loads(self.original[self.recipe]); original['engine_sha'] = old
        self.original[self.recipe] = organization.encoded(original)
        self.write(self.recipe, self.original[self.recipe])
        self.git('add', '.'); self.git('-c', 'user.name=Gate Test', '-c', 'user.email=gate@example.invalid', 'commit', '-qm', 'engine dependency')
        self.commit = self.git('rev-parse', 'HEAD').decode().strip()
        new = organization.digest(current)
        self.write(self.engine_path, current)
        self.migrate(recipe_change=lambda value: value.update(engine_sha=new), extra_hashes={old: new})
        self.verify()
        self.write(self.engine_path, b'another engine change')
        with self.assertRaisesRegex(ValueError, 'engine SHA'):
            self.verify()

    def test_changed_receipt_is_not_hidden_by_parse_cache(self):
        data = self.migrate(); self.verify()
        data['hash_updates']['1' * 64] = '2' * 64
        self.write(organization.RECEIPT, organization.encoded(data))
        with self.assertRaisesRegex(ValueError, 'Unknown'):
            self.verify()

    def test_unused_engine_hash_claim_must_still_match_actual_code(self):
        self.migrate(extra_hashes={organization.digest(self.engine_old): '2' * 64})
        with self.assertRaisesRegex(ValueError, 'engine SHA'):
            self.verify()

    def test_boolean_to_integer_change_remains_a_semantic_change(self):
        self.migrate(recipe_change=lambda value: value.update(enabled=1))
        with self.assertRaisesRegex(ValueError, 'semantic'):
            self.verify()

    def test_changed_binary_cannot_receive_a_relocation_hash(self):
        data = self.migrate()
        original = 'art/characters/parts/top03/image.png'
        row = data['files'][original]
        changed = b'changed image pixels'
        self.write(row['new_path'], changed)
        row['new_sha256'] = organization.digest(changed)
        data['hash_updates'][row['old_sha256']] = row['new_sha256']
        self.write(organization.RECEIPT, organization.encoded(data))
        with self.assertRaisesRegex(ValueError, 'binary changed'):
            organization.verify_legacy_binding(self.repo, original, row['old_sha256'])

    def test_historical_snapshot_keeps_exact_origin_bytes(self):
        path = 'art/characters/sources/test/source.snapshot.json'
        original = b'{"file":"parts/top03/image.png"}'
        self.write(path, original)
        self.git('add', '.'); self.git('-c', 'user.name=Gate Test', '-c', 'user.email=gate@example.invalid', 'commit', '-qm', 'historical snapshot')
        self.commit = self.git('rev-parse', 'HEAD').decode().strip()
        data = self.migrate()
        changed = organization.encoded(json.loads(original))
        old_sha, new_sha = organization.digest(original), organization.digest(changed)
        self.write(path, changed)
        data['files'][path] = {'old_sha256': old_sha, 'new_path': path, 'new_sha256': new_sha}
        data['hash_updates'][old_sha] = new_sha
        self.write(organization.RECEIPT, organization.encoded(data))
        with self.assertRaisesRegex(ValueError, 'snapshot|historical'):
            organization.verify_legacy_binding(self.repo, path, old_sha)
