from pathlib import Path
import json,hashlib
A=Path(__file__).resolve().parent;R=A.parents[2]
p=A/'catalog.json';c=json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
master=R/c['categories']['body'][0]['source'];h=sha(master)
for cat,items in c['categories'].items():
 c['categories'][cat]=items[:1]
 for e in c['categories'][cat]:
  e['design_id']=e['id'];e['template_hash']=h
  paths=[R/'art/design/character-bodies/adult-standard-v1/selection.json']
  if cat in ['top','pants','shoes']:
   base=R/'art/design/character-clothing-proof-v1';paths.extend([base/'semantic-masks.json',base/'build_clothing_proof.py'])
   paths.extend(base/'parts'/(cat+'-owner_'+d+'.png') for d in ['south','west','east','north'])
  if cat in ['hair','hat']:paths.append(A/'restore_baseline_head_layers.py')
  e['hashes'].update({str(x.relative_to(R)):sha(x) for x in paths})
for file in ['wearables-built.json','head-body-built.json']:
 if not (A/file).exists():continue
 data=json.loads((A/file).read_text());entries=list(data['entries'].values()) if isinstance(data,dict) else data
 for e in entries:
  if not e.get('components') or e.get('status')!='candidate':continue
  cat=e.get('category') or next(x for x in c['categories'] if e['id'].startswith(x))
  c['categories'][cat].append(e)
jobs={j['id']:j for j in json.loads((A/'jobs.json').read_text())}
for cat,items in c['categories'].items():
 items.sort(key=lambda x:x['id'])
 for e in items:
  roots={'south':[230,707],'west':[251,708],'east':[268,708],'north':[282,708]}
  if cat=='body' and e['id']!='body01':
   roots={d:m['root_anchor'] for d,m in e['extraction']['metrics'].items()}
  j=jobs.get(e['id'])
  if j:
   refs={str(Path(r).relative_to(R)):sha(Path(r)) for r in j['refs']}
   e['reference_images']=refs;e['hashes'].update(refs)
   provenance=Path(j['directory'])/'generation.json'
   if provenance.exists():e['hashes'][str(provenance.relative_to(R))]=sha(provenance)
  e['display']={'scale':0.2371134,'root_anchors':roots,'scope':'uniform native review scale; independent body candidates are not registered gameplay rigs'}
 print(cat,len(items))
p.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
