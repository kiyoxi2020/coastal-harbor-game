"""Register complete generated water frames. No local rescaling/mirroring/retouch."""
from pathlib import Path
import argparse,hashlib,json,math,shutil
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def build(combo):
 directory=ROOT/combo;cfg=json.loads((directory/'registration-config.json').read_text());frames=[];measurements=[]
 for i,f in enumerate(cfg['frames']):
  original=Image.open(directory/f['source']).convert('RGBA');box=f.get('source_box_px',[0,0,*original.size]);cell=original.crop(tuple(box))
  if cell.size!=(1024,1536):raise ValueError('Expected native1024x1536 single frame; never upsample sheet cells')
  dx,dy=[cfg['root_anchor_px'][j]-f['source_root_px'][j] for j in range(2)]
  if not all(type(x)is int for x in [*box,dx,dy]):raise ValueError('integer registration required')
  if dx<0 or dy<0 or dx+1024>cfg['canvas_px'][0] or dy+1536>cfg['canvas_px'][1]:raise ValueError('full generated source does not fit')
  registered=Image.new('RGBA',tuple(cfg['canvas_px']));registered.paste(cell,(dx,dy));rel=f'registered/water_{cfg["direction"]}_{cfg["garment"]}_{i}.png';registered.save(directory/rel)
  frames.append(dict(pose_id=f'water_{cfg["direction"]}_{cfg["garment"]}_{f["phase"]}',phase=f['phase'],duration_ms=f['duration_ms'],file=rel,sha256=sha(directory/rel),source=f['source'],source_sha256=sha(directory/f['source']),source_box_px=box,whole_frame_translation_px=[dx,dy]))
  measurements.append(dict(phase=f['phase'],source=f['source'],source_canvas_px=list(original.size),visible_alpha_bbox_ge128=cell.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox(),source_root_px=f['source_root_px'],whole_frame_translation_px=[dx,dy],visible_foot_points_px=f['visible_foot_points_px'],visible_grip_points_px=f['visible_grip_points_px'],visible_landmarks_px=f['visible_landmarks_px'],water_landing_px=f.get('water_landing_px'),hidden_joints_px=dict(hip=None,left_knee=None,right_knee=None,left_ankle=None,right_ankle=None),uncertainty_source_px=dict(clear_outline=8,manual_grip_surface=24,occluded_contact=None)))
 dump(directory/'measurements.json',dict(schema_version=1,method='Visible surface/outline observations in unscaled source coordinates: clear contours ±8px, rough grip surfaces up to ±24px; exact occluded contacts null. Some shoe contours color-assisted then visually reviewed. Hidden joints null, not percentage estimates. Root derives from observed footwear; equal root after registration is not passed support trajectory. This measurement precision cannot establish the unchanged <=1screenpx acceptance target.',frames=measurements,scope='Fixed clothed complete frames. No independent body/garment layers, exact grip/rigidity/contact trajectory or visual acceptance.'))
 shutil.copy2(Path(__file__),directory/'registration-tool.py')
 inputs={p.relative_to(directory).as_posix():sha(p) for folder in ['sources','prompts','references'] for p in sorted((directory/folder).glob('*')) if p.is_file()}
 for name in ['registration-config.json','measurements.json','provenance.json','registration-tool.py']:
  if (directory/name).exists():inputs[name]=sha(directory/name)
 c=dict(schema_version=1,template_id='adult-standard-v1',motion_set_id='farming-four-directions-v1',revision_id='v1',action_id='water',direction=cfg['direction'],garment=cfg['garment'],status='complete_four_phase_fixed_outfit_trial_candidate',canvas_px=cfg['canvas_px'],root_anchor_px=cfg['root_anchor_px'],display_scale=138/1164,source_density_scale_vs_idle=2,accepted=False,geometry_checked=False,motion_checked=False,native_checked=False,modular=False,gameplay_available=False,loop=False,events=[],frames=frames,inputs=inputs,scope='Complete ready/raise/pour/recovery fixed-outfit sequence candidate; not independent clothes/body composability, full motion/contact/rigidity acceptance or production migration.')
 c['artifact_digest']=hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest();dump(directory/'candidate.json',c)
 # Diagnostic only: source pixels unchanged; uniform nearest display.
 board=Image.new('RGB',(960,600),(36,49,54));draw=ImageDraw.Draw(board)
 for i,f in enumerate(frames):
  draw.text((i*240+10,10),f['phase'],fill='white')
  for theme,bg in enumerate([(229,216,189),(36,49,54)]):
   draw.rectangle((i*240,35+theme*280,(i+1)*240-1,310+theme*280),fill=bg)
   im=Image.open(directory/f['file']).convert('RGBA');s=138/1164;im=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.NEAREST);board.paste(im,(i*240+25,50+theme*280),im)
 board.save(directory/'static-review.png')
 (directory/'README.md').write_text(f'# {combo} 浇水四姿态候选\n\nready/raise/pour/recovery，固定穿衣完整GPT帧；1000ms。候选 [candidate.json](candidate.json)，[1×明暗诊断板](static-review.png)，[实际点位](measurements.json)。未获用户认可、未证明独立可组合、精确握点/脚接触或生产迁移；原生由主代理独立收证。\n')
 print(combo,sha(directory/'candidate.json'),c['canvas_px'],sum(f['duration_ms'] for f in frames))
 return c
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('combo');args=parser.parse_args();build(args.combo)
