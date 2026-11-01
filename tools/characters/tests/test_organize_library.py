"""Path migration must preserve content and close references, not bless stale hashes."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

class OrganizationTests(unittest.TestCase):
    def test_plan_rewrites_nested_reference_hash_without_touching_pixels(self):
        from organize_library import rewrite_documents
        image = b'unchanged image bytes'
        source = b'{"texture":"parts/top03/view.png"}'
        sha = lambda x: hashlib.sha256(x).hexdigest()
        files = {'parts/top03/view.png': image, 'parts/top03/design.json': source,
                 'recipes/a.json': json.dumps({'file':'parts/top03/design.json','sha256':sha(source)}).encode()}
        result = rewrite_documents(files, {'parts/top03/':'parts/top/top03/'})
        self.assertEqual(result['parts/top/top03/view.png'], image)
        ref = json.loads(result['recipes/a.json'])
        self.assertEqual(ref['file'], 'parts/top/top03/design.json')
        self.assertEqual(ref['sha256'], sha(result[ref['file']]))
        self.assertIn('parts/top03/view.png', files)

    def test_historical_snapshot_is_opaque(self):
        from organize_library import rewrite_documents
        payload = b'{"file":"parts/top03/a.png"}'
        files = {'sources/a/code.snapshot.json':payload}
        self.assertEqual(rewrite_documents(files, {'parts/top03/':'parts/top/top03/'}),files)

    def test_mapping_collision_rejected_before_mutation(self):
        from organize_library import rewrite_documents
        with self.assertRaisesRegex(ValueError,'collision'):
            rewrite_documents({'parts/a/x.png':b'a','parts/b/x.png':b'b'},
                              {'parts/a/':'parts/top/x/','parts/b/':'parts/top/x/'})

    def test_prefix_does_not_replace_other_design(self):
        from organize_library import rewrite_documents
        files = {'recipes/a.json': b'{"file":"parts/top030/design.json"}'}
        self.assertEqual(rewrite_documents(files, {'parts/top03/':'parts/top/top03/'}),files)

    def test_external_engine_hash_is_propagated(self):
        from organize_library import rewrite_documents
        old='1'*64;new='2'*64
        value={'recipes/a.json':json.dumps({'sha256':old}).encode()}
        result=rewrite_documents(value,{},hash_updates={old:new})
        self.assertEqual(json.loads(result['recipes/a.json'])['sha256'],new)

class LegacyReceiptTests(unittest.TestCase):
    def test_historical_binding_requires_exact_original_digest(self):
        from organize_library import historical_binding, RECEIPT
        with tempfile.TemporaryDirectory(prefix='coastal-relocation-',dir='/private/tmp') as folder:
            root=Path(folder);p=root/RECEIPT;p.parent.mkdir(parents=True)
            p.write_text(json.dumps({'files':{'art/characters/a.json':{'old_sha256':'a'*64,'new_path':'art/characters/b.json','new_sha256':'b'*64}}}))
            self.assertEqual(historical_binding(root,'art/characters/a.json','a'*64),('art/characters/b.json','b'*64))
            with self.assertRaisesRegex(ValueError,'origin'):
                historical_binding(root,'art/characters/a.json','c'*64)

class CompositeIdentityTests(unittest.TestCase):
    def test_source_identity_propagates_path_change_into_compatibility(self):
        from organize_library import rewrite_documents
        canonical=lambda x:json.dumps(x,sort_keys=True,separators=(',',':')).encode()
        old_basis={'kind':'coastal-component-source-identity-v1','texture':'parts/top03/view.png'}
        old_identity=hashlib.sha256(canonical(old_basis)).hexdigest()
        files={'parts/top03/pair.json':json.dumps({'hair_identity_sha256':old_identity}).encode()}
        result=rewrite_documents(files,{'parts/top03/':'parts/top/top03/'},identities={old_identity:old_basis})
        expected=dict(old_basis,texture='parts/top/top03/view.png')
        self.assertEqual(json.loads(result['parts/top/top03/pair.json'])['hair_identity_sha256'],hashlib.sha256(canonical(expected)).hexdigest())

    def test_recipe_authoring_snapshot_keeps_exact_historical_text_and_sha(self):
        from organize_library import rewrite_documents
        old='1'*64
        payload=json.dumps({'kind':'coastal-recipe-authoring-snapshot-v1','original_file':'parts/top03/a.json','original_sha256':old,'original_json':'{"old":true}'}).encode()
        files={'sources/assembly/metadata/parent.json':payload}
        self.assertEqual(rewrite_documents(files,{'parts/top03/':'parts/top/top03/'},{old:'2'*64}),files)

class LegacyTypeSafetyTests(unittest.TestCase):
    def test_numeric_to_boolean_change_is_not_a_path_migration(self):
        import subprocess
        from organize_library import verify_legacy_binding, RECEIPT, digest
        with tempfile.TemporaryDirectory(prefix='coastal-relocation-',dir='/private/tmp') as folder:
            root=Path(folder);name='art/characters/recipes/legacy/r001.json';p=root/name;p.parent.mkdir(parents=True)
            old=b'{"count":1}';p.write_bytes(old)
            subprocess.run(['git','init','-q',folder],check=True)
            subprocess.run(['git','add','.'],cwd=root,check=True)
            subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','old'],cwd=root,check=True)
            revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
            p.write_bytes(b'{"count":true}')
            record={'baseline_commit':revision,'path_prefixes':{},'hash_updates':{},'files':{name:{'old_sha256':digest(old),'new_path':name,'new_sha256':digest(p.read_bytes())}}}
            target=root/RECEIPT;target.parent.mkdir(parents=True);target.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError,'semantic'):
                verify_legacy_binding(root,name,digest(old))
