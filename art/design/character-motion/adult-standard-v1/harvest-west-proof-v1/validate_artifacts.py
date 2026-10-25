"""Verify real source-pixel preservation, not anatomy/motion acceptance."""
from pathlib import Path
import json
from PIL import Image

ROOT = Path(__file__).resolve().parent

def validate():
    manifest = json.loads((ROOT/'registered/registration.json').read_text())
    source = Image.open(ROOT/manifest['frames'][0]['source']).convert('RGBA')
    assert source.size == (2048,768)
    results=[]
    for frame in manifest['frames']:
        image=Image.open(ROOT/frame['output']).convert('RGBA')
        assert image.size==(512,768)
        crop=source.crop(frame['source_rect_px'])
        expected=Image.new('RGBA',(512,768))
        expected.paste(crop,tuple(frame['whole_frame_translation_px']))
        assert image.tobytes()==expected.tobytes(), 'Frame changed source RGBA pixels'
        opaque=image.getchannel('A').point(lambda a:255 if a>=128 else 0)
        bbox=opaque.getbbox()
        assert bbox and bbox[0]>0 and bbox[1]>0 and bbox[2]<512 and bbox[3]<768, f'Possible source clipping: {bbox}'
        results.append({'pose_id':frame['pose_id'],'size_correct':True,'exact_source_rgba_preserved':True,'opaque_bbox_px':bbox,'opaque_canvas_edges_clear':True})
    assert len(set(f['sha256'] for f in manifest['frames']))==4
    assert sum(f['duration_ms'] for f in manifest['frames'])==1000
    result={'scope':'source integrity and structural checks only; does not prove density, grip or motion acceptance','source_size_px':source.size,'distinct_frames':4,'duration_ms':1000,'frames':results}
    (ROOT/'evidence/structure-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Verified 4 distinct 512x768 frames, exact source RGBA, clear opaque edges, 1000ms timeline.')

if __name__=='__main__':
    validate()
