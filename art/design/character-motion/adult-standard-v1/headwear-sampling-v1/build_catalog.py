"""Index only the four explicitly produced headwear samples; no acceptance inferred."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
IDS=['run-east','hoe-west','water-south','harvest-north']
if __name__=='__main__':
 records=[]
 for id in IDS:
  path=HERE/id/'sample.json';data=json.loads(path.read_text())
  if data['action_id']+'-'+data['direction']!=id:raise ValueError('sample identity mismatch')
  records.append({'id':id,'sample':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 (HERE/'catalog.json').write_text(json.dumps({'schema_version':1,'template_id':'adult-standard-v1','scope':'sampled-headwear-not-exhaustive','headwear_designs':{'hair':{'design_id':'hair-chestnut-short-v1','label':'栗色短发','pose_views':'Per-sample parts/registration; no compatibility outside sampled poses.'},'hat':{'design_id':'hat-straw-navy-band-v1','label':'藏蓝缎带草帽','pose_views':'Per-sample parts/registration; hair_hat uses explicit tucked-hair variant.'}},'samples':records},indent=2)+'\n')
 print('Indexed four headwear samples; visual acceptance pending.')
