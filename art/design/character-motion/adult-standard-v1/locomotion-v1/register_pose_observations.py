"""Record manual observations of registered source frames, never transforms art.
Hidden joints remain unknown: these observations are not a frozen rig contract.
"""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
# Anatomical left/right. Coordinates visually read from registered PNGs.
# Each tuple: left wrist, right wrist, left ankle, right ankle, left foot, right foot.
WALK={
'south':[
((365,505),(143,482),(295,652),(211,613),(296,707),(213,668)),
((341,484),(139,497),(300,650),(210,584),(300,706),(209,650)),
((343,484),(138,504),(289,616),(210,651),(290,671),(209,706)),
((366,501),(142,483),(299,583),(212,651),(299,649),(211,707))],
'north':[
((128,503),(365,473),(210,611),(302,644),(210,650),(303,715)),
((130,504),(357,481),(210,650),(304,605),(211,706),(306,667)),
((143,468),(368,503),(208,644),(306,611),(209,715),(306,650)),
((143,465),(367,502),(207,604),(302,651),(208,668),(305,706))],
'west':[
((348,505),(166,482),(184,655),(338,649),(155,708),(324,709)),
((319,511),(179,501),(244,664),(340,620),(225,710),(331,678)),
((257,505),(355,498),(350,646),(177,655),(341,710),(155,710)),
((328,511),(184,499),(352,620),(242,663),(344,679),(224,710))],
'east':[
((337,483),(158,505),(171,648),(333,661),(174,710),(355,711)),
((334,495),(181,511),(176,625),(260,664),(177,685),(278,711)),
((151,494),(273,496),(341,659),(158,647),(358,711),(170,711)),
((334,495),(183,511),(291,664),(173,625),(297,711),(173,685))]}
IDLE={
'south':((367,515),(136,514),(301,659),(208,660),(303,709),(207,709)),
'north':((136,515),(369,515),(208,661),(305,661),(208,709),(305,709)),
'west':((324,516),None,(280,661),(210,657),(263,709),(202,701)),
'east':(None,(197,516),(302,656),(224,663),(310,701),(251,709))}
NECK={'south':(256,378),'north':(256,369),'west':(250,377),'east':(264,381)}
SHOULDERS={'south':[(325,397),(185,397)],'north':[(185,395),(325,395)],'west':[(294,400),None],'east':[None,(225,400)]}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 records=[]
 for direction in WALK:
  for action,values in [('idle',[IDLE[direction]]),('walk',WALK[direction])]:
   for index,points in enumerate(values):
    pose=f'{action}_{direction}_{index}';source=ROOT/f'registered/{pose}.png'
    anchors={'neck_root':{'px':(250,378) if action=='walk' and direction=='east' else NECK[direction],'visibility':'visible','status':'manual_approximate'},'waist':{'px':[256,531 if action=='walk' and direction=='east' else 526 if action=='idle' or direction=='west' else 516],'visibility':'clothed_surface','status':'manual_approximate'}}
    for side,shoulder in zip(['left','right'],[None,(215,400)] if action=='walk' and direction=='east' else SHOULDERS[direction]):
     anchors[side+'_shoulder']={'px':shoulder,'visibility':'clothed_surface' if shoulder else 'occluded','status':'manual_approximate' if shoulder else 'unresolved'}
     for joint in ['elbow','hip','knee','tool_grip']:
      anchors[side+'_'+joint]={'px':None,'visibility':'not_frozen','status':'unresolved; must be registered before rig/tool/pants-shoes release'}
    for name,point in zip(['left_wrist','right_wrist','left_ankle','right_ankle','left_foot','right_foot'],points):
     anchors[name]={'px':point,'visibility':'visible_surface' if point else 'occluded','status':'manual_approximate' if point else 'unresolved'}
    contacts={'left':'planted','right':'planted'} if action=='idle' else ({'left':'support','right':'airborne'} if index==1 else {'left':'airborne','right':'support'} if index==3 else {'left':'transition','right':'transition'})
    if action=='walk' and direction=='east' and index in [1,3]:contacts={side:contacts['right' if side=='left' else 'left'] for side in ['left','right']}
    records.append({'pose_id':pose,'source':str(source.relative_to(ROOT)),'source_sha256':digest(source),'root_anchor_px':[256,708],'anchors':anchors,'foot_contact_observation':contacts,'contact_events':[],'near_side':{'west':'left','east':'right'}.get(direction,'pose_specific'),'phase_basis':'matching near-side profile trajectory; anatomical support differs west/east' if direction in ['west','east'] else 'anatomical alternating' ,'strict_screen_foot_error_px':None})
 (ROOT/'poses.json').write_text(json.dumps({'schema_version':2,'status':'draft observations; not a frozen rig or contact-event contract','method':'manual reading of actual registered PNGs; no total-height percentage, no art modification','precision':'approximate source pixels; <=1 screen pixel foot-lock NOT verified','frames':records},ensure_ascii=False,indent=2)+'\n')
 (ROOT/'template.json').write_text(json.dumps({'template_id':'adult-standard-v1','motion_set_id':'locomotion-v1','canvas_px':[512,768],'root_anchor_px':[256,708],'display_scale':138/582,'world_scale':138/582/4,'texture_filter':'nearest','placement':'full_frame; integer whole-frame registration only','supported_actions':['idle','walk'],'directions':['south','west','east','north'],'garments':['A','B'],'pants_shoes':'fixed olive pants and brown shoes, not independently interchangeable','release_status':'review candidate; full rig/contact freeze and five-action migration incomplete','speed_acceptance':'speed-acceptance.json'},ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
