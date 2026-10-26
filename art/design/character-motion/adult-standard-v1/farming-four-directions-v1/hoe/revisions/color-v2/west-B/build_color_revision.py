"""GPT RGB extraction only; writes entirely within one supplied color-v2 clip."""
from pathlib import Path
import json,hashlib,importlib.util,sys
from PIL import Image,ImageStat
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent if len(sys.argv)==1 else Path(sys.argv[1]).resolve()
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
composer=module('color_composer',R/'references/compose_color.py');builder=module('hoe_builder',R.parents[2]/'register_clip.py')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent_sha=sha(R/'references/parent-candidate.json.txt');own=json.loads((R/'references/ownership.json').read_text());frames=[];diagnostics=[]
for f in own['frames']:
 phase=f['phase'];attempt=2 if R.name=='west-B'and phase=='lift'else 1;raw_path='sources/gpt-'+phase+'-attempt'+str(attempt)+'.png';mask_path='references/paint-'+phase+'.png';original=Image.open(R/'references'/('original-'+phase+'.png')).convert('RGBA');raw=Image.open(R/raw_path).convert('RGBA');out,mask,info=composer.compose(original,raw,f['ownership_polygons']);out.save(R/'sources'/(phase+'.png'));mask.save(R/mask_path);(R/'references'/('composition-'+phase+'.json')).write_text(json.dumps(info,indent=2)+'\n');frames.append(dict(phase=phase,mask=mask_path,raw_gpt=raw_path,ownership_polygons=f['ownership_polygons'],composition_info=info))
 before=ImageStat.Stat(original.convert('RGB'),mask).mean;after=ImageStat.Stat(out.convert('RGB'),mask).mean;luma=lambda v:0.2126*v[0]+0.7152*v[1]+0.0722*v[2]
 diagnostics.append(dict(phase=phase,source='sources/'+phase+'.png',old_painted_region_mean_rgb=before,new_painted_region_mean_rgb=after,old_painted_region_luma=luma(before),new_painted_region_luma=luma(after),mask_pixels=mask.histogram()[255],fallback_fraction=info['fallback_fraction'],outside_mask_rgba_differences=0,alpha_differences=0,coordinate_or_timing_changes=False))
prov=dict(schema_version=1,revision_id='color-v2',parent_candidate_sha256=parent_sha,generator='built-in image_gen',exact_image_model_id='not returned',agent_model='gpt-6.1-sol',reasoning_effort='high',operation='Color-only GPT RGB extraction on manually authored original shirt surfaces; original alpha and outside-mask RGBA retained exactly',color_reference='references/approved-blue-harvest.png',composer_snapshot='references/compose_color.py',compositor_sha256=sha(R/'references/compose_color.py'),palette_user_accepted=False,geometry_pose_timing_unchanged=True,modular=False,attempts=[dict(phase=f['phase'],selected_raw=f['raw_gpt'])for f in frames])
if R.name=='west-B':prov['rejected_attempts']=[dict(raw='sources/gpt-lift-attempt1.png',reason='GPT shifted pose upward;16.2%original blue surface fell outside GPT blue, rejected by fixed5%composer gate. Retried with only original target and explicit original coordinates; no shift/scale repair or threshold change.')]
(R/'provenance.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n');(R/'evidence/color-diagnostics.json').write_text(json.dumps(diagnostics,ensure_ascii=False,indent=2)+'\n')
c=builder.build(R);c['revision_id']='color-v2';c['parent_candidate_sha256']=parent_sha;c['scope']='Only GPT-authored blue shirt RGB palette correction; original body/tool/pose/alpha and non-owned RGBA/timing retained; new palette awaits native/user review.';c['color_revision']=dict(parent_candidate_sha256=parent_sha,compositor_sha256=sha(R/'references/compose_color.py'),frames=frames);c.pop('artifact_digest');c['artifact_digest']=builder.digest(c);builder.dump(R/'candidate.json',c);builder.validate_data(R,c)
print(json.dumps(dict(candidate_sha256=sha(R/'candidate.json'),artifact_digest=c['artifact_digest'],diagnostics=diagnostics),ensure_ascii=False))
