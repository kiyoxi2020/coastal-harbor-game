"""Apply reviewed far-underside boundary corrections without moving any registration.
The old cap silhouette is complete; black underside tips must travel with the actual
far underside rather than dangling in front of the original forehead/ear.
"""
from pathlib import Path
from PIL import Image
import json
import fit_probe as f
P=Path(__file__).resolve().parent
for i in range(4):
 pose=f.S['frames'][i]['pose_id'];D=P/pose;m=json.loads((D/'registration-probe.json').read_text());ox,oy=m['candidate_translation_px'];src,own,nm,fm=f.parts_motion(i)
 for name,im in [('source-full-frame.png',src),('source-ownership.png',own),('source-near-ownership.png',nm),('source-far-ownership.png',fm)]:im.save(D/name)
 f.js(D/'source-contours.json',{'pose_id':pose,'source_crop_px':f.R['motion'][i]['atlas_box_px'],'source_crop_canvas_px':list(src.size),'source_ownership':f.segments(own),'near_ownership':f.segments(nm),'far_ownership':f.segments(fm),'near_far_basis':f.seams[i],'reviewed_far_tip_correction':'Actual underside-black tips at left return and rear lobe belong far; continuous bright top/near lower black lip stays near. No near surface is relabelled to hide a body defect.','source_rgba_policy':'Unchanged actual source RGBA, frozen masks only.'})
 body=Image.open(D/'original-body.png').convert('RGBA');hair=Image.open(D/'full-original-hair.png').convert('RGBA')
 def reg(mask):
  out=Image.new('RGBA',body.size);part=Image.new('RGBA',src.size);part.paste(src,(0,0),mask);out.paste(part,(ox,oy));return out
 near=reg(nm);far=reg(fm);plate=reg(own)
 for name,im in [('hat-near.png',near),('hat-far.png',far),('hat-complete-plate.png',plate)]:im.save(D/name)
 for name,mask in [('registered-ownership.png',own),('near-ownership.png',nm),('far-ownership.png',fm)]:
  out=Image.new('L',body.size);out.paste(mask,(ox,oy));out.save(D/name)
 comp,_=f.standard.compose(body,near,far);both,_=f.standard.compose(body,near,far,hair);comp.save(D/'composite.png');both.save(D/'hair-hat-composite.png')
 print(pose,'frozen offset retained',[ox,oy])
