from pathlib import Path
from PIL import Image
import json,hashlib,shutil
r=Path(__file__).resolve().parents[5];base=r/'art/design/character-bodies/adult-standard-v1';out=base/'registration';im=Image.open(base/'source.png')
roots={'south':[230,707],'west':[251,708],'east':[268,708],'north':[282,708]}
# All coordinates observed on the approved four-column master, local to its cell.
landmarks={
 'south':{'neck':[230,376],'shoulders':[[155,390],[305,390]],'wrists':[[108,510],[349,510]],'waist':[230,531],'hips':[230,566],'knees':[[190,626],[270,626]],'ankles':[[187,663],[273,663]],'foot_direction':'front'},
 'west':{'neck':[267,371],'shoulders':[[231,394],[319,408]],'wrists':[[314,518]],'waist':[251,531],'hips':[264,566],'knees':[[229,628],[286,628]],'ankles':[[229,663],[285,663]],'foot_direction':'left'},
 'east':{'neck':[250,371],'shoulders':[[198,408],[286,394]],'wrists':[[199,518]],'waist':[268,531],'hips':[253,566],'knees':[[230,628],[288,628]],'ankles':[[231,663],[287,663]],'foot_direction':'right'},
 'north':{'neck':[283,370],'shoulders':[[208,389],[358,389]],'wrists':[[164,511],[402,511]],'waist':[283,531],'hips':[282,567],'knees':[[244,626],[321,626]],'ankles':[[243,663],[324,663]],'foot_direction':'back'}}
frames={};output=r/'godot2d/assets/characters/adult-standard-v1';output.mkdir(parents=True,exist_ok=True)
for i,d in enumerate(roots):
 frame=im.crop((i*512,0,(i+1)*512,768));p=out/(d+'.png');frame.save(p); assert frame.tobytes()==Image.open(p).tobytes()
 shutil.copy2(p,output/(d+'.png'))
 frames[d]={'source_box':[i*512,0,(i+1)*512,768],'canvas':[512,768],'root_anchor':roots[d],'whole_frame_transform':{'translation':[0,0],'scale':1.0},'landmarks':landmarks[d],'landmark_precision':'manually observed source coordinates, approx +/-4 px; hidden far limbs not invented','texture_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
meta={'template_id':'adult-standard-v1','version':1,'pose':'standing_0','source_sha256':hashlib.sha256((base/'source.png').read_bytes()).hexdigest(),'registration':'whole equal-column crop only; no alpha/RGB modifications, no local transform','alpha_policy':'preserved approved source RGBA; 0..254 is not itself an error; accepted only as standing-head proof input after native light/dark inspection','world_scale':34.5/582,'frames':frames,'review_status':{'selected':True,'registered':True,'native_alpha_inspected':True,'geometry_checked':'exact crop bytes, no visual redraw','swap_checked':False,'user_accepted_components':False}}
meta['display_calibration']={'reference': 'player-unified-v4/walk_south_0.png alpha bbox height230; actual scene sprite scale .15 and camera4', 'world_body_height': 34.5, 'camera_zoom': 4, 'screen_body_height': 138, 'source_body_height': 582, 'notes': 'uniform scale for every direction; no per-part or per-direction rescale'}
(out/'registration.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')

print('REGISTERED_4_EXACT_RGBA_CROPS')
