from pathlib import Path
from PIL import Image,ImageChops
import json,hashlib
from contract_checks import assess
from composition import assemble_hat,render,binary
P=Path(__file__).resolve().parent;HEAD=P.parents[1];BASE=HEAD/'run-east'
def load_contract():
 c=json.loads((P/'contracts/idle-contract.json').read_text());masks={}
 for rel,digest in c['inputs_sha256'].items():assert hashlib.sha256((HEAD/rel).read_bytes()).hexdigest()==digest,rel
 for key,item in c['masks'].items():
  path=P/'contracts'/item['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'];masks[key]=Image.open(path).convert('L')
 return c,masks
def images(c,m,hat,result,tags,edit,selected):
 source=Image.open(HEAD/c['source_to_target']['source_image']).convert('RGBA').crop(tuple(c['source_to_target']['source_crop_px']))
 return {'base':Image.open(BASE/'references/idle_east_0-bare.png').convert('RGBA'),'old_hat':source,'hat':hat,'final':result,'owners':tags,'required_cover':m['required_cover'],'required_contact':m['required_contact'],'required_opening':m['required_opening'],'visible_head_in_edit_band':m['visible_head_in_edit_band'],'frozen_hat':m['frozen_hat'],'allowed_edit':edit,'source_checks':[{'ownership':selected,'forbidden':m['old_source_forbidden']}]}
def main():
 c,m=load_contract();base=Image.open(BASE/'references/idle_east_0-bare.png').convert('RGBA');oldhat=Image.open(BASE/'parts/idle_east_0-hat-registered.png').convert('RGBA')
 empty=Image.new('L',base.size);tags=Image.new('L',base.size);tags.paste(3,(0,0,*base.size),binary(oldhat))
 oldout,owners,edit=render(base,oldhat,tags,empty)
 original=assess({'placement_px':[0,0]},images(c,m,oldhat,oldout,owners,edit,binary(oldhat)))
 source=Image.open(HEAD/c['source_to_target']['source_image']).convert('RGBA').crop(tuple(c['source_to_target']['source_crop_px']))
 recovered,source_tags=assemble_hat(source,m['old_source_ownership'],Image.new('RGBA',base.size),empty,m['allowed_edit'],empty,m['frozen_hat'])
 recovered_out,owners,edit=render(base,recovered,source_tags,empty)
 extraction=assess({'placement_px':[0,0]},images(c,m,recovered,recovered_out,owners,edit,m['old_source_ownership']))
 assert not original['passed'] and original['non_hat_source_pixels']>0
 assert not extraction['passed'] and extraction['uncovered_contact']>0 and extraction['hat_inside_required_opening']>0
 (P/'baseline-failures.json').write_text(json.dumps({'original_extraction':original,'ownership_only_recovery':extraction,'scope':'Both are intentionally failing old candidates, not deliverables.'},indent=2)+'\n')
 print(json.dumps({'original_extraction':original,'ownership_only_recovery':extraction}))
if __name__=='__main__':main()
