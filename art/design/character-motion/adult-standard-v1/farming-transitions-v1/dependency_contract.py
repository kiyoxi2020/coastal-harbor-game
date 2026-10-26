"""Post-run attribution gate. Does not modify or rerun native capture evidence."""
from pathlib import Path
import argparse,datetime,hashlib,json,posixpath,re,subprocess
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
BASE='art/design/character-motion/adult-standard-v1/'
EVIDENCE=BASE+'farming-transitions-v1/evidence/native/'
DEFAULT=EVIDENCE+'dependency-contract.json'
BASELINE='f6d9e20678d2280198e92801332df41f05b0d958'
ROLES={'locomotion':BASE+'locomotion-v1/baked/export-manifest.json','run_candidate':BASE+'run-four-directions-v1/candidate.json','run_garments':BASE+'run-four-directions-v1/run-garments.json','world':'godot2d/scenes/world/harbor_exterior.tscn','camera':'godot2d/scripts/world_camera.gd','project':'godot2d/project.godot','trial':'godot2d/dev/character_walk_trial.tscn','native_script':'godot2d/tests/test_character_farming_transitions_native.gd','native_report':EVIDENCE+'report.json','native_checks':EVIDENCE+'checks.json','idle_texture':BASE+'locomotion-v1/baked/A_0.png','run_texture':BASE+'run-four-directions-v1/registered/run_west_0.png'}
def sha(data):return hashlib.sha256(data).hexdigest()
def utc(timestamp=None):return datetime.datetime.fromtimestamp(timestamp,datetime.timezone.utc).isoformat() if timestamp is not None else datetime.datetime.now(datetime.timezone.utc).isoformat()
def normalized(path):
 path=posixpath.normpath(path)
 if path.startswith('/') or path=='..' or path.startswith('../'):raise ValueError('outside repository: '+path)
 return path
def closure(root,read=None):
 read=read or (lambda path:(root/path).read_bytes());cache={};dependencies={};edges={}
 def data(path):
  path=normalized(path)
  if path not in cache:
   try:cache[path]=read(path)
   except (OSError,KeyError) as e:raise ValueError('missing dependency: '+path) from e
  return cache[path]
 def add(path,reason,expected=None):
  path=normalized(path);digest=sha(data(path))
  if expected is not None and digest!=expected:raise ValueError('manifest/report hash mismatch: '+path)
  dependencies[path]=digest;edges.setdefault(path,set()).add(reason)
  return path
 def obj(path):return json.loads(data(path))
 def declared_inputs(manifest,base):
  d=obj(manifest)
  for rel,value in d.get('inputs',{}).items():
   digest=value['sha256'] if isinstance(value,dict) else value
   add(base+'/'+rel,manifest+'#inputs',digest)
  return d
 for role,path in ROLES.items():add(path,'required:'+role)
 report=obj(ROLES['native_report']);checks=obj(ROLES['native_checks'])
 if report['checks']!=checks or not checks or not all(v is True for v in checks.values()):raise ValueError('native checks are not identical/passing')
 for path,digest in report['inputs'].items():add('godot2d/'+path.removeprefix('res://'),'original native report#inputs',digest)
 loc=ROLES['locomotion'];locroot=BASE+'locomotion-v1';ld=declared_inputs(loc,locroot)
 for rel,digest in ld['source_contract'].items():
  if ld['inputs'].get(rel,{}).get('sha256')!=digest:raise ValueError('source_contract disagreement: '+rel)
  add(locroot+'/'+rel,loc+'#source_contract',digest)
 for recipe in ld['recipes'].values():
  for frame in recipe['frames']:add(locroot+'/baked/'+frame['file'],loc+'#recipes',frame['sha256'])
 runroot=BASE+'run-four-directions-v1';rd=declared_inputs(ROLES['run_candidate'],runroot)
 if rd['walk_artifact_digest']!=ld['artifact_digest']:raise ValueError('run walk_artifact_digest disagreement')
 for frame in rd['frames']:add(runroot+'/'+frame['file'],ROLES['run_candidate']+'#frames',frame['sha256'])
 gd=declared_inputs(ROLES['run_garments'],runroot)
 if gd['candidate_manifest_sha256']!=dependencies[ROLES['run_candidate']]:raise ValueError('garment candidate binding mismatch')
 for directions in gd['recipes'].values():
  for files in directions.values():
   for rel in files:
    path=runroot+'/'+rel
    if path not in dependencies:raise ValueError('run recipe texture not hash-bound: '+path)
 catalog='godot2d/dev/farming_review_catalog.json';add(catalog,'farming catalog')
 for record in obj(catalog)['clips']:
  action=record['action_id']
  candidate=normalized(record['candidate']);add(candidate,catalog+'#'+action,record['sha256'])
  if report['clips'][action]['candidate_sha256']!=record['sha256']:raise ValueError('native farming candidate mismatch: '+action)
  d=declared_inputs(candidate,posixpath.dirname(candidate))
  for frame in d['frames']:add(posixpath.dirname(candidate)+'/'+frame['file'],candidate+'#frames',frame['sha256'])
 # Follow only reachable literal resource references; no repository/cache traversal.
 pending=[ROLES['trial'],ROLES['native_script'],ROLES['project']];visited=set();dynamic=[]
 pattern=re.compile(r'''["'](res://[^"'\n]+)["']''')
 while pending:
  path=pending.pop()
  if path in visited:continue
  visited.add(path);add(path,'reachable static resource graph')
  if Path(path).suffix not in ['.gd','.tscn','.tres','.godot','.json']:continue
  for ref in pattern.findall(data(path).decode('utf-8')):
   tail=ref.removeprefix('res://')
   # Directory fragments and format templates are not complete static files.
   if not Path(tail).suffix or any(c in tail for c in '%{}'):
    dynamic.append({'source':path,'literal':ref});continue
   target=normalized('godot2d/'+tail);add(target,path+'#literal');pending.append(target)
 return dict(sorted(dependencies.items())),{k:sorted(v) for k,v in sorted(edges.items())},dynamic,cache
