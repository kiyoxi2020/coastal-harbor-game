"""Inspect actual source/output dimensions and registered native display footprint."""
from pathlib import Path
from PIL import Image
import hashlib,json
HERE=Path(__file__).resolve().parent
if __name__=='__main__':
 samples={}
 for name in ['run-east','hoe-west','water-south','harvest-north']:
  folder=HERE/name;path=folder/'sample.json';data=json.loads(path.read_text());records=[]
  for frame in data['frames']+[data['idle']]:
   scale=frame.get('display_scale',data['display_scale'])
   for state,item in frame['states'].items():
    with Image.open(folder/item['file']) as picture:
     bbox=picture.getchannel('A').getbbox();width=bbox[2]-bbox[0];height=bbox[3]-bbox[1]
     records.append({'pose_id':frame['pose_id'],'state':state,'file':item['file'],'output_canvas_px':list(picture.size),'visible_source_bbox_px':list(bbox),'world_native_visible_px':[round(width*scale,3),round(height*scale,3)],'review_panel_visible_px':[round(width*scale*2,3),round(height*scale*2,3)],'registered_whole_frame_display_scale':scale})
  sources={}
  for image in sorted((folder/'sources').glob('*.png')):
   with Image.open(image) as picture:sources[image.relative_to(folder).as_posix()]=list(picture.size)
  samples[name]={'sample_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'retained_source_dimensions_px':sources,'outputs':records}
 (HERE/'display-measurements.json').write_text(json.dumps({'scope':'Measured PNG alpha footprints and registered scale; not a visual quality or user acceptance claim. World native uses 1x; side panel 2x.','samples':samples},ensure_ascii=False,indent=2)+'\n')
 print('Measured source/output/native dimensions for 80 sampled states.')
