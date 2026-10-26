"""Expose only checked garment capabilities through the existing trial contract."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    candidate=json.loads((ROOT/'candidate.json').read_text())
    recipes={'A':{d:[f'registered/run_{d}_{i}.png' for i in range(4)] for d in candidate['directions']},'B':{d:[f'baked/B_{d}_{i}.png' for i in range(4)] for d in ['west','east']}}
    paths={p for dirs in recipes.values() for frames in dirs.values() for p in frames}
    parts=json.loads((ROOT/'parts-manifest.json').read_text())
    for g in ['A','B']:
        for f in parts['recipes'][g]['frames']:
            if f['direction'] not in ['west','east']:continue
            for l in f['layers']:
                for key in ['source','hide_mask','hidden_source','hidden_mask']:
                    if key in l:paths.add(l[key])
    paths.update(['candidate.json','build_garment_manifest.py','sources/west/parts-manifest.json'])
    m={'candidate_manifest_sha256':sha(ROOT/'candidate.json'),'scope':'A four directions; real same-body layered B only west/east. South source drift and north alpha/ownership failures are explicitly rejected. No independent pants/shoes or complete naked body.','recipes':recipes,'inputs':{p:sha(ROOT/p) for p in sorted(paths)},'rejected_capabilities':{'B':['south','north']},'user_accepted':False}
    (ROOT/'run-garments.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
    print('Enabled A:south/west/east/north; B:west/east. Rejected B:south/north.')
if __name__=='__main__':main()