def git_context(root,dependencies,cache):
 def git(*args):return subprocess.check_output(['git',*args],cwd=root)
 head=git('rev-parse','HEAD').decode().strip();tree=git('ls-tree','-r','-z',BASELINE,'--',*dependencies)
 blobs={}
 for item in tree.split(b'\0'):
  if not item:continue
  meta,path=item.split(b'\t',1);blobs[path.decode()]=meta.decode().split()[2]
 matching=[];different=[];untracked=[]
 for path in dependencies:
  if path not in blobs:untracked.append(path);continue
  content=cache[path];blob=hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()
  (matching if blob==blobs[path] else different).append(path)
 # Newly implemented trial code is covered by original run-time input hashes.
 original=json.loads(cache[ROLES['native_report']])['inputs']
 runtime_bound={'godot2d/'+p.removeprefix('res://') for p in original}
 unexplained=[p for p in different if p not in runtime_bound]
 if unexplained:raise ValueError('baseline dependency changed without runtime binding: '+','.join(unexplained))
 return dict(baseline_commit=BASELINE,current_head=head,clean_start_attestation='Parent agent reports clean initial git at baseline and no changes to previously omitted dependencies between start and capture; this is session provenance, not recovered runtime telemetry.',current_git_status=git('status','--short').decode().splitlines(),baseline_matching_paths=matching,baseline_different_but_original_runtime_hash_bound=different,not_in_baseline=untracked,unexplained_baseline_differences=unexplained,verification='Current bytes Git blob SHA-1 compared to baseline tree IDs; dependency SHA-256 independently recorded. No historical clean status invented.')
