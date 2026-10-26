"""Preserve accepted20 records verbatim; select only four corrected hoe-B clips."""
from pathlib import Path
import hashlib,json,importlib.util
ROOT=Path(__file__).resolve().parent
HOE=ROOT.parents[1]
CATALOG_ROOT=HOE.parent
REPO=CATALOG_ROOT.parents[4]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def build():
 spec=importlib.util.spec_from_file_location('hoe_registration',HOE/'register_clip.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 original=json.loads((CATALOG_ROOT/'catalog-before-color-v2.json').read_text())
 for record in original['clips']:
  if record['action_id']=='hoe' and record['garment']=='B':
   path=ROOT/(record['direction']+'-B')/'candidate.json';m.validate(path)
   record['candidate']=str(path.relative_to(REPO));record['sha256']=sha(path);record['note']=record['note'].replace('待你验收。','仅长袖衣色修订，待确认。')
 original['scope']='24fixed outfits;only four hoe-B shirt palettes changed;color-only revision pending visual review.20other clip records are identical to accepted catalog.'
 path=CATALOG_ROOT/'catalog-color-v2.json';path.write_text(json.dumps(original,ensure_ascii=False,indent=2)+'\n');print(path,sha(path))
if __name__=='__main__':build()
