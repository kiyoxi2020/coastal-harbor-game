import unittest,tempfile,json
from unittest.mock import patch
from pathlib import Path
import evidence_contract as m
class ContractTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='coastal-headwear-contract-');self.root=Path(self.tmp.name)
  self.catalog=self.root/'catalog.json';self.records=[]
  for id in sorted(m.IDS):
   folder=self.root/id;folder.mkdir();(folder/'source.bin').write_bytes(b'source')
   parent={'inputs':{'source.bin':m.sha(folder/'source.bin')}}
   (folder/'parent.json').write_text(json.dumps(parent))
   sample={'action_id':id.split('-')[0],'direction':id.split('-')[1],'parent_sample':id+'/parent.json','parent_sha256':m.sha(folder/'parent.json'),'inputs':{'source.bin':m.sha(folder/'source.bin')}}
   sample['frames']=[{'pose_id':id.replace('-','_')+'_'+str(i),'duration_ms':100} for i in range(4)]
   (folder/'sample.json').write_text(json.dumps(sample));self.records.append({'id':id,'sample':id+'/sample.json','sha256':m.sha(folder/'sample.json')})
  self.data={'schema_version':1,'scope':'sampled-headwear-not-exhaustive','samples':self.records};self.save()
 def tearDown(self):self.tmp.cleanup()
 def save(self):self.catalog.write_text(json.dumps(self.data))
 def complete_report(self,contract):
  states=['bare','hair','hat','hair_hat'];checks={key:True for key in ['real_gpu','four_head_samples_loaded','sample_controls_fit','head_controls_fit','motion_panel_fits','capture_overview']}
  clips={};captures=[];outputs={};samples=[]
  def output(path,capture=False):
   file=self.root/path;file.parent.mkdir(exist_ok=True);file.write_bytes(('native:'+path).encode());outputs[path]=m.sha(file)
   if capture:
    captures.append(path)
    if '-cycle-' not in path and '-world-' not in path:checks['capture_'+path.removeprefix('sequence/').removesuffix('.png')]=True
  output('overview.png')
  for record in self.records:
   id=record['id'];poses=[id.replace('-','_')+'_'+str(i) for i in range(4)]
   clips[id]={'sample_sha256':record['sha256'],'pose_ids':poses,'durations_ms':[100]*4,'states':states}
   for state in states:
    group=id+'-'+state
    for suffix in ['selected','idle_matches','canvas_fits','ten_panel_cycles','live_switch_keeps_clock','all_world_poses','motion_policy','ends_matching_idle']:checks[group+'_'+suffix]=True
    if id!='run-east':checks[group+'_tool_starts']=True
    for background in ['dark','light']:
     output('boards/'+group+'-'+background+'.png')
     output('sequence/'+group+'-'+background+'-idle.png',True)
     for i in range(4):
      checks[group+'_'+background+'_pose_'+str(i)]=True
      output('sequence/'+group+'-'+background+'-pose-'+str(i)+'.png',True)
    for i in range(10):output('sequence/'+group+'-cycle-'+str(i).zfill(4)+'.png',True)
    for i in range(4):output('sequence/'+group+'-world-'+str(i)+'.png',True)
    for i in range(41):samples.append({'clip':id,'state':state,'wall_ms':i*100,'phase_ms':i*100%400,'unwrapped_ms':i*100,'pose':i%4})
  return {'input_contract_sha256':m.sha(contract),'catalog_sha256':m.sha(self.catalog),'clips':clips,'checks':checks,'started_utc':m.base.utc(),'finished_utc':m.base.utc(),'output_hashes':outputs,'captures':captures,'samples':samples}
 def test_closure_includes_parent(self):self.assertEqual(len(m.collect(self.root,self.catalog)),13)
 def test_missing_sample(self):
  self.data['samples'].pop();self.save()
  with self.assertRaises(ValueError):m.collect(self.root,self.catalog)
 def test_source_tamper(self):
  (self.root/self.records[0]['id']/'source.bin').write_bytes(b'changed')
  with self.assertRaises(ValueError):m.collect(self.root,self.catalog)
 def test_parent_tamper(self):
  (self.root/self.records[0]['id']/'parent.json').write_bytes(b'{}')
  with self.assertRaises(ValueError):m.collect(self.root,self.catalog)
 def test_duplicate(self):
  self.data['samples'][1]=self.data['samples'][0];self.save()
  with self.assertRaises(ValueError):m.collect(self.root,self.catalog)
 def test_traversal(self):
  self.data['samples'][0]['sample']='../outside.json';self.save()
  with self.assertRaises(ValueError):m.collect(self.root,self.catalog)
 def test_snapshot_validates_parent_wardrobe_closure(self):
  contract=self.root/'before.json';report=self.root/'report.json';receipt=self.root/'receipt.json';output=self.root/'native.png';output.write_bytes(b'native')
  with patch.object(m,'ROOT',self.root),patch.object(m,'CATALOG',self.catalog),patch.object(m.base,'make_snapshot',return_value={}),patch.object(m.base,'validate_snapshot'),patch.object(m.wardrobe,'collect',return_value={'wardrobe.json':'original'}) as closure:
   m.snapshot(contract)
   report.write_text(json.dumps(self.complete_report(contract)))
   self.assertTrue(m.validate(contract,report,receipt))
   closure.return_value={'wardrobe.json':'changed'}
   self.assertFalse(m.validate(contract,report,receipt))
   self.assertIn('parent wardrobe dependency closure changed',json.loads(receipt.read_text())['error'])
 def test_one_image_fake_report_is_rejected(self):
  contract=self.root/'before.json';report=self.root/'report.json';receipt=self.root/'receipt.json';output=self.root/'native.png';output.write_bytes(b'native')
  with patch.object(m,'ROOT',self.root),patch.object(m,'CATALOG',self.catalog),patch.object(m.base,'make_snapshot',return_value={}),patch.object(m.base,'validate_snapshot'),patch.object(m.wardrobe,'collect',return_value={'wardrobe.json':'original'}):
   m.snapshot(contract)
   report.write_text(json.dumps({'input_contract_sha256':m.sha(contract),'clips':{id:{} for id in m.IDS},'checks':{'fake':True},'started_utc':m.base.utc(),'finished_utc':m.base.utc(),'output_hashes':{'native.png':m.sha(output)}}))
   self.assertFalse(m.validate(contract,report,receipt))
 def test_complete_native_report_and_missing_coverage(self):
  contract=self.root/'before.json';report=self.root/'report.json';receipt=self.root/'receipt.json'
  with patch.object(m,'ROOT',self.root),patch.object(m,'CATALOG',self.catalog),patch.object(m.base,'make_snapshot',return_value={}),patch.object(m.base,'validate_snapshot'),patch.object(m.wardrobe,'collect',return_value={'wardrobe.json':'original'}):
   m.snapshot(contract);complete=self.complete_report(contract)
   report.write_text(json.dumps(complete));self.assertTrue(m.validate(contract,report,receipt))
   group='run-east-hair'
   defects={}
   def altered(name,change):
    value=json.loads(json.dumps(complete));change(value);defects[name]=value
   altered('missing_check',lambda r:r['checks'].pop(group+'_ten_panel_cycles'))
   altered('fake_check',lambda r:r['checks'].update(fake=True))
   altered('clip_hash',lambda r:r['clips']['run-east'].update(sample_sha256='fake'))
   altered('clip_pose',lambda r:r['clips']['run-east']['pose_ids'].pop())
   altered('missing_board',lambda r:r['output_hashes'].pop('boards/'+group+'-dark.png'))
   altered('missing_idle',lambda r:r['output_hashes'].pop('sequence/'+group+'-dark-idle.png'))
   altered('missing_pose',lambda r:r['output_hashes'].pop('sequence/'+group+'-dark-pose-0.png'))
   altered('missing_world',lambda r:r['output_hashes'].pop('sequence/'+group+'-world-0.png'))
   altered('nine_cycle_captures',lambda r:(r['output_hashes'].pop('sequence/'+group+'-cycle-0009.png'),r['captures'].remove('sequence/'+group+'-cycle-0009.png')))
   altered('capture_mismatch',lambda r:r['captures'].remove('sequence/'+group+'-world-0.png'))
   altered('missing_group_samples',lambda r:r.update(samples=[s for s in r['samples'] if not(s['clip']=='run-east' and s['state']=='hair')]))
   altered('missing_pose_sample',lambda r:r.update(samples=[s for s in r['samples'] if not(s['clip']=='run-east' and s['state']=='hair' and s['pose']==3)]))
   altered('short_samples',lambda r:r['samples'][-1].update(unwrapped_ms=3900))
   altered('reversed_samples',lambda r:r['samples'][-2].update(unwrapped_ms=5000))
   for name,value in defects.items():
    with self.subTest(name=name):
     report.write_text(json.dumps(value));self.assertFalse(m.validate(contract,report,receipt),name)
 def test_receipt_aliases(self):
  a=self.root/'contract';b=self.root/'report';a.write_text('{}');b.write_text('{}')
  for source in [a,b]:
   for kind in ['direct','symlink','hardlink']:
    alias=self.root/(kind+source.name)
    if kind=='direct':alias=source
    elif kind=='symlink':alias.symlink_to(source)
    else:alias.hardlink_to(source)
    with self.assertRaises(ValueError):m.validate(a,b,alias)
    self.assertEqual(source.read_text(),'{}')
if __name__=='__main__':unittest.main()