def make_contract(root=ROOT,read=None,include_git=True):
 deps,edges,dynamic,cache=closure(root,read)
 script=HERE/'dependency_contract.py';tests=HERE/'test_dependency_contract.py'
 report=json.loads(cache[ROLES['native_report']]);times=[s['wall_ms'] for s in report['samples'] if 'wall_ms' in s]
 return dict(schema_version=1,association_mode='post_run_supplement_not_runtime_sampling',supplement_created_utc=utc(),scope='Existing isolated west/A native keypose transition run; adds current dependency attribution only; original capture conclusions, report, checks and test script unchanged.',dependency_set_kind='conservative_static_reachability_and_manifest_superset_not_runtime_load_list',required_roles=ROLES,dependencies=deps,dependency_edges=edges,static_parse_unresolved_fragments=dynamic,diagnostics_enabled=False,diagnostics_basis='Native test instantiates trial and sets run root; no diagnostics flag/property is enabled in this run. User launcher is a separate invocation and is outside this capture contract.',capture_time=dict(runtime_utc_timestamp='not recorded in original report; cannot recover a trustworthy UTC run start/end',original_report_file_mtime_utc=utc((root/ROLES['native_report']).stat().st_mtime),mtime_meaning='Filesystem mtime retained when native report was archived; post-run observation, not runtime UTC sampling.',runtime_monotonic_wall_ms_range=[min(times),max(times)] if times else None),git_provenance=git_context(root,deps,cache) if include_git else {'fixture':'in_memory_validation_no_git_attestation'},tools={script.relative_to(ROOT).as_posix():sha(script.read_bytes()),tests.relative_to(ROOT).as_posix():sha(tests.read_bytes())},limitations=['Conservative static literal graph plus explicitly resolved motion manifests; not a runtime file-access trace. Inherited test scripts can contribute branches not executed in this capture.','Godot imported cache/engine binary/display server/OS are not captured; .godot cache is intentionally not read.','Revalidation detects current dependency changes; it cannot retroactively prove historical absence of edits between observations.','Do not silently regenerate to preserve a passing label after input changes; old run evidence becomes stale until reviewed/recollected as appropriate.'])
def validate(contract,root=ROOT,read=None):
 if contract.get('association_mode')!='post_run_supplement_not_runtime_sampling':raise ValueError('post-run association mode required')
 if contract.get('required_roles')!=ROLES:raise ValueError('mandatory dependency role contract incomplete/changed')
 actual,_,_,_=closure(root,read)
 expected=contract.get('dependencies',{})
 if set(actual)!=set(expected):raise ValueError('dependency graph missing/extra files: '+str(sorted(set(actual)^set(expected))[:8]))
 for path,digest in actual.items():
  if expected[path]!=digest:raise ValueError('contract hash mismatch: '+path)
 reader=read or (lambda path:(root/path).read_bytes())
 for path,digest in contract['tools'].items():
  if sha(reader(path))!=digest:raise ValueError('gate tool changed: '+path)
 return dict(input_hashes_current=True,dependency_files=len(actual),mandatory_roles=len(ROLES),association_mode=contract['association_mode'],validated_utc=utc())
def record_validation(contract_path,summary_path,root=ROOT,read=None):
 summary=json.loads(summary_path.read_text())
 try:
  contract=json.loads(contract_path.read_text());result=validate(contract,root,read)
 except (ValueError,OSError,KeyError) as e:
  summary['input_hashes_current']=False;summary['dependency_validation_error']=str(e)
  summary_path.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
  raise
 result['dependency_contract_sha256']=sha(contract_path.read_bytes())
 summary.update(result);summary.pop('dependency_validation_error',None)
 summary['dependency_contract']='dependency-contract.json'
 summary['input_hashes_scope']='Original runtime bindings plus conservative post-run static/manifests superset; validation gate required before archive/reuse. Superset membership is not proof of runtime loading.'
 summary_path.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
 return result
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['build','validate']);args=parser.parse_args();path=ROOT/DEFAULT
 summary_path=ROOT/EVIDENCE/'validation-summary.json'
 try:
  if args.command=='build':
   contract=make_contract();validate(contract);path.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n')
  result=record_validation(path,summary_path);print(json.dumps(result,ensure_ascii=False))
 except (ValueError,OSError,KeyError,json.JSONDecodeError) as e:
  if summary_path.exists():
   summary=json.loads(summary_path.read_text());summary['input_hashes_current']=False;summary['dependency_validation_error']=str(e);summary_path.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
  raise SystemExit('DEPENDENCY CONTRACT REJECTED: '+str(e))
if __name__=='__main__':main()
