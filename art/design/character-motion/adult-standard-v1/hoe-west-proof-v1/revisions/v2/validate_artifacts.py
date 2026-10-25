"""Check actual source fidelity/structure and report marked geometry honestly."""
from pathlib import Path
import hashlib,json,math
from PIL import Image

ROOT=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def build():
    m=json.loads((ROOT/'registered/registration.json').read_text())
    source=Image.open(ROOT/m['frames'][0]['source']).convert('RGBA')
    frames=[]
    for f in m['frames']:
        im=Image.open(ROOT/f['output']).convert('RGBA')
        expected=Image.new('RGBA',(512,768));expected.paste(source.crop(f['source_rect_px']),tuple(f['whole_frame_translation_px']))
        bbox=im.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox()
        frames.append({'pose_id':f['pose_id'],'canvas_size_correct':im.size==(512,768),'source_rgba_exact':im.tobytes()==expected.tobytes(),'sha256_matches':sha(ROOT/f['output'])==f['sha256'],'opaque_bbox_px':bbox,'opaque_canvas_edges_clear':bool(bbox and bbox[0]>0 and bbox[1]>0 and bbox[2]<512 and bbox[3]<768)})
    report={'status':'rejected','scope':'structure and supplied manual geometry; no native/user/dynamic wardrobe acceptance','source_size_px':source.size,'frames':frames,'distinct_frames':len(set(f['sha256'] for f in m['frames'])),'timeline_ms':sum(f['duration_ms'] for f in m['frames']),'native_checked':False,'user_accepted':False,'geometry_checked':False,'motion_checked':False,'dynamic_swap_checked':False}
    if (ROOT/'poses.json').exists():
        p=json.loads((ROOT/'poses.json').read_text());results=[]
        for pose in p['poses']:
            a=pose.get('shaft_collar');b=pose.get('shaft_butt')
            item={'pose_id':pose['pose_id'],'endpoint_uncertainty_px':pose.get('endpoint_uncertainty_px')}
            if a is None or b is None:
                item.update({'shaft_length_px':None,'rigidity':'unverified; endpoint hidden or ambiguous'})
            else:
                length=math.dist(a,b);item.update({'shaft_length_px':round(length,2),'deviation_from300_px':round(length-300,2)})
                grips=[]
                for name,g in pose.get('grip_crossings',{}).items():
                    vx,vy=b[0]-a[0],b[1]-a[1];wx,wy=g[0]-a[0],g[1]-a[1]
                    grips.append({'name':name,'distance_to_centerline_px':round(abs(vx*wy-vy*wx)/length,2),'normalized_shaft_position':round((vx*wx+vy*wy)/(length*length),4)})
                item['observed_grip_geometry']=grips
            results.append(item)
        report['manual_geometry_metrics']=results
        report['manual_geometry_does_not_prove_1screenpx_target']=True
    (ROOT/'evidence/validation.json').write_text(json.dumps(report,indent=2)+'\n')
    assert all(f['canvas_size_correct'] and f['source_rgba_exact'] and f['sha256_matches'] for f in frames)
    assert report['distinct_frames']==4
    print(json.dumps({'frames':len(frames),'source_rgba_exact':True,'opaque_edges_clear':[f['opaque_canvas_edges_clear'] for f in frames],'native_checked':False}))

if __name__=='__main__':build()
