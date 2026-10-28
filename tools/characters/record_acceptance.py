"""Retain lightweight, scope-preserving acceptance links to immutable Git history."""
from pathlib import Path
import json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[2];LIB=ROOT/'art/characters';M='art/design/character-motion/adult-standard-v1'
CASES={
 'locomotion':['locomotion-v1/visual-acceptance.json'],
 'run':['run-four-directions-v1/visual-acceptance-2026-10-26.json','run-four-directions-v1/visual-acceptance-long-sleeves-2026-10-26.json'],
 'farming':['farming-four-directions-v1/visual-acceptance-final-2026-10-26.json'],
 'wardrobe':['wardrobe-sampling-v1/visual-acceptance-2026-10-26.json'],
 'headwear-run-east':['headwear-sampling-v1/revisions/run-east-hat-approved-v5/visual-acceptance-dynamic-2026-10-27.json'],
 'headwear-hoe-west':['headwear-sampling-v1/revisions/hoe-west-ear-v3/visual-acceptance-2026-10-28.json']}

def main():
 mapping=json.loads((LIB/'migrations/2026-10-resource-layout/dynamic-path-map.json').read_text());ref=mapping['baseline_commit'];files=mapping['files']
 groups={
 'locomotion':[x for x in files if x['new_path']=='art/characters/builds/locomotion-r001/manifest.json'],
 'run':[x for x in files if x['new_path'] in ['art/characters/builds/run-r001/candidate.json','art/characters/builds/run-r001/run-garments.json','art/characters/builds/run-r001/run-diagnostics.json']],
 'farming':[x for x in files if x['type']=='new-path-manifest' and x['new_path'].startswith('art/characters/builds/farming-')],
 'wardrobe':[x for x in files if x['type']=='new-path-manifest' and x['new_path'].startswith('art/characters/builds/wardrobe-')],
 'headwear-run-east':[x for x in files if x['new_path']=='art/characters/builds/headwear-run-east-r001/sample.json'],
 'headwear-hoe-west':[x for x in files if x['new_path']=='art/characters/builds/headwear-hoe-west-r001/sample.json']}
 for case,origins in CASES.items():
  records=[]
  for relative in origins:
   old=M+'/'+relative;raw=subprocess.check_output(['git','show',ref+':'+old],cwd=ROOT);data=json.loads(raw)
   record={'git_commit':ref,'path':old,'sha256':hashlib.sha256(raw).hexdigest(),'date':data.get('date',data.get('accepted_at_utc')),'user_statement':data.get('user_statement',data.get('user_message',data.get('user_feedback'))),'scope':data.get('accepted_scope',data.get('scope')),'limits':data.get('limits',data.get('not_implied',data.get('excluded_feedback')))}
   records.append(record)
  output={'kind':'original-user-acceptance-with-migration-equivalence','original_acceptance_records':records,'migrated_subjects':groups[case],'equivalence':'migrations/2026-10-resource-layout/dynamic-path-map.json','native_migration_receipt':'evidence/layout-native/receipt.json','policy':'Original visual approval applies only to its recorded scope after exact pixel/pose/config equivalence. This record does not claim new user operations or newly supported combinations.'}
  p=LIB/'evidence'/case/'acceptance.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
 coverage=json.loads((LIB/'coverage.json').read_text())
 for row in coverage['rows']:
  row['migration_native']='derived from evidence/layout-native/receipt.json; absent or invalid receipt means unverified'
  key=row['user_acceptance']
  if key.startswith('wardrobe-'):key='wardrobe'
  if key!='not-recorded':row['user_acceptance']='evidence/'+key+'/acceptance.json'
 (LIB/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
 print('Recorded',len(CASES),'lightweight acceptance bundles; original scopes and Git references retained.')
if __name__=='__main__':main()
