"""Isolated native evidence gates: mutate only /private/tmp fixtures."""
from pathlib import Path
import copy,datetime,hashlib,importlib.util,json,struct,subprocess,sys,tempfile,unittest,zlib
HERE=Path(__file__).resolve().parent
MODULE=HERE/'evidence_contract.py'
API=None
if MODULE.exists():
 spec=importlib.util.spec_from_file_location('evidence_contract',MODULE);API=importlib.util.module_from_spec(spec);spec.loader.exec_module(API)
BASE='art/design/character-motion/adult-standard-v1/'
TOOL=BASE+'farming-four-directions-v1/evidence_contract.py'
CATALOG=BASE+'farming-four-directions-v1/catalog.json'
NATIVE='godot2d/tests/test_character_farming_24_native.gd'
def sha(b):return hashlib.sha256(b).hexdigest()
def png(color,width=1,height=1):
 def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,6,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+bytes(color)*width)*height))+chunk(b'IEND',b'')
class Fixture:
 def __init__(self,root):self.root=root;self.build()
 def write(self,path,data):
  p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data if isinstance(data,bytes) else data.encode());return sha(p.read_bytes())
 def json(self,path,data):return self.write(path,json.dumps(data,sort_keys=True))
 def read_json(self,path):return json.loads((self.root/path).read_text())
 def build(self):
  self.write(TOOL,MODULE.read_bytes());self.write(NATIVE,'extends SceneTree\nconst Support=preload("res://tests/support.gd")\n')
  self.write('godot2d/tests/support.gd','extends RefCounted\n')
  self.write('godot2d/project.godot','config_version=5\n[application]\nrun/main_scene="res://dev/character_walk_trial.tscn"\n')
  self.write('godot2d/dev/character_walk_trial.tscn','[gd_scene format=3]\n[ext_resource type="PackedScene" path="res://scenes/world/harbor_exterior.tscn" id="world"]\n[ext_resource type="Script" path="res://scripts/world_camera.gd" id="camera"]\n')
  self.write('godot2d/scenes/world/harbor_exterior.tscn','[gd_scene format=3]\n[ext_resource type="Texture2D" path="res://assets/world.png" id="art"]\n')
  self.write('godot2d/scripts/world_camera.gd','extends Camera2D\n');self.write('godot2d/assets/world.png',png([0,100,0,255]))
  loc=BASE+'locomotion-v1/';source=self.write(loc+'motion.json','{"fixture":true}')
  idle=self.write(loc+'baked/A_0.png',png([1,0,0,255]));walk=self.write(loc+'baked/A_1.png',png([2,0,0,255]))
  self.json(loc+'baked/export-manifest.json',dict(schema_version=2,source_root='..',artifact_digest='fixture-walk-artifact',inputs={'motion.json':{'path':'motion.json','sha256':source}},source_contract={'motion.json':source},recipes={'A':{'frames':[{'file':'A_0.png','sha256':idle},{'file':'A_1.png','sha256':walk}]}},canvas_px=[1,1]))
  run=BASE+'run-four-directions-v1/';inputs={};frames=[];recipes={'A':{},'B':{}}
  for i,direction in enumerate(['south','west','east','north']):
   path=f'registered/{direction}.png';digest=self.write(run+path,png([i+4,0,0,255]));inputs[path]=digest;frames.append({'pose_id':'run_'+direction,'direction':direction,'file':path,'sha256':digest});recipes['A'][direction]=[path]
  candidate=self.json(run+'candidate.json',dict(walk_artifact_digest='fixture-walk-artifact',frames=frames,inputs=inputs,canvas_px=[1,1]))
  for direction in ['west','east']:
   path=f'baked/B_{direction}.png';inputs[path]=self.write(run+path,png([10,1 if direction=='west' else 2,0,255]));recipes['B'][direction]=[path]
  garment=self.json(run+'run-garments.json',dict(candidate_manifest_sha256=candidate,recipes=recipes,inputs={**inputs,'candidate.json':candidate}))
  diag_inputs={'candidate.json':candidate,'run-garments.json':garment};records=[]
  for direction in ['south','north']:
   path=f'diagnostics/B_{direction}.png';diag_inputs[path]=self.write(run+path,png([12,1 if direction=='south' else 2,0,255]));records.append(dict(direction=direction,garment='B',frames=[{'file':path,'pose_id':'run_'+direction,'duration_ms':80}]))
  self.json(run+'run-diagnostics.json',dict(schema_version=1,candidate_manifest_sha256=candidate,run_garments_sha256=garment,inputs=diag_inputs,records=records,canvas_px=[1,1]))
  clips=[]
  for action,phases in {'water':['ready','raise','pour','recovery'],'hoe':['ready','lift','contact','recovery'],'harvest':['ready','reach','pluck','recovery']}.items():
   for direction in ['south','west','east','north']:
    for garment in ['A','B']:
     folder=BASE+f'farming-four-directions-v1/{action}/{direction}-{garment}/';frames=[];deps={}
     for i,phase in enumerate(phases):
      source='sources/'+phase+'.png';file='registered/'+phase+'.png';b=png([i+20,0,0,255]);deps[source]=self.write(folder+source,b);digest=self.write(folder+file,b)
      frames.append(dict(pose_id=f'{action}_{direction}_{garment}_{phase}',phase=phase,duration_ms=250,file=file,sha256=digest,source=source,source_sha256=deps[source]))
     c=dict(schema_version=1,template_id='adult-standard-v1',action_id=action,direction=direction,garment=garment,status='fixture',canvas_px=[1,1],root_anchor_px=[0,0],source_density_scale_vs_idle=2,display_scale=138/1164,inputs=deps,frames=frames)
     path=folder+'candidate.json';digest=self.json(path,c);clips.append(dict(action_id=action,direction=direction,garment=garment,candidate=path,sha256=digest,note='fixture only'))
  self.json(CATALOG,dict(schema_version=2,template_id='adult-standard-v1',clips=clips))
 def alter_candidate(self,change):
  catalog=self.read_json(CATALOG);record=catalog['clips'][0];c=self.read_json(record['candidate']);change(c,record);record['sha256']=self.json(record['candidate'],c);self.json(CATALOG,catalog)
class EvidenceContractTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='coastal-farming24-contract-',dir='/private/tmp');self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  if API:self.fixture=Fixture(self.root)
 def require_api(self):
  if API is None:self.skipTest('gate not implemented yet')
 def snapshot(self):self.require_api();return API.make_snapshot(self.root,CATALOG,NATIVE)
 def resigned(self,c):c.pop('artifact_digest',None);c['artifact_digest']=API.canonical_digest(c);return c
 def test_complete_pre_capture_snapshot_and_roundtrip(self):
  self.assertIsNotNone(API,'24-clip evidence tool missing')
  c=self.snapshot();result=API.validate_snapshot(c,self.root)
  self.assertTrue(result['input_hashes_current']);self.assertEqual(len(c['clip_keys']),24);self.assertTrue(c['run_diagnostics_enabled'])
  self.assertEqual(c['capture_phase'],'before_native_capture');self.assertIsNotNone(datetime.datetime.fromisoformat(c['snapshot_utc']).tzinfo)
  self.assertIn(BASE+'locomotion-v1/baked/A_0.png',c['dependencies'])
 def test_missing_24th_combination_rejected(self):
  self.require_api();d=self.fixture.read_json(CATALOG);d['clips'].pop();self.fixture.json(CATALOG,d)
  with self.assertRaises(ValueError):self.snapshot()
 def test_duplicate_combination_rejected(self):
  self.require_api();d=self.fixture.read_json(CATALOG);d['clips'][-1]=d['clips'][0];self.fixture.json(CATALOG,d)
  with self.assertRaises(ValueError):self.snapshot()
 def test_missing_phase_rejected_even_after_candidate_rehash(self):
  self.require_api();self.fixture.alter_candidate(lambda c,r:c['frames'].pop())
  with self.assertRaises(ValueError):self.snapshot()
 def test_missing_candidate_hash_rejected(self):
  self.require_api();d=self.fixture.read_json(CATALOG);d['clips'][0].pop('sha256');self.fixture.json(CATALOG,d)
  with self.assertRaises(ValueError):self.snapshot()
 def test_missing_texture_hash_rejected(self):
  self.require_api();self.fixture.alter_candidate(lambda c,r:c['frames'][0].pop('sha256'))
  with self.assertRaises(ValueError):self.snapshot()
 def test_missing_source_hash_rejected(self):
  self.require_api();self.fixture.alter_candidate(lambda c,r:c['frames'][0].pop('source_sha256'))
  with self.assertRaises(ValueError):self.snapshot()
 def test_missing_world_rejected(self):
  self.require_api();(self.root/'godot2d/scenes/world/harbor_exterior.tscn').unlink()
  with self.assertRaises(ValueError):self.snapshot()
 def test_idle_actual_input_change_rejected(self):self.changed_after(BASE+'locomotion-v1/baked/A_0.png')
 def test_run_actual_input_change_rejected(self):self.changed_after(BASE+'run-four-directions-v1/registered/west.png')
 def test_camera_actual_input_change_rejected(self):self.changed_after('godot2d/scripts/world_camera.gd')
 def test_snapshot_tool_change_rejected(self):self.changed_after(TOOL)
 def changed_after(self,path):
  c=self.snapshot();(self.root/path).write_bytes((self.root/path).read_bytes()+b' changed')
  with self.assertRaises(ValueError):API.validate_snapshot(c,self.root)
 def test_omitted_required_role_set_rejected(self):
  c=self.snapshot();c['roles'].pop('camera');self.resigned(c)
  with self.assertRaises(ValueError):API.validate_snapshot(c,self.root)
 def test_omitted_world_dependency_rejected(self):
  c=self.snapshot();c['dependencies'].pop('godot2d/scenes/world/harbor_exterior.tscn');self.resigned(c)
  with self.assertRaises(ValueError):API.validate_snapshot(c,self.root)
 def test_omitted_clip_key_set_rejected(self):
  c=self.snapshot();c['clip_keys'].pop();self.resigned(c)
  with self.assertRaises(ValueError):API.validate_snapshot(c,self.root)
 def test_missing_diagnostics_rejected(self):
  self.require_api();(self.root/(BASE+'run-four-directions-v1/run-diagnostics.json')).unlink()
  with self.assertRaises(ValueError):self.snapshot()
 def test_failure_receipt_clears_old_pass(self):
  c=self.snapshot();contract=self.root/'input-contract.json';contract.write_text(json.dumps(c));receipt=self.root/'receipt.json';receipt.write_text('{"input_hashes_current":true}')
  (self.root/'godot2d/scripts/world_camera.gd').write_text('changed')
  result=API.write_validation_receipt(contract,receipt,root=self.root)
  self.assertFalse(result['input_hashes_current']);self.assertFalse(json.loads(receipt.read_text())['archive_allowed'])
 def test_report_binding_required_for_archive(self):
  c=self.snapshot();contract=self.root/'input-contract.json';contract.write_text(json.dumps(c));receipt=self.root/'receipt.json'
  started=datetime.datetime.fromisoformat(c['snapshot_utc']).replace(tzinfo=None,microsecond=0).isoformat();finished=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None,microsecond=0).isoformat()
  report=self.root/'report.json';report.write_text(json.dumps({'input_contract_sha256':sha(contract.read_bytes()),'started_utc':started,'finished_utc':finished,'checks':{'native':True}}))
  result=API.write_validation_receipt(contract,receipt,root=self.root,native_report=report)
  self.assertTrue(result['input_hashes_current']);self.assertTrue(result['archive_allowed']);self.assertEqual(result['native_report_sha256'],sha(report.read_bytes()))
  report.write_text(json.dumps({'input_contract_sha256':'0'*64,'checks':{'native':True}}))
  self.assertFalse(API.write_validation_receipt(contract,receipt,root=self.root,native_report=report)['archive_allowed'])
 def test_malformed_report_cannot_leave_previous_pass(self):
  c=self.snapshot();contract=self.root/'input-contract.json';contract.write_text(json.dumps(c));receipt=self.root/'receipt.json';receipt.write_text('{"input_hashes_current":true,"archive_allowed":true}')
  report=self.root/'report.json';report.write_text('[]')
  result=API.write_validation_receipt(contract,receipt,root=self.root,native_report=report)
  self.assertFalse(result['input_hashes_current']);self.assertFalse(json.loads(receipt.read_text())['archive_allowed'])
 def test_cli_absolute_catalog_snapshot_report_and_fail_closed_revalidation(self):
  self.require_api();contract=self.root/'capture/input-contract.json';script=str(self.root/TOOL)
  args=[sys.executable,script,'snapshot','--catalog',str(self.root/CATALOG),'--native-script',NATIVE,'--output',str(contract)]
  first=subprocess.run(args,capture_output=True,text=True);self.assertEqual(first.returncode,0,first.stdout+first.stderr)
  original=contract.read_bytes();self.assertEqual(json.loads(first.stdout)['input_contract_sha256'],sha(original))
  second=subprocess.run(args,capture_output=True,text=True);self.assertNotEqual(second.returncode,0);self.assertEqual(contract.read_bytes(),original)
  report=self.root/'capture/report.json';report.write_text(json.dumps({'input_contract_sha256':sha(original),'started_utc':API.utc(),'finished_utc':API.utc(),'checks':{'native':True}}))
  check=[sys.executable,script,'validate','--contract',str(contract),'--native-report',str(report)]
  good=subprocess.run(check,capture_output=True,text=True);self.assertEqual(good.returncode,0,good.stdout+good.stderr);self.assertTrue(json.loads(good.stdout)['archive_allowed'])
  (self.root/'godot2d/scripts/world_camera.gd').write_text('changed')
  bad=subprocess.run(check,capture_output=True,text=True);self.assertNotEqual(bad.returncode,0);self.assertFalse(json.loads((contract.parent/'input-validation.json').read_text())['input_hashes_current'])
 def test_capture_time_order_and_missing_runtime_timestamps_rejected(self):
  c=self.snapshot();contract=self.root/'input-contract.json';contract.write_text(json.dumps(c));report=self.root/'report.json';receipt=self.root/'receipt.json'
  old=(datetime.datetime.fromisoformat(c['snapshot_utc'])-datetime.timedelta(seconds=3)).isoformat()
  for times in [{'started_utc':old,'finished_utc':API.utc()},{'started_utc':API.utc(),'finished_utc':old},{}]:
   report.write_text(json.dumps({'input_contract_sha256':sha(contract.read_bytes()),'checks':{'native':True},**times}))
   self.assertFalse(API.write_validation_receipt(contract,receipt,root=self.root,native_report=report)['archive_allowed'])
if __name__=='__main__':unittest.main()
