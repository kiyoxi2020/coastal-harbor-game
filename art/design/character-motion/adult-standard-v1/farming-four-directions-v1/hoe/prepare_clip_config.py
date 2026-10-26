"""Serialize reviewed observations. No art transformations beyond registered full frames."""
from pathlib import Path
import json,sys,shutil
from author_observations import OBS
ROOT=Path(__file__).resolve().parent
DUR=[180,220,140,260];PHASES=['ready','lift','contact','recovery']
def make(direction,garment):
 root=ROOT/(direction+'-'+garment);frames=[]
 for i,phase in enumerate(PHASES):
  o=OBS[direction][phase]
  lm={k:None for k in ['hip_joint','near_knee_joint','far_knee_joint','near_ankle_joint','far_ankle_joint','far_shoulder_joint','far_elbow_joint']};lm.update(o['surface']);lm.update(head_crown=[(o['head'][0]+o['head'][2])//2,o['head'][1]],chin=[(o['head'][0]+o['head'][2])//2,o['head'][3]])
  if garment=='B':
   for name in list(lm):
    if name.endswith('_wrist'):lm[name]=None
   lm['near_cuff_surface']=None;lm['far_cuff_surface']=None
  frames.append(dict(source=o.get('source','sources/'+phase+'-attempt1.png')if garment=='A'else'sources/'+phase+'-attempt1.png',phase=phase,duration_ms=DUR[i],source_root_px=o['root'],head_bbox_px=o['head'],landmarks_px=lm,foot_points_px=o['feet'],tool_points_px=o['tool'],observation='Visible outline/skin/cloth boundary observation ±12sourcepx. '+('B pose inherits its A edit-target coordinate observations after visual alignment review; cloth cuff boundaries differ and hidden joints remain unknown.'if garment=='B'else'Independent true direction generation from approved directional identity; root from observed planted footprint.')))
  if garment=='B':shutil.copy2(ROOT/(direction+'-A')/o.get('source','sources/'+phase+'-attempt1.png'),root/'references'/(phase+'-A-edit-target.png'))
 cfg=dict(schema_version=1,template_id='adult-standard-v1',action_id='hoe',direction=direction,garment=garment,source_canvas_px=[1024,1536],canvas_px=[1536,1792],root_anchor_px=[768,1544],display_scale=138/1164,source_density_scale_vs_idle=2,manual_uncertainty_source_px=12,root_method='Observed near shoe heel offset for east; observed central planted footprint for south/north. Author root, not certified support trajectory.',frames=frames)
 (root/'registration-config.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
 p=dict(generator='built-in image_gen',exact_model_id='not returned',direction=direction,garment=garment,method='Independent direction from approved idle and complete same-direction READY variants'if garment=='A'else'GPT full-pose shirt-only editing of corresponding A complete sprite; fixed B outfit, not independent garment parts',no_mirroring=True,no_local_transformations=True,no_face_hand_pasting=True,source_format='1024x1536 original complete rasters, no upsampling',rejected_sheet='sources/rejected-sheet-low-density.png; actual1024x1536 instead of requested2048x3072, rejected and switched to single images'if direction=='east'and garment=='A'else None)
 (root/'provenance.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':make(sys.argv[1],sys.argv[2])
