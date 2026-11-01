"""Static imports preserve identity, source closure and reproducible bytes."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'import_static.py'


def sha(data):
    return hashlib.sha256(data).hexdigest()


class StaticImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='coastal-static-')
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        self.payloads = {
            'old/body.png': b'complete clothed static body',
            'old/pants08/rejected/skirt-waist/source.png': b'necessary rejected reference',
            'old/style02.png': b'same filename different design two',
            'old/style03.png': b'same filename different design three',
        }
        candidates = []
        for identity, old in [('body02', 'old/body.png'), ('pants08', 'old/pants08/rejected/skirt-waist/source.png'), ('top02', 'old/style02.png'), ('top03', 'old/style03.png')]:
            candidates.append({'id': identity, 'design_id': identity, 'status': 'candidate', 'source': old, 'compatibility': {'body_ids': [identity if identity.startswith('body') else 'body01'], 'pose': 'standing_0'}, 'hashes': {old: sha(self.payloads[old])}})
        self.payloads['old/catalog.json'] = json.dumps({'categories': {'body': candidates[:1], 'pants': candidates[1:2], 'top': candidates[2:]}}).encode()
        destinations = ['templates/body02-candidate-v1/revisions/static-candidate-v1/body-atlas.png', 'sources/static-pants08-waist-reference-v1/source.png', 'parts/top/top02/static/source.png', 'parts/top/top03/static/source.png', 'reviews/static-candidates/catalog.json']
        self.inventory = {'schema_version': 1, 'selected_template': {'active_revision': {'id': 'directional-brows-v3'}}, 'candidates': candidates, 'files': []}
        for (old, data), dest in zip(self.payloads.items(), destinations):
            p = self.repo / old
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            self.inventory['files'].append({'old_path': old, 'sha256': sha(data), 'bytes': len(data), 'disposition': 'keep_current_catalog_needs_rewrite' if old.endswith('catalog.json') else 'keep_source', 'proposed_destination': 'art/characters/' + dest})
        subprocess.run(['git', '-C', str(self.repo), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.repo), '-c', 'user.name=Static Test', '-c', 'user.email=static@example.invalid', 'commit', '-qm', 'fixture'], check=True)
        self.inventory_path = self.repo / 'selection.json'
        self.inventory_path.write_text(json.dumps(self.inventory))
        self.dest = self.repo / 'art/characters'

    def run_import(self):
        self.assertTrue(MODULE.exists(), 'static importer has not been implemented')
        spec = importlib.util.spec_from_file_location('static_import_under_test', MODULE)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.module = mod
        return mod.import_static(self.repo, self.dest, 'HEAD', self.inventory_path)

    def test_candidate_scope_and_separate_designs_survive(self):
        result = self.run_import()
        catalog = result['catalog']
        candidates = [c for group in catalog['categories'].values() for c in group]
        self.assertEqual(len(candidates), 4)
        self.assertEqual({c['status'] for c in candidates}, {'candidate'})
        self.assertEqual(candidates[0]['compatibility'], self.inventory['candidates'][0]['compatibility'])
        self.assertEqual(candidates[0]['resource_kind'], 'static-candidate')
        self.assertNotEqual(result['path_map']['old/style02.png'], result['path_map']['old/style03.png'])

    def test_rejected_reference_preserved(self):
        result = self.run_import()
        p = result['path_map']['old/pants08/rejected/skirt-waist/source.png']
        self.assertEqual((self.repo / p).read_bytes(), b'necessary rejected reference')

    def test_rebuild_uses_git_when_old_worktree_files_are_gone(self):
        first = self.run_import()
        snapshot = {p.relative_to(self.dest).as_posix(): p.read_bytes() for p in self.dest.rglob('*') if p.is_file()}
        for old in self.payloads:
            (self.repo / old).unlink()
        second = self.run_import()
        self.assertEqual(first, second)
        self.assertEqual(snapshot, {p.relative_to(self.dest).as_posix(): p.read_bytes() for p in self.dest.rglob('*') if p.is_file()})

    def test_sha_mismatch_is_rejected_before_output(self):
        self.inventory['files'][0]['sha256'] = '0' * 64
        self.inventory_path.write_text(json.dumps(self.inventory))
        with self.assertRaisesRegex(ValueError, 'SHA'):
            self.run_import()
        self.assertFalse(self.dest.exists())

    def test_missing_sha_is_rejected(self):
        del self.inventory['files'][0]['sha256']
        self.inventory_path.write_text(json.dumps(self.inventory))
        with self.assertRaisesRegex(ValueError, 'SHA'):
            self.run_import()

    def test_destination_cannot_escape_library(self):
        self.inventory['files'][0]['proposed_destination'] = 'art/characters/../escape.png'
        self.inventory_path.write_text(json.dumps(self.inventory))
        with self.assertRaisesRegex(ValueError, 'path'):
            self.run_import()

    def test_manifest_bare_filenames_resolve_in_their_declared_scope(self):
        additions = {
            'old/proof/parts/pants.png': (b'transparent part', 'parts/pants/pants01/static/pants.png'),
            'old/proof/proof/pants.png': (b'clothed preview', 'builds/static-proof/pants.png'),
        }
        manifest = {'parts': {'pants.png': sha(b'transparent part')}, 'frames': {'pants.png': sha(b'clothed preview')}}
        additions['old/proof/manifest.json'] = (json.dumps(manifest).encode(), 'builds/static-proof/manifest.json')
        for old, (data, new) in additions.items():
            p = self.repo / old
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            self.inventory['files'].append({'old_path': old, 'sha256': sha(data), 'bytes': len(data), 'disposition': 'keep_source', 'proposed_destination': 'art/characters/' + new})
        subprocess.run(['git', '-C', str(self.repo), 'add', 'old'], check=True)
        subprocess.run(['git', '-C', str(self.repo), '-c', 'user.name=Static Test', '-c', 'user.email=static@example.invalid', 'commit', '-qm', 'manifest scope'], check=True)
        self.inventory_path.write_text(json.dumps(self.inventory))
        self.run_import()
        migrated = json.loads((self.dest / 'builds/static-proof/manifest.json').read_text())
        self.assertEqual(migrated['parts'], {'parts/pants/pants01/static/pants.png': sha(b'transparent part')})
        self.assertEqual(migrated['frames'], {'builds/static-proof/pants.png': sha(b'clothed preview')})

    def test_missing_candidate_source_cannot_become_history(self):
        self.inventory['files'] = self.inventory['files'][1:]
        self.inventory_path.write_text(json.dumps(self.inventory))
        with self.assertRaisesRegex(ValueError, 'unmapped resource'):
            self.run_import()

    def test_absolute_generated_path_is_only_history(self):
        old = 'old/generation.json'
        original = {'generated_path': '/private/unknown/exec.png', 'reference_images': ['/Users/old/project/old/body.png']}
        # Use a committed relative reference for the active input.
        original['reference_images'] = ['old/body.png']
        data = json.dumps(original).encode()
        (self.repo / old).write_bytes(data)
        self.inventory['files'].append({'old_path': old, 'sha256': sha(data), 'bytes': len(data), 'disposition': 'keep_provenance', 'proposed_destination': 'art/characters/sources/static-test/generation.json'})
        subprocess.run(['git', '-C', str(self.repo), 'add', old], check=True)
        subprocess.run(['git', '-C', str(self.repo), '-c', 'user.name=Static Test', '-c', 'user.email=static@example.invalid', 'commit', '-qm', 'generation provenance'], check=True)
        self.inventory_path.write_text(json.dumps(self.inventory))
        self.run_import()
        migrated = json.loads((self.dest / 'sources/static-test/generation.json').read_text())
        self.assertNotIn('generated_path', migrated)
        self.assertEqual(migrated['reference_images'], ['templates/body02-candidate-v1/revisions/static-candidate-v1/body-atlas.png'])
        self.assertEqual(migrated['historical_provenance']['references'][0]['value'], original['generated_path'])

    def test_verification_rejects_modified_imported_resource(self):
        result = self.run_import()
        verify = getattr(self.module, 'verify_static', None)
        self.assertTrue(callable(verify), 'static verification entry point missing')
        self.assertTrue(verify(self.repo, self.dest)['passed'])
        (self.repo / result['path_map']['old/body.png']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'SHA'):
            verify(self.repo, self.dest)

    def test_retained_source_has_current_asset_navigation(self):
        self.run_import()
        path = self.dest / 'sources/static-pants08-waist-reference-v1/source.json'
        self.assertTrue(path.exists(), 'source navigation index missing')
        index = json.loads(path.read_text())
        self.assertEqual(index['source_id'], 'static-pants08-waist-reference-v1')
        self.assertEqual(index['assets'][0]['file'], 'sources/static-pants08-waist-reference-v1/source.png')
        self.assertEqual(index['assets'][0]['sha256'], sha(b'necessary rejected reference'))

    def test_collision_requires_identical_sha(self):
        self.inventory['files'][3]['proposed_destination'] = self.inventory['files'][2]['proposed_destination']
        self.inventory_path.write_text(json.dumps(self.inventory))
        with self.assertRaisesRegex(ValueError, 'collision'):
            self.run_import()


if __name__ == '__main__':
    unittest.main()
