"""Bind the bounded hoe-west native rerun to the existing strict coverage gates."""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path

P=Path(__file__).resolve().parent
ROOT=P.parents[6]
HEAD=P.parents[1]
spec=importlib.util.spec_from_file_location('headwear_evidence',HEAD/'evidence_contract.py')
legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
CATALOG=P/'catalog.json'
NATIVE='godot2d/tests/test_character_headwear_hoe_native.gd'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def tool_dependencies():
    files={Path(path).resolve() for path in [__file__,legacy.__file__,legacy.base.__file__,legacy.wardrobe.__file__]}
    return {path.relative_to(ROOT).as_posix():sha(path) for path in sorted(files)}

def assert_tool_dependencies(expected):
    if expected!=tool_dependencies():raise ValueError('Called validation-tool implementation changed.')

def target_clips():
    return {'hoe-west':legacy.clip_metadata(ROOT,CATALOG)['hoe-west']}

def check_coverage(report,expected):
    original_ids=legacy.IDS
    try:
        legacy.IDS={'hoe-west'}
        legacy.report_coverage(report,expected)
    finally:legacy.IDS=original_ids

def snapshot(path):
    path=Path(path)
    if path.exists():raise ValueError('Do not overwrite capture input contract.')
    c={'scope':'Changed hoe-west only; other three samples load unchanged, not newly visually accepted.',
       'snapshot_utc':legacy.base.utc(),'sample_dependencies':legacy.collect(ROOT,CATALOG),
       'expected_clips':target_clips(),'tool_sha256':sha(__file__),
       'validation_tools':tool_dependencies(),
       'baseline_contract':legacy.base.make_snapshot(ROOT,HEAD.parent/'farming-four-directions-v1/catalog-color-v2.json',NATIVE)}
    c['artifact_digest']=legacy.base.canonical_digest(c)
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(c,indent=2)+'\n')
    print('Frozen bounded hoe-west native inputs:',len(c['sample_dependencies']))

def validate(contract,report,receipt):
    contract,report,receipt=map(Path,[contract,report,receipt])
    # Reject aliases before either success or failure can write a receipt.
    declared=json.loads(report.read_text())
    outputs=declared.get('output_hashes',{})
    if not isinstance(outputs,dict):raise ValueError('Native output hashes must be a mapping.')
    protected=[contract,report]
    for rel in outputs:
        legacy.base.relative(rel)
        protected.append(report.parent/rel)
    for source in protected:
        if receipt.resolve()==source.resolve() or receipt.exists() and receipt.samefile(source):
            raise ValueError('Receipt cannot overwrite evidence.')
    result={'archive_allowed':False,'scope':'hoe-west only'}
    try:
        c=json.loads(contract.read_text());digest=c.pop('artifact_digest')
        assert_tool_dependencies(c['validation_tools'])
        legacy.base.require(digest==legacy.base.canonical_digest(c),'contract digest changed')
        legacy.base.validate_snapshot(c['baseline_contract'],ROOT)
        legacy.base.require(c['sample_dependencies']==legacy.collect(ROOT,CATALOG),'source/texture/mask closure changed')
        legacy.base.require(c['expected_clips']==target_clips(),'pose/timing metadata changed')
        legacy.base.require(c['tool_sha256']==sha(__file__),'validator changed')
        r=json.loads(report.read_text())
        legacy.base.require(r['input_contract_sha256']==sha(contract),'native input binding differs')
        legacy.base.require(r['catalog_sha256']==sha(CATALOG),'native catalog differs')
        # Reuse all existing exact output/check sets and ten-cycle time gates.
        check_coverage(r,c['expected_clips'])
        times=[legacy.base.declared_utc(c['snapshot_utc']),legacy.base.declared_utc(r['started_utc'],True),legacy.base.declared_utc(r['finished_utc'],True)]
        legacy.base.require(int(times[0].timestamp())<=int(times[1].timestamp())<=int(times[2].timestamp())<=int(datetime.datetime.now(datetime.timezone.utc).timestamp()),'capture time order invalid')
        for rel,digest in r['output_hashes'].items():
            legacy.base.relative(rel)
            legacy.base.require(sha(report.parent/rel)==digest,'native capture changed: '+rel)
        result.update(archive_allowed=True,input_contract_sha256=sha(contract),native_report_sha256=sha(report),validated_utc=legacy.base.utc(),native_check_count=len(r['checks']),captures=len(r['captures']))
    except Exception as exc:result['error']=str(exc)
    receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
    return result['archive_allowed']

if __name__=='__main__':
    p=argparse.ArgumentParser();commands=p.add_subparsers(dest='command',required=True)
    s=commands.add_parser('snapshot');s.add_argument('--output',required=True)
    v=commands.add_parser('validate');v.add_argument('--contract',required=True);v.add_argument('--report',required=True);v.add_argument('--receipt',required=True)
    a=p.parse_args()
    if a.command=='snapshot':snapshot(a.output)
    else:raise SystemExit(0 if validate(a.contract,a.report,a.receipt) else 1)
