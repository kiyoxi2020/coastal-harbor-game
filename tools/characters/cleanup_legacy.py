"""Remove verified Git-restorable character working history after native migration passes.

Unknown/untracked content is preserved in a temporary holding directory, never
silently erased. Production player-unified-v4 is deliberately outside this scope.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess
ROOT=Path(__file__).resolve().parents[2]
LIB=ROOT/'art/characters';META=LIB/'migrations/2026-10-resource-layout'
OLD_ROOTS=['art/design/character-motion','art/design/character-bodies','art/design/character-candidates-v2','art/design/character-head-proof-v1','art/design/character-clothing-proof-v1','art/design/character-library-v1','godot2d/assets/characters/adult-standard-v1/head-proof','godot2d/scenes/reviews/character_head_proof.tscn']
HOLD=Path('/private/tmp/coastal-character-layout-untracked-hold')
PENDING=Path('/private/tmp/coastal-layout-cleanup-inventory.json')

def sha(data):return hashlib.sha256(data).hexdigest()
def json_write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def baseline():
 ref=json.loads((META/'dynamic-path-map.json').read_text())['baseline_commit'];blobs={}
 for record in subprocess.check_output(['git','ls-tree','-rz','--full-tree','-r',ref],cwd=ROOT).split(b'\0'):
  if record:
   fields,path=record.split(b'\t',1);blobs[path.decode()]=fields.split()[2].decode()
 return ref,blobs

def prepare():
 ref,blobs=baseline();files=[];changed=[]
 for relative in OLD_ROOTS:
  folder=ROOT/relative
  if not folder.exists():continue
  paths=[folder] if folder.is_file() else sorted(q for q in folder.rglob('*') if q.is_file())
  for path in paths:
   old=path.relative_to(ROOT).as_posix();data=path.read_bytes();object_id=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
   if old in blobs:
    if object_id!=blobs[old]:changed.append(old)
    action='remove-git-restorable'
   elif '__pycache__' in path.parts or path.suffix=='.pyc' or path.name=='.DS_Store':action='remove-regenerable-cache'
   else:action='preserve-untracked-in-temporary-hold'
   files.append({'old_path':old,'bytes':len(data),'sha256':sha(data),'git_blob':blobs.get(old),'action':action})
 if changed:raise ValueError('User-modified tracked history must be reconciled first: '+str(changed))
 result={'schema_version':1,'baseline_commit':ref,'scope':OLD_ROOTS,'files':files,'counts':{action:sum(x['action']==action for x in files) for action in sorted({x['action'] for x in files})},'total_bytes':sum(x['bytes'] for x in files),'temporary_hold':str(HOLD),'recovery':'git show '+ref+':<old_path> ; use an isolated checkout for full old-layout tools/evidence','production_old_model_preserved':True,'applied':False}
 json_write(PENDING,result);print(json.dumps({'counts':result['counts'],'MiB':round(result['total_bytes']/1024**2,2)}));return result

def apply():
 receipt_path=LIB/'evidence/layout-native/receipt.json';receipt=json.loads(receipt_path.read_text())
 if receipt.get('archive_allowed') is not True:raise ValueError('Validated real GPU migration receipt required before cleanup')
 # Use the actual validator, not just the receipt flag.
 contract=Path('/private/tmp/coastal-character-layout-native/input-contract.json');report=contract.parent/'report.json'
 subprocess.run(['python3',str(ROOT/'tools/characters/native_contract.py'),'validate','--contract',str(contract),'--report',str(report),'--receipt','/private/tmp/coastal-layout-before-cleanup-'+__import__('uuid').uuid4().hex+'.json'],cwd=ROOT,check=True)
 inventory=prepare();held=[]
 for item in inventory['files']:
  path=ROOT/item['old_path']
  if sha(path.read_bytes())!=item['sha256']:raise ValueError('File changed after cleanup inventory: '+item['old_path'])
  if item['action']=='preserve-untracked-in-temporary-hold':
   dest=HOLD/item['old_path'];dest.parent.mkdir(parents=True,exist_ok=True)
   if dest.exists():raise ValueError('Refuse to overwrite holding file: '+str(dest))
   shutil.move(str(path),str(dest));held.append(item)
  else:path.unlink()
 for relative in OLD_ROOTS:
  path=ROOT/relative
  if path.is_dir():
   for directory in sorted((x for x in path.rglob('*') if x.is_dir()),key=lambda x:len(x.parts),reverse=True):directory.rmdir()
   path.rmdir()
 if held:json_write(HOLD/'inventory.json',{'baseline_commit':inventory['baseline_commit'],'files':held,'note':'Untracked historical files preserved during approved cleanup; no content silently deleted.'})
 inventory['applied']=True;inventory['held_untracked_count']=len(held);json_write(META/'cleanup-inventory.json',inventory)
 print(json.dumps({'legacy_cleanup_applied':True,'held_untracked':len(held),'removed_MiB':round(inventory['total_bytes']/1024**2,2)}))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','apply']);a=p.parse_args()
 if a.command=='prepare':prepare()
 else:apply()
