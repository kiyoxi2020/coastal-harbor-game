"""Authoring diagnostics; rejected north B never enters the playable manifest."""
from pathlib import Path
from collections import deque,Counter
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def holes(im):
    a=im.getchannel('A');seen=set();q=deque([(0,0)])
    while q:
        x,y=q.popleft()
        if not(0<=x<512 and 0<=y<768) or (x,y) in seen or a.getpixel((x,y))>=128:continue
        seen.add((x,y));q.extend([(x-1,y),(x+1,y),(x,y-1),(x,y+1)])
    return [(x,y) for y in range(335,550) for x in range(55,455) if a.getpixel((x,y))<128 and (x,y) not in seen]
def main():
    records=[]
    for i in range(4):
        p=ROOT/f'baked/B_north_{i}.png';im=Image.open(p).convert('RGBA');points=holes(im)
        records.append({'pose_id':f'run_north_{i}','file':str(p.relative_to(ROOT)),'sha256':sha(p),'enclosed_alpha_below_128_pixels':len(points),'fully_transparent_pixels':sum(im.getpixel(p)[3]==0 for p in points),'points_px':points,'result':'rework_required' if points else 'geometry_check_only'})
    report={'method':'4-neighbor flood from canvas exterior at alpha<128; report closed garment-band pockets y335:550 x55:455; original PNG alpha unchanged','records':records,'north_B_status':'rework_required_not_enabled','south_B_status':'rejected_source_pose_drift_v1_v2','active_B_directions':['west','east'],'diagnostic_points':[{'pose':'run_north_0','point':[306,495],'A_RGBA':[53,47,35,253],'A_owner':'torso_A','B_source_RGBA':[91,80,60,253],'B_result_alpha':0,'cause':'A waist brown/dark edge incorrectly included by cloth edge adjacency; B cloth classifier excludes actual brown; original pants surface must remain body owner, not fill paint'},{'pose':'run_north_1','point':[217,347],'A_RGBA':[9,5,3,253],'A_owner':'torso_A','B_source_RGBA':[89,67,54,253],'B_result_alpha':0,'cause':'A neck dark contour at same cloth/skin boundary removed; B source neck contour differs; source ownership/neck contour requires explicit registration'},{'pose':'run_north_3','point':[331,433],'B_source_RGBA':[30,45,64,119],'complete_torso_RGBA':[3,4,7,252],'cause':'B underarm source alpha below128 while torso source has opaque actual cloth; current occlusion based on A arm projection prevents surfacing; hidden-source presence is not proof that changing mask would be spatially valid'}],'scope':'diagnostic authoring only; no mask expansion, patch pixels, scale, relocation, or fake native/user acceptance'}
    (ROOT/'evidence/garment-quality.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({r['pose_id']:r['enclosed_alpha_below_128_pixels'] for r in records}))
if __name__=='__main__':main()
