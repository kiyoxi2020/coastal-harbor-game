"""Pre-capture dependency snapshot and post-capture fail-closed validation.

Conservative static/manifest superset, never a runtime file-access trace.
No Godot invocation, resource edits, repository traversal or .godot reads.
"""
from pathlib import Path,PurePosixPath
import argparse,datetime,hashlib,json,math,posixpath,re,struct,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
BASE='art/design/character-motion/adult-standard-v1/'
TOOL=BASE+'farming-four-directions-v1/evidence_contract.py'
PHASES={'water':['ready','raise','pour','recovery'],'hoe':['ready','lift','contact','recovery'],'harvest':['ready','reach','pluck','recovery']}
DIRECTIONS=['south','west','east','north']
GARMENTS=['A','B']
EXPECTED_KEYS=sorted(f'{a}/{d}/{g}' for a in PHASES for d in DIRECTIONS for g in GARMENTS)
SHA=re.compile(r'^[0-9a-f]{64}$')
STATIC=re.compile(r'''["'](res://[^"'\n]+)["']''')
NO_DECLARED_HASH=object()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(data):return hashlib.sha256(data).hexdigest()
def canonical_digest(data):return sha(json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
def require(condition,message):
 if not condition:raise ValueError(message)
def declared_utc(value,allow_native_naive=False):
 require(isinstance(value,str) and value,'capture UTC timestamp missing')
 try:stamp=datetime.datetime.fromisoformat(value.replace('Z','+00:00'))
 except ValueError as e:raise ValueError('capture UTC timestamp invalid') from e
 if stamp.tzinfo is None and allow_native_naive:stamp=stamp.replace(tzinfo=datetime.timezone.utc)
 require(stamp.utcoffset()==datetime.timedelta(0),'capture timestamp is not UTC')
 return stamp
def normalized(path):
 path=posixpath.normpath(str(path))
 require(not path.startswith('/') and path!='..' and not path.startswith('../') and path!='.','path escapes repository: '+path)
 require('.godot' not in PurePosixPath(path).parts,'cache dependency forbidden')
 return path
def relative(path):
 require(isinstance(path,str) and path and not PurePosixPath(path).is_absolute() and ':' not in path and '\\' not in path,'invalid relative resource path')
 require(all(p not in ['', '.', '..'] for p in path.split('/')),'unsafe relative resource path: '+path)
 return path
def repository_path(root,path):
 p=Path(path)
 if p.is_absolute():
  try:path=p.resolve().relative_to(root.resolve()).as_posix()
  except ValueError as e:raise ValueError('input must be inside repository') from e
 return normalized(path)
def roles(catalog,native_script):
 return {'catalog':catalog,'locomotion_manifest':BASE+'locomotion-v1/baked/export-manifest.json','run_candidate':BASE+'run-four-directions-v1/candidate.json','run_garments':BASE+'run-four-directions-v1/run-garments.json','run_diagnostics':BASE+'run-four-directions-v1/run-diagnostics.json','trial_scene':'godot2d/dev/character_walk_trial.tscn','world_scene':'godot2d/scenes/world/harbor_exterior.tscn','camera':'godot2d/scripts/world_camera.gd','project':'godot2d/project.godot','native_script':native_script,'evidence_tool':TOOL}
def png_size(data):
 require(len(data)>=24 and data[:8]==b'\x89PNG\r\n\x1a\n' and data[12:16]==b'IHDR','frame is not PNG')
 return list(struct.unpack('>II',data[16:24]))
class Graph:
 def __init__(self,root,read=None):self.root=root;self.reader=read;self.dependencies={};self.edges={};self.fragments=[]
 def read(self,path):
  path=normalized(path)
  try:return self.reader(path) if self.reader else (self.root/path).read_bytes()
  except (OSError,KeyError) as e:raise ValueError('missing actual dependency: '+path) from e
 def add(self,path,reason,expected=NO_DECLARED_HASH):
  path=normalized(path)
  if expected is not NO_DECLARED_HASH:require(isinstance(expected,str) and SHA.fullmatch(expected) is not None,'missing/invalid declared hash: '+path)
  if path not in self.dependencies:self.dependencies[path]=sha(self.read(path))
  require(expected is NO_DECLARED_HASH or self.dependencies[path]==expected,'declared dependency hash mismatch: '+path)
  self.edges.setdefault(path,set()).add(reason)
  return path
 def obj(self,path):
  try:d=json.loads(self.read(path))
  except (json.JSONDecodeError,UnicodeDecodeError) as e:raise ValueError('invalid JSON: '+path) from e
  require(isinstance(d,dict),'JSON object required: '+path);return d
 def inputs(self,manifest,base):
  d=self.obj(manifest);entries=d.get('inputs')
  require(isinstance(entries,dict) and entries,'missing inputs: '+manifest)
  for rel,value in entries.items():
   relative(rel);digest=value.get('sha256') if isinstance(value,dict) else value
   if isinstance(value,dict):require(value.get('path',rel)==rel,'ambiguous input path: '+manifest)
   self.add(base+'/'+rel,manifest+'#inputs',digest)
  return d
 def static(self,seeds):
  pending=list(seeds);visited=set()
  while pending:
   path=pending.pop()
   if path in visited:continue
   visited.add(path);self.add(path,'reachable Godot static graph')
   if Path(path).suffix not in ['.gd','.tscn','.tres','.godot','.json']:continue
   for ref in STATIC.findall(self.read(path).decode('utf-8')):
    tail=ref.removeprefix('res://')
    if not Path(tail).suffix or any(c in tail for c in '%{}'):
     self.fragments.append({'source':path,'literal':ref});continue
    target=normalized('godot2d/'+tail);self.add(target,path+'#static_literal');pending.append(target)
def collect(root,catalog,native_script,read=None):
 g=Graph(root,read);mandatory=roles(catalog,native_script)
 for role,path in mandatory.items():g.add(path,'required:'+role)
 catalog_data=g.obj(catalog);require(catalog_data.get('schema_version')==2 and catalog_data.get('template_id')=='adult-standard-v1','schema2 complete catalog required')
 records=catalog_data.get('clips');require(isinstance(records,list) and len(records)==24,'catalog must contain all24 combinations')
 clips={}
 for record in records:
  require(isinstance(record,dict),'invalid catalog record')
  action,direction,garment=[record.get(k) for k in ['action_id','direction','garment']]
  require(action in PHASES and direction in DIRECTIONS and garment in GARMENTS,'unknown catalog capability')
  key=f'{action}/{direction}/{garment}';require(key not in clips,'duplicate catalog combination: '+key)
  candidate=relative(record.get('candidate'));g.add(candidate,catalog+'#'+key,record.get('sha256'));base=posixpath.dirname(candidate);d=g.inputs(candidate,base)
  require(d.get('schema_version')==1 and d.get('template_id')=='adult-standard-v1' and [d.get(k) for k in ['action_id','direction','garment']]==[action,direction,garment],'candidate identity mismatch: '+key)
  scale=d.get('display_scale');require(type(scale) in [int,float] and math.isfinite(scale) and abs(scale-138/1164)<1e-12 and d.get('source_density_scale_vs_idle')==2,'candidate source density mismatch')
  canvas=d.get('canvas_px');root_px=d.get('root_anchor_px');require(isinstance(canvas,list) and len(canvas)==2 and all(type(x)is int and x>0 for x in canvas),'invalid canvas')
  require(isinstance(root_px,list) and len(root_px)==2 and all(type(x)is int and 0<=x<canvas[i] for i,x in enumerate(root_px)),'invalid root')
  frames=d.get('frames');require(isinstance(frames,list) and len(frames)>=4,'candidate missing real phases: '+key)
  seen_ids=set();phases=set();texture_hashes=set();previous=-1;index=[]
  for f in frames:
   require(isinstance(f,dict),'invalid frame')
   pose=f.get('pose_id');require(isinstance(pose,str) and pose and pose not in seen_ids,'missing/duplicate pose');seen_ids.add(pose)
   phase=f.get('phase');require(phase in PHASES[action],'missing/invalid phase');order=PHASES[action].index(phase);require(order>=previous,'reordered phase');previous=order;phases.add(phase)
   duration=f.get('duration_ms');require(type(duration)is int and duration>0,'invalid frame duration')
   file=relative(f.get('file'));frame_path=base+'/'+file;g.add(frame_path,candidate+'#frames',f.get('sha256'));require(png_size(g.read(frame_path))==canvas,'actual frame size differs from candidate')
   source=relative(f.get('source'));digest=f.get('source_sha256');require(isinstance(digest,str) and SHA.fullmatch(digest) is not None and d['inputs'].get(source)==digest,'source not bound to inputs')
   g.add(base+'/'+source,candidate+'#source',digest);texture_hashes.add(f['sha256'])
   index.append({'pose_id':pose,'phase':phase,'duration_ms':duration,'file':frame_path,'sha256':f['sha256'],'source':base+'/'+source,'source_sha256':digest})
  require(phases==set(PHASES[action]) and len(texture_hashes)>=4,'missing phases or repeated poses')
  clips[key]={'candidate':candidate,'sha256':g.dependencies[candidate],'frames':index,'duration_ms':sum(f['duration_ms'] for f in index)}
 require(sorted(clips)==EXPECTED_KEYS,'catalog coverage differs from required24 keys')
 loc=mandatory['locomotion_manifest'];ld=g.obj(loc);source_root=normalized(posixpath.dirname(loc)+'/'+ld.get('source_root','..'));ld=g.inputs(loc,source_root)
 contract=ld.get('source_contract');require(isinstance(contract,dict) and contract,'locomotion source_contract missing')
 for rel,digest in contract.items():
  relative(rel);require(isinstance(ld['inputs'].get(rel),dict) and ld['inputs'][rel].get('sha256')==digest,'locomotion source_contract/input mismatch');g.add(source_root+'/'+rel,loc+'#source_contract',digest)
 require(isinstance(ld.get('recipes'),dict) and ld['recipes'],'locomotion recipes missing')
 for recipe in ld['recipes'].values():
  entries=recipe.get('frames');require(isinstance(entries,list) and entries,'locomotion actual textures missing')
  for f in entries:g.add(posixpath.dirname(loc)+'/'+relative(f.get('file')),loc+'#actual_texture',f.get('sha256'))
 run=mandatory['run_candidate'];runroot=posixpath.dirname(run);rd=g.inputs(run,runroot)
 require(rd.get('walk_artifact_digest')==ld.get('artifact_digest') and isinstance(ld.get('artifact_digest'),str),'run/locomotion artifact mismatch')
 require(isinstance(rd.get('frames'),list) and rd['frames'],'run frames missing')
 for f in rd['frames']:g.add(runroot+'/'+relative(f.get('file')),run+'#frames',f.get('sha256'))
 garment=mandatory['run_garments'];gd=g.inputs(garment,runroot);require(gd.get('candidate_manifest_sha256')==g.dependencies[run],'garments/run binding mismatch')
 capabilities=set();require(isinstance(gd.get('recipes'),dict),'run recipes missing')
 for outfit,directions in gd['recipes'].items():
  require(outfit in GARMENTS and isinstance(directions,dict),'unknown run garment')
  for direction,files in directions.items():
   require(direction in DIRECTIONS and isinstance(files,list) and files,'invalid run direction/texture capability')
   for rel in files:
    relative(rel);require(rel in gd['inputs'],'run garment texture is not input-bound');g.add(runroot+'/'+rel,garment+'#recipes',gd['inputs'][rel])
   capabilities.add(direction+'/'+outfit)
 diag=mandatory['run_diagnostics'];dd=g.inputs(diag,runroot)
 require(dd.get('candidate_manifest_sha256')==g.dependencies[run] and dd.get('run_garments_sha256')==g.dependencies[garment],'diagnostics base manifest mismatch')
 require(isinstance(dd.get('records'),list) and dd['records'],'diagnostics records missing');diagnostic_keys=set()
 for record in dd['records']:
  direction,outfit=record.get('direction'),record.get('garment');require(direction in DIRECTIONS and outfit in GARMENTS,'invalid diagnostic capability')
  key=direction+'/'+outfit;require(key not in diagnostic_keys,'duplicate diagnostic capability');diagnostic_keys.add(key)
  require(isinstance(record.get('frames'),list) and record['frames'],'diagnostic frames missing')
  for f in record['frames']:
   rel=relative(f.get('file'));require(rel in dd['inputs'],'diagnostic actual texture is not input-bound');g.add(runroot+'/'+rel,diag+'#frames',dd['inputs'][rel])
  capabilities.add(key)
 require(capabilities=={d+'/'+a for d in DIRECTIONS for a in GARMENTS},'incomplete run A/B capability set with diagnostics')
 g.static([mandatory[k] for k in ['trial_scene','world_scene','camera','project','native_script']])
 return g,mandatory,dict(sorted(clips.items())),sorted(capabilities)
def make_snapshot(root,catalog,native_script,read=None):
 root=Path(root).resolve();started=utc();catalog=repository_path(root,catalog);native_script=repository_path(root,native_script)
 g,mandatory,clips,run_capabilities=collect(root,catalog,native_script,read)
 c={'schema_version':1,'capture_phase':'before_native_capture','snapshot_started_utc':started,'snapshot_utc':utc(),'repo_root_at_snapshot':str(root),'configuration':{'catalog':catalog,'native_script':native_script},'run_diagnostics_enabled':True,'scope':'Conservative reachable Godot static resources plus explicitly resolved manifests; includes inherited/optional unexecuted branches, not a runtime load trace. No visual or gameplay acceptance inferred.','roles':mandatory,'clip_keys':sorted(clips),'clips':clips,'run_capabilities':run_capabilities,'dependencies':dict(sorted(g.dependencies.items())),'dependency_edges':{k:sorted(v) for k,v in sorted(g.edges.items())},'unresolved_static_fragments':g.fragments,'limitations':['Only referenced resources are traversed; no repository/cache enumeration.','Godot engine executable, imported .godot cache, OS and display server are outside this snapshot.','Snapshot must be invoked before capture. Post validation compares current exact bytes; it does not prove no temporary edits occurred between observations.','Source hashes verify referenced files, not whether historical failed art is visually good.']}
 c['artifact_digest']=canonical_digest(c);return c
def validate_snapshot(contract,root=ROOT,read=None):
 require(isinstance(contract,dict),'input contract must be an object')
 root=Path(root).resolve();c=dict(contract);digest=c.pop('artifact_digest',None);require(isinstance(digest,str) and canonical_digest(c)==digest,'snapshot content digest mismatch')
 require(c.get('schema_version')==1 and c.get('capture_phase')=='before_native_capture' and c.get('run_diagnostics_enabled')is True,'not this pre-capture diagnostics-enabled contract')
 try:stamp=datetime.datetime.fromisoformat(c['snapshot_utc'])
 except (ValueError,KeyError,TypeError) as e:raise ValueError('snapshot UTC missing/invalid') from e
 require(stamp.utcoffset()==datetime.timedelta(0),'snapshot timestamp must be UTC')
 require(c.get('repo_root_at_snapshot')==str(root),'repository root differs from snapshot')
 config=c.get('configuration',{});require(isinstance(config,dict),'snapshot configuration must be an object');catalog=repository_path(root,config.get('catalog',''));native=repository_path(root,config.get('native_script',''))
 require(c.get('roles')==roles(catalog,native),'required role set omitted/changed')
 require(c.get('clip_keys')==EXPECTED_KEYS,'required24 clip key set omitted/changed')
 g,mandatory,clips,capabilities=collect(root,catalog,native,read)
 expected=c.get('dependencies',{});require(set(g.dependencies)==set(expected),'dependency closure omitted/changed')
 for path,digest in g.dependencies.items():require(expected[path]==digest,'snapshot actual input changed: '+path)
 require(c.get('clips')==clips and c.get('run_capabilities')==capabilities,'snapshot clip/recipe set differs from actual manifests')
 return {'input_hashes_current':True,'clip_count':len(clips),'frame_count':sum(len(x['frames']) for x in clips.values()),'dependency_files':len(g.dependencies),'role_count':len(mandatory),'validated_utc':utc()}
def write_validation_receipt(contract_path,receipt_path,root=ROOT,native_report=None):
 contract_path=Path(contract_path);receipt_path=Path(receipt_path)
 require(receipt_path.resolve()!=contract_path.resolve(),'receipt cannot overwrite input contract')
 if native_report:require(receipt_path.resolve()!=Path(native_report).resolve(),'receipt cannot overwrite original native report')
 result={'input_hashes_current':False,'archive_allowed':False,'validated_utc':utc(),'scope':'Dependency and report binding gate only; native visual results remain those in the original report.'}
 try:
  data=contract_path.read_bytes();contract=json.loads(data);result['input_contract_sha256']=sha(data);result.update(validate_snapshot(contract,root))
  if native_report:
   report_data=Path(native_report).read_bytes();report=json.loads(report_data);result['native_report_sha256']=sha(report_data);require(isinstance(report,dict),'native report must be an object')
   require(report.get('input_contract_sha256')==result['input_contract_sha256'],'native report does not bind exact input-contract bytes')
   checks=report.get('checks');require(isinstance(checks,dict) and checks and all(v is True for v in checks.values()),'native checks are missing/failed')
   before=declared_utc(contract['snapshot_utc']);started=declared_utc(report.get('started_utc'),True);finished=declared_utc(report.get('finished_utc'),True)
   # Godot's UTC datetime strings have one-second precision. Compare those
   # clock intervals explicitly; do not invent sub-second runtime timestamps.
   clock_second=lambda value:value.replace(microsecond=0)
   require(clock_second(before)<=clock_second(started)<=clock_second(finished)<=clock_second(datetime.datetime.now(datetime.timezone.utc)),'capture UTC order is not snapshot <= started <= finished <= validation')
   result.update(capture_time_order_verified=True,capture_clock_precision_seconds=1,started_utc=started.isoformat(),finished_utc=finished.isoformat())
   result['archive_allowed']=True;result['native_report_path']=str(Path(native_report).resolve())
  else:result['archive_reason']='No native report supplied; dependencies current, archive binding not yet established.'
 except (ValueError,OSError,KeyError,TypeError,AttributeError,IndexError,UnicodeDecodeError,struct.error) as e:
  result['input_hashes_current']=False;result['archive_allowed']=False;result['error']=str(e)
 receipt_path.parent.mkdir(parents=True,exist_ok=True);receipt_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result
def main():
 parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
 snap=sub.add_parser('snapshot');snap.add_argument('--catalog',required=True);snap.add_argument('--native-script',required=True);snap.add_argument('--output',required=True)
 check=sub.add_parser('validate');check.add_argument('--contract',required=True);check.add_argument('--native-report');check.add_argument('--receipt')
 args=parser.parse_args()
 try:
  if args.command=='snapshot':
   target=Path(args.output);require(not target.exists(),'refusing to overwrite snapshot; use a fresh pre-capture evidence directory')
   contract=make_snapshot(ROOT,args.catalog,args.native_script);validate_snapshot(contract,ROOT)
   target.parent.mkdir(parents=True,exist_ok=True)
   with target.open('x') as f:f.write(json.dumps(contract,ensure_ascii=False,indent=2)+'\n')
   result={'capture_phase':contract['capture_phase'],'snapshot_utc':contract['snapshot_utc'],'input_contract_sha256':sha(target.read_bytes()),'clip_count':24,'dependency_files':len(contract['dependencies']),'output':str(target.resolve())}
  else:
   target=Path(args.contract);receipt=Path(args.receipt) if args.receipt else target.with_name('input-validation.json');result=write_validation_receipt(target,receipt,native_report=args.native_report)
   print(json.dumps(result,ensure_ascii=False));return 0 if result['input_hashes_current'] and (not args.native_report or result['archive_allowed']) else 1
  print(json.dumps(result,ensure_ascii=False));return 0
 except (ValueError,OSError,KeyError,TypeError) as e:
  print(json.dumps({'input_hashes_current':False,'archive_allowed':False,'error':str(e)},ensure_ascii=False));return 1
if __name__=='__main__':sys.exit(main())
