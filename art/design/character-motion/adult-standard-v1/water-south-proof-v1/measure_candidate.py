"""Visible outline and point diagnostics; not a skeletal, grip or rigidity acceptance test."""
from pathlib import Path
import hashlib,json,math
from PIL import Image
ROOT=Path(__file__).resolve().parent
def dist(a,b):return math.dist(a,b)
def main():
 cfg=json.loads((ROOT/'registration-config.json').read_text());scale=cfg['display_scale']
 ref=Image.open(ROOT/'references/approved-idle-south.png').convert('RGBA')
 ref_head=ref.getchannel('A').point(lambda x:255 if x>=128 else 0).crop((0,0,512,367)).getbbox()
 ref_size=[ref_head[2]-ref_head[0],ref_head[3]-ref_head[1]]
 rows=[];registered=[]
 for f in cfg['frames']:
  im=Image.open(ROOT/f['source']).convert('RGBA');bbox=im.getchannel('A').point(lambda x:255 if x>=128 else 0).getbbox();head=f['manual_head_bbox_px'];hs=[head[2]-head[0],head[3]-head[1]]
  dx,dy=[a-b for a,b in zip(cfg['root_anchor_px'],f['source_root_px'])]
  foot={k:[v[0]+dx,v[1]+dy] for k,v in f['visible_foot_points_source_px'].items()};registered.append(foot)
  t=f['tool_source_px'];m=f['landmarks_source_px']
  rows.append(dict(source=f['source'],source_sha256=hashlib.sha256((ROOT/f['source']).read_bytes()).hexdigest(),source_canvas_px=list(im.size),alpha_range=im.getchannel('A').getextrema(),visible_alpha_bbox_ge128=bbox,manual_head_bbox_px=head,head_width_height_px=hs,head_vs_2x_reference_percent=[round((hs[i]/(ref_size[i]*2)-1)*100,3) for i in range(2)],projected_crown_to_observed_root_px=f['source_root_px'][1]-m['head_crown'][1],projected_crown_to_chin_px=m['chin'][1]-m['head_crown'][1],shirt_hem_note='Only visible lateral hem surface measured; center hidden by can, no false full torso segment comparison.',foot_source_px=f['visible_foot_points_source_px'],foot_registered_px=foot,tool_source_px=t,tool_projected_metrics_px=dict(rose_to_top_contact=dist(t['rose'],t['top_handle_contact']),rose_to_side_contact=dist(t['rose'],t['side_handle_contact']),barrel_center_axis=dist(t['barrel_top_center'],t['barrel_bottom_center'])),grip_note='Visible hand/handle crossing points manually observed; exact finger contact occluded. Hand centroid distance is not grip error.',hidden_joint_status='hip/knee/ankle null; no anatomical percentage estimate'))
 feet={k:dict(delta_source_px=[registered[1][k][i]-registered[0][k][i] for i in range(2)],euclidean_screen_px=dist(registered[0][k],registered[1][k])*scale) for k in registered[0]}
 result=dict(schema_version=1,status='diagnostic_only_no_geometry_acceptance',method='Manual visible outlines/surfaces ±8 source px each; differences propagate uncertainty. Direction front; no hidden joints inferred. Whole-frame density 2x declared from source canvas, never fitted to total height.',reference=dict(path='references/approved-idle-south.png',canvas_px=list(ref.size),head_bbox_px=ref_head,head_size_px=ref_size,root_y=708,root_to_crown_px=584,sole_y=710),canvas_density_contract=dict(source_canvas_px=[1024,1536],source_density_scale=2,display_scale=scale,registered_canvas_px=cfg['canvas_px'],registered_canvas_screen_px=[v*scale for v in cfg['canvas_px']]),frames=rows,relative_foot_after_whole_frame_registration=feet,projected_crown_to_root_spread_screen_px=abs(rows[1]['projected_crown_to_observed_root_px']-rows[0]['projected_crown_to_observed_root_px'])*scale,support_conclusion='Sole midpoint defines diagnostic root: any equality implied by registration is not passed foot contact. No approved south watering target trajectory exists.',tool_conclusion='Frontward tilting changes projection; these 2D lengths do not prove or disprove 3D rigidity. Exact grip is not frozen.',acceptance=dict(structure='tested separately',geometry=False,foot_contact=False,tool_rigidity=False,exact_grip=False,full_sequence=False,clothing_layers=False,user_accepted=False,gameplay=False))
 (ROOT/'measurements.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print('projected crown-root spread screen px',result['projected_crown_to_root_spread_screen_px'])
 print('head differences %',[r['head_vs_2x_reference_percent'] for r in rows])
 print('toe deltas screen px',{k:round(v['euclidean_screen_px'],3) for k,v in feet.items()})
if __name__=='__main__':main()
