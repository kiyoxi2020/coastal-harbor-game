"""Bind dynamic headwear and original outfit dependencies before/after native capture."""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,math,re
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
OLD=HERE.parent/'farming-four-directions-v1/evidence_contract.py'
spec=importlib.util.spec_from_file_location('farming_contract',OLD);base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
wardrobe_spec=importlib.util.spec_from_file_location('wardrobe_contract_for_headwear',HERE.parent/'wardrobe-sampling-v1/evidence_contract.py');wardrobe=importlib.util.module_from_spec(wardrobe_spec);wardrobe_spec.loader.exec_module(wardrobe)
IDS={'run-east','hoe-west','water-south','harvest-north'}
STATES=('bare','hair','hat','hair_hat')
CATALOG=HERE/'catalog.json'
NATIVE='godot2d/tests/test_character_headwear_native.gd'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def collect(root,catalog):
 root=Path(root).resolve();catalog=Path(catalog).resolve();dependencies={}
 def add(path,expected=None):
  path=Path(path).resolve();rel=path.relative_to(root).as_posix();actual=sha(path)
  if expected is not None and expected!=actual:raise ValueError('input hash mismatch: '+rel)
  dependencies[rel]=actual
 add(catalog);data=json.loads(catalog.read_text())
 if data.get('schema_version')!=1 or data.get('scope')!='sampled-headwear-not-exhaustive' or len(data.get('samples',[]))!=4:raise ValueError('expected four headwear sampled clips')
 seen=set()
 for entry in data['samples']:
  if entry['id'] not in IDS or entry['id'] in seen:raise ValueError('duplicate/unknown sample')
  seen.add(entry['id']);base.relative(entry['sample']);path=root/entry['sample'];add(path,entry['sha256']);sample=json.loads(path.read_text())
  if sample['action_id']+'-'+sample['direction']!=entry['id']:raise ValueError('sample capability mismatch')
  for rel,digest in sample['inputs'].items():base.relative(rel);add(path.parent/rel,digest)
  base.relative(sample['parent_sample']);parent_path=root/sample['parent_sample'];add(parent_path,sample['parent_sha256']);parent=json.loads(parent_path.read_text())
  for rel,digest in parent['inputs'].items():base.relative(rel);add(parent_path.parent/rel,digest)
 return dict(sorted(dependencies.items()))
def clip_metadata(root,catalog):
 root=Path(root);data=json.loads(Path(catalog).read_text());clips={}
 for entry in data['samples']:
  sample=json.loads((root/entry['sample']).read_text())
  clips[entry['id']]={'sample_sha256':entry['sha256'],'pose_ids':[f['pose_id'] for f in sample['frames']],'durations_ms':[f['duration_ms'] for f in sample['frames']],'states':list(STATES)}
 return clips
def report_coverage(report,expected_clips):
 base.require(report.get('clips')==expected_clips,'native clip metadata differs from frozen samples')
 base.require(isinstance(report.get('checks'),dict),'native checks missing')
 base_checks={'real_gpu','four_head_samples_loaded','sample_controls_fit','head_controls_fit','motion_panel_fits','capture_overview'}
 required_checks=set(base_checks);required_outputs={'overview.png'};static=set();world=set();groups={}
 for clip in sorted(IDS):
  for state in STATES:
   group=clip+'-'+state;groups[(clip,state)]=group
   required_checks.update(group+'_'+suffix for suffix in ('selected','idle_matches','canvas_fits','ten_panel_cycles','live_switch_keeps_clock','all_world_poses','motion_policy','ends_matching_idle'))
   if clip!='run-east':required_checks.add(group+'_tool_starts')
   for background in ('dark','light'):
    required_outputs.add('boards/'+group+'-'+background+'.png')
    for pose in ('idle','pose-0','pose-1','pose-2','pose-3'):
     name=group+'-'+background+'-'+pose;static.add('sequence/'+name+'.png');required_checks.add('capture_'+name)
    required_checks.update(group+'_'+background+'_pose_'+str(i) for i in range(4))
   world.update('sequence/'+group+'-world-'+str(i)+'.png' for i in range(4))
 base.require(set(report['checks'])==required_checks and all(value is True for value in report['checks'].values()),'native checks incomplete/failed/unrelated')
 outputs=report.get('output_hashes');captures=report.get('captures')
 base.require(isinstance(outputs,dict) and isinstance(captures,list),'native outputs/captures missing')
 sequence=static|world;cycles=set()
 for group in groups.values():
  pattern=re.compile(r'^sequence/'+re.escape(group)+r'-cycle-(\d{4})\.png$')
  indices=sorted(int(match.group(1)) for path in outputs if (match:=pattern.fullmatch(path)))
  base.require(len(indices)>=10 and indices==list(range(len(indices))),'native cycle captures incomplete: '+group)
  cycles.update('sequence/'+group+'-cycle-'+str(i).zfill(4)+'.png' for i in indices)
 sequence|=cycles
 base.require(set(outputs)==required_outputs|sequence,'native output set incomplete/unrelated')
 base.require(len(captures)==len(sequence) and set(captures)==sequence,'native captures differ from sequence outputs')
 samples=report.get('samples');base.require(isinstance(samples,list) and samples,'native timed samples missing')
 by_group={key:[] for key in groups}
 for point in samples:
  base.require(isinstance(point,dict) and (point.get('clip'),point.get('state')) in by_group,'native sample has unknown group')
  by_group[(point['clip'],point['state'])].append(point)
 for (clip,state),group in groups.items():
  duration=sum(expected_clips[clip]['durations_ms']);points=by_group[(clip,state)]
  base.require(duration>0 and points,'native timed samples missing: '+group)
  seen=set();previous=-1.0
  for point in points:
   pose=point.get('pose');phase=point.get('phase_ms');unwrapped=point.get('unwrapped_ms')
   base.require(type(pose)is int and 0<=pose<4 and type(phase) in (int,float) and math.isfinite(phase) and 0<=phase<duration and type(unwrapped) in (int,float) and math.isfinite(unwrapped) and unwrapped>=previous,'native timed sample invalid: '+group)
   seen.add(pose);previous=unwrapped
  base.require(seen=={0,1,2,3} and previous>=duration*10,'native ten-cycle timed samples incomplete: '+group)
