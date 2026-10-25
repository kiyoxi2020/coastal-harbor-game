"""Exact crop and integer whole-frame registration; never redraw or resize art."""
from pathlib import Path
import hashlib
import json
from PIL import Image

ROOT = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def build():
    cfg = json.loads((ROOT / 'registration-config.json').read_text())
    source = ROOT / cfg['source']
    im = Image.open(source).convert('RGBA')
    if list(im.size) != cfg['source_size_px']:
        raise ValueError('Source dimensions changed')
    records = []
    for i, spec in enumerate(cfg['frames']):
        frame = im.crop(spec['source_box_px'])
        dx, dy = spec['whole_frame_translation_px']
        if type(dx) is not int or type(dy) is not int:
            raise ValueError('Only integer whole-frame registration is permitted')
        alpha = frame.getchannel('A')
        box = alpha.point(lambda a: 255 if a >= 16 else 0).getbbox()
        if not box or box[0] + dx < 0 or box[1] + dy < 0 or box[2] + dx > cfg['canvas_px'][0] or box[3] + dy > cfg['canvas_px'][1]:
            raise ValueError(f'Visible artwork would be cropped in frame {i}')
        registered = Image.new('RGBA', tuple(cfg['canvas_px']))
        registered.paste(frame, (dx, dy))
        path = ROOT / f'registered/water_west_{i}.png'
        registered.save(path)
        records.append({'pose_id': f'water_west_{i}', 'file': str(path.relative_to(ROOT)),
                        'duration_ms': cfg['durations_ms'][i],
                        'source_box_px': spec['source_box_px'], 'whole_frame_translation_px': [dx, dy],
                        'visible_alpha_bbox': registered.getchannel('A').point(lambda a: 255 if a >= 128 else 0).getbbox(),
                        'sha256': sha(path)})
    inputs = {str(p.relative_to(ROOT)): sha(p) for p in [source, ROOT / 'registration-config.json', ROOT / 'poses.json', Path(__file__)]}
    data = {'schema_version': 1, 'template_id': 'adult-standard-v1', 'motion_set_id': 'water-west-proof-v1',
            'action_id': 'water', 'direction': 'west', 'status': 'unapproved_complete_frame_candidate',
            'canvas_px': cfg['canvas_px'], 'root_anchor_px': cfg['root_anchor_px'], 'display_scale': 138 / 582,
            'loop': False, 'review_repeat': True, 'move_policy': 'stationary_locked_candidate',
            'source_pixel_density_status': cfg['source_pixel_density_status'],
            'frames': records, 'inputs': inputs,
            'scope': 'Complete GPT raster frames only; no modular garments, gameplay transactions or release acceptance.'}
    digest_input = json.dumps(data, sort_keys=True, separators=(',', ':')).encode()
    data['artifact_digest'] = hashlib.sha256(digest_input).hexdigest()
    (ROOT / 'candidate.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(data['artifact_digest'])

if __name__ == '__main__':
    build()
