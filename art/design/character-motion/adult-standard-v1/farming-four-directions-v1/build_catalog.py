"""Publish only the complete fixed-outfit 24-clip review catalog."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[4]
PHASES={'hoe':['ready','lift','contact','recovery'],'water':['ready','raise','pour','recovery'],'harvest':['ready','reach','pluck','recovery']}
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def build():
 records=[]
 names={'hoe':'锄地','water':'浇水','harvest':'收获','south':'南向','west':'西向','east':'东向','north':'北向','A':'短袖','B':'长袖'}
 for action in PHASES:
  for direction in ['south','west','east','north']:
   for garment in ['A','B']:
    path=ROOT/action/(direction+'-'+garment)/'candidate.json';data=json.loads(path.read_text())
    if (data['action_id'],data['direction'],data['garment'])!=(action,direction,garment):raise ValueError('wrong capability '+str(path))
    if [f.get('phase') for f in data['frames']]!=PHASES[action] or len({f['sha256'] for f in data['frames']})<4:raise ValueError('not complete real phases '+str(path))
    for ref,digest in data['inputs'].items():
     p=Path(ref)
     if p.is_absolute() or '..' in p.parts or sha(path.parent/p)!=digest:raise ValueError('input mismatch '+str(path)+' '+ref)
    for frame in data['frames']:
     if sha(path.parent/frame['file'])!=frame['sha256'] or data['inputs'].get(frame['source'])!=frame['source_sha256']:raise ValueError('texture/source mismatch '+str(path))
    ms=sum(f['duration_ms'] for f in data['frames'])
    records.append({'action_id':action,'direction':direction,'garment':garment,'candidate':str(path.relative_to(REPO)),'sha256':sha(path),'note':f'{names[direction]}{names[garment]} · {names[action]} · 4姿态/{ms}ms，待你验收。'})
 result={'schema_version':2,'template_id':'adult-standard-v1','scope':'24 fixed-outfit complete farming review sequences. No new user approval, independent garment composition or production gameplay claim.','clips':records}
 (ROOT/'catalog.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print('complete catalog',len(records),'sha256',sha(ROOT/'catalog.json'))
if __name__=='__main__':build()
