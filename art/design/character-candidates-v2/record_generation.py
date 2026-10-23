from pathlib import Path
from PIL import Image
import json,sys,shutil,hashlib
ROOT=Path(__file__).resolve().parents[3];ART=Path(__file__).resolve().parent
ident,original=sys.argv[1:];jobs=json.loads((ART/'jobs.json').read_text());job=next(j for j in jobs if j['id']==ident);folder=Path(job['directory']);dest=folder/'source.png'
assert not dest.exists(),f'Refuse overwrite {dest}'
shutil.copy2(original,dest);im=Image.open(dest)
meta={'id':ident,'category':job['category'],'label':job['label'],'backend':'builtin GPT imagegen','generated_path':original,'reference_images':job['refs'],'source_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'source_size':list(im.size),'source_mode':im.mode,'status':'generated_pending_extraction'}
(folder/'generation.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');job['status']='generated';job['generated_path']=original
(ART/'jobs.json').write_text(json.dumps(jobs,ensure_ascii=False,indent=2)+'\n');print(ident,'SAVED',im.size)
