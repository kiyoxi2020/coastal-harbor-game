from pathlib import Path
import json,importlib.util,hashlib
A=Path(__file__).resolve().parent;R=A.parents[2];H=R/'art/design/character-head-proof-v1'
spec=importlib.util.spec_from_file_location('head',H/'build_head_proof.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
c=json.loads((A/'catalog.json').read_text());policy=json.loads((H/'semantic-masks.json').read_text())
for cat in ['hair','hat']:
 e=c['categories'][cat][0];folder=A/cat/(cat+'01')/'components';folder.mkdir(parents=True,exist_ok=True)
 atlas=m.Image.open(R/e['source']).convert('RGBA')
 for i,d in enumerate(['south','west','east','north']):
  part,mask=m.layer(atlas,i,policy[cat+'_polygons'][d],cat=='hair');p=folder/(d+'.png');part.save(p);mp=folder/('owner-'+d+'.png');mask.save(mp)
  e['components'][d]=str(p.relative_to(R));e['hashes'][str(p.relative_to(R))]=m.sha(p);e['hashes'][str(mp.relative_to(R))]=m.sha(mp)
 e['hashes'][str((H/'semantic-masks.json').relative_to(R))]=m.sha(H/'semantic-masks.json')
 e['provenance']='Re-extracted existing approved GPT source using original reviewed semantic polygons; old proof filename contains composed body, so it is not a component.'
(A/'catalog.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
print('Baseline head source layers extracted independently of composed proof filenames')
