"""Color-only source assembly; both owned south/north output folders only."""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys,shutil
from PIL import Image,ImageChops,ImageOps,ImageDraw
SCRIPT=Path(__file__).resolve();COLOR=SCRIPT.parent.parent;HOE=COLOR.parent.parent
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
COMPOSITOR=module('approved_color_compositor',COLOR/'compose_color.py');REGISTER=module('hoe_registration',HOE/'register_clip.py')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def luminance(path):
 im=Image.open(path).convert('RGBA');r,g,b,a=im.split();mask=a.point(lambda v:255 if v>220 else 0)
 for m in [ImageChops.subtract(b,r).point(lambda v:255 if v>35 else 0),ImageChops.subtract(b,g).point(lambda v:255 if v>15 else 0),r.point(lambda v:255 if v<120 else 0),g.point(lambda v:255 if v<150 else 0)]:mask=ImageChops.multiply(mask,m)
 hist=im.convert('RGB').convert('L',matrix=(.2126,.7152,.0722,0)).histogram(mask);n=sum(hist);acc=0;median=None
 for i,v in enumerate(hist):
  acc+=v
  if acc>=(n+1)//2:median=i;break
 return dict(median_rec709=median,diagnostic_blue_pixels=n,owner=False)
def changed_pixels(a,b,selection=None):
 channels=ImageChops.difference(a.convert('RGBA'),b.convert('RGBA')).split();diff=channels[0]
 for channel in channels[1:]:diff=ImageChops.lighter(diff,channel)
 binary=diff.point(lambda v:255 if v else 0)
 if selection is not None:binary=ImageChops.multiply(binary,selection)
 return binary.histogram()[255]
def build(name):
 if name not in ['south-B','north-B']:raise ValueError('not an assigned color-revision directory')
 root=COLOR/name;parent=HOE/name;parent_cfg=json.loads((parent/'registration-config.json').read_text());cfg=copy.deepcopy(parent_cfg);ownership=json.loads((root/'manual-ownership.json').read_text())['polygons'];choice=json.loads((root/'raw-selection.json').read_text()) if (root/'raw-selection.json').exists() else {};frames=[];diagnostics=[]
 shutil.copy2(SCRIPT,root/'references/build_revision.py')
 for frame in cfg['frames']:
  phase=frame['phase'];original=Image.open(parent/frame['source']).convert('RGBA');raw_path=choice.get(phase,f'sources/raw-gpt-{phase}-attempt1.png');raw=Image.open(root/raw_path).convert('RGBA');polygons=ownership[phase]
  out,paint,info=COMPOSITOR.compose(original,raw,polygons)
  out_path=f'sources/composed-{phase}.png';mask_path=f'sources/paintmask-{phase}.png';out.save(root/out_path);paint.save(root/mask_path)
  outside=changed_pixels(out,original,ImageOps.invert(paint));alpha_equal=out.getchannel('A').tobytes()==original.getchannel('A').tobytes();paint_rgb_changes=changed_pixels(out.convert('RGB'),raw.convert('RGB'),paint)
  if outside or not alpha_equal or paint_rgb_changes:raise ValueError('independent pixel proof failed')
  frame['source']=out_path
  frames.append(dict(phase=phase,mask=mask_path,raw_gpt=raw_path,original=f'references/original-{phase}.png',ownership_polygons=polygons,composition_info=info,mask_coordinate_space='original source1024x1536'))
  diagnostics.append(dict(phase=phase,original=luminance(parent/parent_cfg['frames'][len(diagnostics)]['source']),raw_gpt=luminance(root/raw_path),composed=luminance(root/out_path),outside_mask_rgba_differences=outside,original_alpha_unchanged=alpha_equal,paint_rgb_not_from_raw_pixels=paint_rgb_changes,fallback_fraction=info['fallback_fraction'],max_fallback_fraction=info['max_fallback_fraction']))
  # Diagnostic overlay only, never used as art or ownership input.
  overlay=original.copy();highlight=Image.new('RGBA',original.size,(255,0,120,255));overlay=Image.composite(highlight,overlay,paint.point(lambda v:125 if v else 0));overlay.save(root/f'evidence/ownership-overlay-{phase}.png')
 if any({k:v for k,v in a.items() if k!='source'}!={k:v for k,v in b.items() if k!='source'} for a,b in zip(parent_cfg['frames'],cfg['frames'])):raise ValueError('non-source pose/timing metadata changed')
 dump(root/'registration-config.json',cfg)
 color=dict(parent_candidate_sha256=sha(parent/'candidate.json'),compositor_sha256=sha(COLOR/'compose_color.py'),frames=frames)
 dump(root/'provenance.json',dict(generator='built-in image_gen',exact_image_model='not returned; not inferred',revision_id='color-v2',parent_candidate_sha256=color['parent_candidate_sha256'],color_revision=color,policy='GPT fabric RGB only through manual surface ownership; all original alpha and nonpaint RGBA exact. No lighting/pose/tool/body/timing changes.',parent_non_color_visual_scope_retained=True,new_color_user_accepted=False))
 dump(root/'color-diagnostics.json',dict(scope='Non-owning blue diagnostic, not formal garment ownership or a blind color acceptance threshold',criteria='A>220,B-R>35,B-G>15,R<120,G<150; uint8 Rec709 luminance median',reference=luminance(root/'references/approved-water-color.png'),frames=diagnostics))
 c=REGISTER.build(root);c.update(revision_id='color-v2',parent_candidate_sha256=color['parent_candidate_sha256'],color_revision=color,parent_non_color_visual_scope_retained=True,new_color_user_accepted=False)
 for path in ['manual-ownership.json','color-diagnostics.json','raw-selection.json']:c['inputs'][path]=sha(root/path)
 c.pop('artifact_digest',None);c['artifact_digest']=REGISTER.digest(c);dump(root/'candidate.json',c);REGISTER.validate_data(root,c)
 print(json.dumps(dict(candidate=str(root/'candidate.json'),sha256=sha(root/'candidate.json'),outside_mask_rgba_differences=0,all_alpha_unchanged=True,color=[(d['phase'],d['composed']['median_rec709'],round(d['fallback_fraction'],5))for d in diagnostics]),ensure_ascii=False))
 return c
if __name__=='__main__':build(sys.argv[1])
