import importlib.util
from pathlib import Path
import tempfile,unittest,hashlib
SPEC=importlib.util.spec_from_file_location('layout_migration',Path(__file__).parents[1]/'migrate_layout.py')
class MigrationTests(unittest.TestCase):
 def module(self):
  self.assertTrue(Path(SPEC.origin).exists(), "Migration module is not implemented")
  module=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(module);return module
 def test_path_policy_rejects_escape(self):
  m=self.module()
  for value in ['/tmp/a','../a','a/../../x','a\\b','res://x']:
   with self.subTest(value=value),self.assertRaises(ValueError):m.relative(value)
  self.assertEqual(m.relative('sources/x/original.png'),'sources/x/original.png')
 def test_equal_blob_reuses_storage_and_retains_two_origins(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as d:
   store=m.AssetStore(Path(d));a=store.add('old/a.png',b'abc','sources/a/original.png');b=store.add('old/b.png',b'abc','sources/b/original.png')
   self.assertEqual(a,b);self.assertEqual(len(store.records),2)
 def test_same_destination_different_bytes_is_rejected(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as d:
   store=m.AssetStore(Path(d));store.add('a',b'abc','parts/a/view.png')
   with self.assertRaises(ValueError):store.add('b',b'xyz','parts/a/view.png')
 def test_registered_part_bake_restores_ear_with_real_alpha_compositing(self):
  m=self.module()
  from PIL import Image
  body=Image.new('RGBA',(2,2),(240,150,100,253));hair=Image.new('RGBA',(2,2),(60,30,20,253));clear=Image.new('RGBA',(2,2))
  self.assertEqual(m.compose_head(body,hair,clear,clear).getpixel((0,0)),Image.alpha_composite(body,hair).getpixel((0,0)))
 def test_two_source_registered_views_keep_distinct_identity(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'old').mkdir();(root/'old/front.png').write_bytes(b'front');(root/'old/back.png').write_bytes(b'back')
   class Reader:
    blobs={'old/front.png':True,'old/back.png':True}
    def read(self,path):return (root/path).read_bytes()
   migration=m.Migration.__new__(m.Migration);migration.reader=Reader();migration.root=root/'new';migration.store=m.AssetStore(migration.root);migration.core={};migration.sources=m.defaultdict(set);migration.discovering=set()
   record={'registered_file':'front.png','source_views':[{'registered_file':'back.png'}]}
   result=migration.convert(record,'old/sample.json',set(),context={'part':'hair_under_hat','design':'hair','recipe':'hoe','pose':'key2','build':'hoe'})
   self.assertNotEqual(result['registered_file'],result['source_views'][0]['registered_file'])
   self.assertEqual((migration.root/result['registered_file']).read_bytes(),b'front')
   self.assertEqual((migration.root/result['source_views'][0]['registered_file']).read_bytes(),b'back')
 def test_layers_without_placement_mode_are_slot_views_not_final_frames(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'old').mkdir()
   for name,data in [('torso.png',b'torso'),('sleeve.png',b'sleeve')]: (root/'old'/name).write_bytes(data)
   class Reader:
    blobs={'old/torso.png':True,'old/sleeve.png':True}
    def read(self,path):return (root/path).read_bytes()
   migration=m.Migration.__new__(m.Migration);migration.reader=Reader();migration.root=root/'new';migration.store=m.AssetStore(migration.root);migration.core={};migration.sources=m.defaultdict(set);migration.discovering=set()
   record={'layers':[{'id':'torso','slot':'top','file':'torso.png','offset_px':[0,0]},{'id':'sleeve','slot':'top','file':'sleeve.png','offset_px':[0,0]}]}
   try:
    result=migration.convert(record,'old/sample.json',set(),context={'recipe':'walk','pose':'key0','build':'walk','slots':{'top':'top03'}})
   except ValueError as error:self.fail('Distinct authored layers must not collide: '+str(error))
   for layer in result['layers']:self.assertTrue(layer['file'].startswith('parts/top03/'))
 def test_manifest_rejects_stale_external_hash_and_unresolved_ownership(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'parent.json').write_bytes(b'new parent')
   with self.assertRaisesRegex(ValueError,'Stale external_inputs'):
    m.validate_manifest_references(root,{'external_inputs':{'parent.json':'0'*64}})
   with self.assertRaisesRegex(ValueError,'Missing ownership'):
    m.validate_manifest_references(root,{'parts':{'hair':{'source_views':[{'ownership':'missing.png'}]}}})
   (root/'mask.png').write_bytes(b'mask')
   self.assertTrue(m.validate_manifest_references(root,{'parts':{'hair':{'source_views':[{'ownership':'mask.png'}]}}}))
 def test_semantic_equivalence_rejects_offset_and_missing_idle(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as d:
   migration=m.Migration.__new__(m.Migration);migration.root=Path(d);migration.core={};migration.store=m.AssetStore(d)
   class Reader:
    blobs={}
   migration.reader=Reader()
   original={'frames':[{'pose_id':'p','parts':{'hair':{'offset_px':[0,0]}}}],'idle':{'pose_id':'idle'}}
   changed={'frames':[{'pose_id':'p','parts':{'hair':{'offset_px':[99,99]}}}],'idle':{'pose_id':'idle'}}
   with self.assertRaisesRegex(ValueError,'Semantic configuration changed'):
    migration.compare_semantics('old/sample.json',original,changed)
   with self.assertRaisesRegex(ValueError,'Semantic configuration changed'):
    migration.compare_semantics('old/sample.json',original,{'frames':original['frames']})
 def test_publish_cannot_overwrite_validated_library(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as d:
   repo=Path(d);receipt=repo/'art/characters/evidence/layout-native/receipt.json';receipt.parent.mkdir(parents=True);receipt.write_text('{}')
   with self.assertRaisesRegex(ValueError,'Validated library is immutable'):
    m.publish('/private/tmp/coastal-unused-staging',repo=repo)
if __name__=='__main__':unittest.main()
