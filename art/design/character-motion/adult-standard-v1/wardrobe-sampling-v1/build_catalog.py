"""Pin only the five requested wardrobe samples, without changing accepted assets."""
from pathlib import Path
import hashlib,json
from PIL import Image
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
IDS=['walk-west','run-east','hoe-west','water-south','harvest-north']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def parent(action,direction):
 if action=='walk':return json.loads((HERE.parent/'locomotion-v1/baked/export-manifest.json').read_text())
 if action=='run':return json.loads((HERE.parent/'run-four-directions-v1/candidate.json').read_text())
 cat=json.loads((HERE.parent/'farming-four-directions-v1/catalog-color-v2.json').read_text())
 record=next(r for r in cat['clips'] if (r['action_id'],r['direction'],r['garment'])==(action,direction,'B'))
 return json.loads((ROOT/record['candidate']).read_text())
def build():
 records=[]
 for id in IDS:
  path=HERE/id/'sample.json';data=json.loads(path.read_text());action,direction=id.split('-');assert (data['action_id'],data['direction'])==(action,direction)
  original=parent(action,direction)
  frames=original['frames']
  if action in ['walk','run']:frames=[f for f in frames if f['pose_id'].startswith(action+'_'+direction+'_')]
  assert len(frames)==len(data['frames'])==4
  for field in ['canvas_px','root_anchor_px','display_scale']:assert data[field]==original[field],(id,field)
  assert [(f['pose_id'],f['duration_ms']) for f in data['frames']]==[(f['pose_id'],f['duration_ms']) for f in frames],id
  assert len({f['sha256'] for f in data['frames']})==4,id
  for rel,digest in data['inputs'].items():
   assert not Path(rel).is_absolute() and '..' not in Path(rel).parts
   assert sha(path.parent/rel)==digest,(id,rel)
  for f in data['frames']+[data['idle']]:
   assert data['inputs'][f['file']]==f['sha256']==sha(path.parent/f['file'])
   assert Image.open(path.parent/f['file']).size==tuple(f.get('canvas_px',data['canvas_px']))
  assert data['idle']['pose_id']=='idle_'+direction+'_0'
  assert data['idle']['canvas_px']==[512,768] and data['idle']['root_anchor_px']==[256,708]
  assert data['idle']['display_scale']==138/582
  records.append({'id':id,'sample':path.relative_to(ROOT).as_posix(),'sha256':sha(path)})
 out=HERE/'catalog.json';out.write_text(json.dumps({'schema_version':1,'template_id':'adult-standard-v1','scope':'sampled-not-exhaustive','samples':records},ensure_ascii=False,indent=2)+'\n')
 print('Five sampled clips pinned:',sha(out))
if __name__=='__main__':build()
