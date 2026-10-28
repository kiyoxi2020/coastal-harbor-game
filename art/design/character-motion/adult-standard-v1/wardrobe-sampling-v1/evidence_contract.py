"""Extend the existing dependency gate with five sampled wardrobe manifests."""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
OLD=HERE.parent/'farming-four-directions-v1/evidence_contract.py'
spec=importlib.util.spec_from_file_location('farming_contract',OLD);base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
IDS={'walk-west','run-east','hoe-west','water-south','harvest-north'}
CATALOG=HERE/'catalog.json'
NATIVE='godot2d/tests/test_character_wardrobe_native.gd'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def collect(root,catalog):
 root=Path(root).resolve();catalog=Path(catalog).resolve();dependencies={}
 def add(path,expected=None):
  path=Path(path).resolve();rel=path.relative_to(root).as_posix();actual=sha(path)
  if expected is not None and expected!=actual:raise ValueError('input hash mismatch: '+rel)
  dependencies[rel]=actual
 add(catalog);data=json.loads(catalog.read_text())
 if data.get('schema_version')!=1 or data.get('scope')!='sampled-not-exhaustive' or len(data.get('samples',[]))!=5:raise ValueError('expected five sampled clips')
 seen=set()
 for entry in data['samples']:
  if entry['id'] not in IDS or entry['id'] in seen:raise ValueError('duplicate/unknown sample')
  seen.add(entry['id']);base.relative(entry['sample']);path=root/entry['sample'];add(path,entry['sha256']);sample=json.loads(path.read_text())
  if sample['action_id']+'-'+sample['direction']!=entry['id']:raise ValueError('sample capability mismatch')
  for rel,digest in sample['inputs'].items():base.relative(rel);add(path.parent/rel,digest)
 return dict(sorted(dependencies.items()))
def snapshot(output):
 output=Path(output)
 if output.exists():raise ValueError('snapshot already exists')
 old=base.make_snapshot(ROOT,HERE.parent/'farming-four-directions-v1/catalog-color-v2.json',NATIVE)
 c={'schema_version':1,'capture_phase':'before_native_capture','snapshot_utc':base.utc(),'baseline_contract':old,'sample_dependencies':collect(ROOT,CATALOG),'tool_sha256':sha(__file__),'scope':'Five explicitly sampled action-direction recipes; conservative static+baseline and complete sample inputs, not runtime load trace.'}
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
  base.require(c['tool_sha256']==sha(__file__),'contract tool changed')
  r=json.loads(Path(report).read_text());base.require(r['input_contract_sha256']==sha(contract),'report contract binding mismatch')
  base.require(len(r['clips'])==5 and set(r['clips'])==IDS and r['checks'] and all(v is True for v in r['checks'].values()),'native checks incomplete/failed')
  before=base.declared_utc(c['snapshot_utc']);start=base.declared_utc(r['started_utc'],True);end=base.declared_utc(r['finished_utc'],True)
  base.require(int(before.timestamp())<=int(start.timestamp())<=int(end.timestamp())<=int(datetime.datetime.now(datetime.timezone.utc).timestamp()),'capture time order invalid')
  out.update(archive_allowed=True,input_hashes_current=True,input_contract_sha256=sha(contract),native_report_sha256=sha(report),validated_utc=base.utc(),sample_count=5)
 except Exception as exc:out['error']=str(exc)
 Path(receipt).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));return out['archive_allowed']
if __name__=='__main__':
 p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True);a=s.add_parser('snapshot');a.add_argument('--output',required=True);a=s.add_parser('validate');a.add_argument('--contract',required=True);a.add_argument('--report',required=True);a.add_argument('--receipt',required=True);args=p.parse_args()
 if args.command=='snapshot':snapshot(args.output)
 else:raise SystemExit(0 if validate(args.contract,args.report,args.receipt) else 1)
