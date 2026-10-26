"""Measure source alpha shoe soles inside manually selected visible shoe ROIs.
No source pixels, body scales, or world roots are modified.
"""
from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parent
ROIS={
 'ready':{'left':[240,1250,525,1450],'right':[600,1250,860,1450]},
 'reach':{'left':[180,1230,510,1440],'right':[620,1230,900,1440]},
 'pluck':{'left':[240,1250,550,1460],'right':[600,1250,880,1460]},
 'recovery':{'left':[250,1260,550,1490],'right':[560,1260,820,1490]}}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def soles(path,rois):
 im=Image.open(path).convert('RGBA');alpha=im.getchannel('A');points={}
 for side,roi in rois.items():
  mask=alpha.crop(tuple(roi)).point(lambda a:255 if a>=128 else 0);bbox=mask.getbbox()
  if bbox is None:raise ValueError('shoe ROI empty')
  y=roi[1]+bbox[3]-1;xs=[x for x in range(roi[0],roi[2]) if alpha.getpixel((x,y))>=128]
  if not xs:raise ValueError('sole row empty')
  points[side]=dict(manual_shoe_roi_px=roi,sole_row_endpoints_px=[[min(xs),y],[max(xs),y]],visible_sole_center_px=[round((min(xs)+max(xs))/2),y])
 return dict(source_canvas_px=list(im.size),alpha_range=im.getchannel('A').getextrema(),visible_alpha_bbox_ge128=alpha.point(lambda a:255 if a>=128 else 0).getbbox(),shoes=points)
def main():
 records=[]
 for phase,roi in ROIS.items():
  source=ROOT/'sources'/f'{phase}.png';reference=ROOT/'references'/f'pose-A-{phase}.png'
  b=soles(source,roi);a=soles(reference,roi)
  if b['source_canvas_px']!=[1024,1536]:raise ValueError('wrong source density canvas')
  if b['alpha_range'][0]!=0:raise ValueError('no transparent negative space')
  delta={side:[b['shoes'][side]['visible_sole_center_px'][i]-a['shoes'][side]['visible_sole_center_px'][i] for i in range(2)] for side in ['left','right']}
  l=b['shoes']['left']['visible_sole_center_px'];r=b['shoes']['right']['visible_sole_center_px']
  records.append(dict(phase=phase,source='sources/'+source.name,sha256=sha(source),B_measurements=b,A_reference_measurements=a,sole_center_delta_B_minus_A_px=delta,visible_shoe_reference_midpoint_px=[round((l[0]+r[0])/2),max(l[1],r[1])],world_root_status='not assigned; main agent registers shared harvest canvas/root',hidden_hip_knee_ankle_joints_px=None))
  print(phase,b['shoes'],delta)
 result=dict(schema_version=1,direction='north',garment='B',method='Manual shoe ROI selection on viewed complete A/B images, actual alpha>=128 lowest visible shoe row. Anatomical left=image left in back view. No body-height percentage, no per-shoe movement/scaling, and different soles retain their real y.',frames=records,scope='Source-only measurement. No skeleton, <=1screenpx support/grip acceptance, native rendering, modular clothing compatibility or user approval.')
 (ROOT/'manual-foot-measurements.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
