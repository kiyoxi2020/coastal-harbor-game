"""Independent exact pixel and metadata proof for assigned color-only revisions."""
from pathlib import Path
import hashlib,importlib.util,json,sys
from PIL import Image,ImageChops,ImageOps
SCRIPT=Path(__file__).resolve();COLOR=SCRIPT.parent.parent;HOE=COLOR.parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def changed(a,b,mask=None):
 d=ImageChops.difference(a.convert('RGBA'),b.convert('RGBA')).split();anydiff=d[0]
 for channel in d[1:]:anydiff=ImageChops.lighter(anydiff,channel)
 binary=anydiff.point(lambda v:255 if v else 0)
 if mask is not None:binary=ImageChops.multiply(binary,mask)
 return binary.histogram()[255]
def verify(name):
 if name not in ['south-B','north-B']:raise ValueError('unassigned directory')
 q=COLOR/name;p=HOE/name;c=json.loads((q/'candidate.json').read_text());parent=json.loads((p/'candidate.json').read_text());cfg=json.loads((q/'registration-config.json').read_text());oldcfg=json.loads((p/'registration-config.json').read_text())
 spec=importlib.util.spec_from_file_location('original_register',HOE/'register_clip.py');reg=importlib.util.module_from_spec(spec);spec.loader.exec_module(reg);reg.validate_data(q,c)
 assert c['revision_id']=='color-v2';revision=c['color_revision'];assert revision['parent_candidate_sha256']==sha(p/'candidate.json')==c['parent_candidate_sha256'];assert revision['compositor_sha256']==sha(COLOR/'compose_color.py')==sha(q/'references/compose_color.py')
 assert {k:v for k,v in cfg.items()if k!='frames'}=={k:v for k,v in oldcfg.items()if k!='frames'}
 results=[]
 for old,new,meta,a,b in zip(parent['frames'],c['frames'],revision['frames'],oldcfg['frames'],cfg['frames']):
  assert {k:v for k,v in a.items()if k!='source'}=={k:v for k,v in b.items()if k!='source'}
  for field in ['pose_id','phase','duration_ms','source_box_px','whole_frame_translation_px']:assert old[field]==new[field],field
  assert meta['phase']==new['phase'];assert meta['mask']in c['inputs']and meta['raw_gpt']in c['inputs'];assert sha(p/old['source'])==sha(q/meta['original'])
  original=Image.open(p/old['source']).convert('RGBA');out=Image.open(q/new['source']).convert('RGBA');raw=Image.open(q/meta['raw_gpt']).convert('RGBA');mask=Image.open(q/meta['mask']).convert('L')
  assert out.getchannel('A').tobytes()==original.getchannel('A').tobytes();assert mask.histogram()[0]+mask.histogram()[255]==1024*1536
  outside=changed(out,original,ImageOps.invert(mask));from_raw=changed(out.convert('RGB'),raw.convert('RGB'),mask);assert outside==from_raw==0
  low=ImageChops.multiply(mask,original.getchannel('A').point(lambda a:255 if a<220 else 0)).histogram()[255];assert low==0,'external blue glow became owner'
  translated=Image.new('L',tuple(c['canvas_px']));translated.paste(mask,tuple(new['whole_frame_translation_px']));registered_outside=changed(Image.open(q/new['file']),Image.open(p/old['file']),ImageOps.invert(translated));assert registered_outside==0
  assert meta['composition_info']['fallback_fraction']<=0.05 and meta['composition_info']['max_fallback_fraction']==0.05
  results.append(dict(phase=new['phase'],outside_source_rgba_differences=outside,outside_registered_rgba_differences=registered_outside,alpha_unchanged=True,masked_rgb_not_from_raw_pixels=from_raw,paint_low_alpha_pixels=low,changed_clothing_rgb_pixels=changed(out,original,mask),fallback_fraction=meta['composition_info']['fallback_fraction']))
 report=dict(candidate_sha256=sha(q/'candidate.json'),parent_candidate_sha256=sha(p/'candidate.json'),verification_tool_sha256=sha(SCRIPT),register_validate_data=True,all_inputs_current=True,all_non_source_pose_root_head_foot_grip_timing_metadata_equal=True,frames=results,scope='Exact color-only invariants. New hue remains pending native/user visual review; other20 groups not edited by this task.')
 (q/'evidence/exact-color-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False));return report
if __name__=='__main__':verify(sys.argv[1])