def snapshot(output):
 output=Path(output)
 if output.exists():raise ValueError('snapshot already exists')
 old=base.make_snapshot(ROOT,HERE.parent/'farming-four-directions-v1/catalog-color-v2.json',NATIVE)
 c={'schema_version':1,'capture_phase':'before_native_capture','snapshot_utc':base.utc(),'baseline_contract':old,'sample_dependencies':collect(ROOT,CATALOG),'expected_clips':clip_metadata(ROOT,CATALOG),'wardrobe_dependencies':wardrobe.collect(ROOT,HERE.parent/'wardrobe-sampling-v1/catalog.json'),'tool_sha256':sha(__file__),'scope':'Four headwear sampled action-direction recipes with four head states; conservative static+baseline and complete sample inputs, not runtime load trace.'}
 c['artifact_digest']=base.canonical_digest(c)
 output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(c,indent=2)+'\n');print(json.dumps({'input_contract_sha256':sha(output),'sample_dependencies':len(c['sample_dependencies'])}))
def validate(contract,report,receipt):
 # Fail before any write, including a failed validation receipt.
 target=Path(receipt).resolve()
 for source in [Path(contract).resolve(),Path(report).resolve()]:
  if target==source or target.exists() and source.exists() and target.samefile(source):raise ValueError('receipt cannot overwrite contract or native report')
 out={'archive_allowed':False,'input_hashes_current':False}
 try:
  c=json.loads(Path(contract).read_text());digest=c.pop('artifact_digest');base.require(base.canonical_digest(c)==digest,'outer contract digest mismatch')
  base.validate_snapshot(c['baseline_contract'],ROOT)
  base.require(c['sample_dependencies']==collect(ROOT,CATALOG),'sample dependency closure changed')
  base.require(c['expected_clips']==clip_metadata(ROOT,CATALOG),'headwear clip metadata changed')
  base.require(c['wardrobe_dependencies']==wardrobe.collect(ROOT,HERE.parent/'wardrobe-sampling-v1/catalog.json'),'parent wardrobe dependency closure changed')
  base.require(c['tool_sha256']==sha(__file__),'contract tool changed')
  r=json.loads(Path(report).read_text());base.require(r['input_contract_sha256']==sha(contract),'report contract binding mismatch')
  base.require(r.get('catalog_sha256')==c['sample_dependencies'][CATALOG.relative_to(ROOT).as_posix()],'native catalog differs from frozen catalog')
  report_coverage(r,c['expected_clips'])
  before=base.declared_utc(c['snapshot_utc']);start=base.declared_utc(r['started_utc'],True);end=base.declared_utc(r['finished_utc'],True)
  base.require(int(before.timestamp())<=int(start.timestamp())<=int(end.timestamp())<=int(datetime.datetime.now(datetime.timezone.utc).timestamp()),'capture time order invalid')
  for rel,digest in r.get('output_hashes',{}).items():
   base.relative(rel);base.require(sha(Path(report).parent/rel)==digest,'native output changed: '+rel)
  base.require(bool(r.get('output_hashes')),'native output hashes missing')
  out.update(archive_allowed=True,input_hashes_current=True,input_contract_sha256=sha(contract),native_report_sha256=sha(report),validated_utc=base.utc(),sample_count=4)
 except Exception as exc:out['error']=str(exc)
 Path(receipt).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));return out['archive_allowed']
if __name__=='__main__':
 p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True);a=s.add_parser('snapshot');a.add_argument('--output',required=True);a=s.add_parser('validate');a.add_argument('--contract',required=True);a.add_argument('--report',required=True);a.add_argument('--receipt',required=True);args=p.parse_args()
 if args.command=='snapshot':snapshot(args.output)
 else:raise SystemExit(0 if validate(args.contract,args.report,args.receipt) else 1)
