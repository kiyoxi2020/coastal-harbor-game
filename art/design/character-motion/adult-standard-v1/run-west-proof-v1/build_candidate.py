"""Register whole GPT frames for authoring review, never a modular release."""
from pathlib import Path
import hashlib
import json
from PIL import Image

ROOT = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def register_frame(frame, offset):
    if frame.size != (512, 768) or len(offset) != 2 or any(type(v) is not int for v in offset):
        raise ValueError('512x768 frame and integer offset required')
    dx, dy = offset
    # Only alpha=1 disconnected border residue was observed in the GPT v2.
    alpha = frame.getchannel('A').point(lambda a: 255 if a > 1 else 0)
    box = alpha.getbbox()
    if box and (box[0] + dx < 0 or box[1] + dy < 0 or box[2] + dx > 512 or box[3] + dy > 768):
        raise ValueError('whole-frame translation would crop source alpha')
    out = Image.new('RGBA', frame.size)
    out.paste(frame, (dx, dy))
    return out

def build():
    registration = json.loads((ROOT / 'registration-config.json').read_text())
    source_path = ROOT / registration['source']
    source = Image.open(source_path).convert('RGBA')
    if source.size != (2048, 768):
        raise ValueError('four exact 512x768 cells required')
    (ROOT / 'registered').mkdir(exist_ok=True)
    frames = []
    inputs = {str(p.relative_to(ROOT)): sha(p) for p in [source_path, ROOT / 'registration-config.json', Path(__file__)]}
    for index, offset in enumerate(registration['whole_frame_translations_px']):
        frame = source.crop((index * 512, 0, (index + 1) * 512, 768))
        out = register_frame(frame, offset)
        cropped_noise = sum(frame.getchannel('A').histogram()[1:]) - sum(out.getchannel('A').histogram()[1:])
        path = ROOT / f'registered/run_west_{index}.png'
        out.save(path)
        inputs[str(path.relative_to(ROOT))] = sha(path)
        frames.append({'pose_id': f'run_west_{index}', 'file': str(path.relative_to(ROOT)), 'duration_ms': 80,
                       'source_box': [index * 512, 0, (index + 1) * 512, 768], 'whole_frame_translation_px': offset,
                       'cropped_border_alpha_one_pixels': cropped_noise,
                       'visible_alpha_bbox': out.getchannel('A').point(lambda a: 255 if a >= 128 else 0).getbbox()})
    walk = json.loads((ROOT.parent / 'locomotion-v1/baked/export-manifest.json').read_text())
    data = {'template_id': 'adult-standard-v1', 'motion_set_id': 'run-west-proof-v1',
            'status': 'unapproved_complete_frame_proof', 'canvas_px': [512, 768], 'root_anchor_px': [256, 708],
            'display_scale': 138 / 582, 'base_world_speed': 108, 'playback_rate': .75,
            'phase_map': [0, 1, 2, 3], 'phase_map_status': 'candidate observations, not frozen contact events',
            'walk_artifact_digest': walk['artifact_digest'], 'frames': frames, 'inputs': inputs,
            'scope': 'complete GPT frame motion proof; no garment/body decomposition or release compatibility claimed'}
    (ROOT / 'candidate.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print('Registered complete-frame run proof:', sha(ROOT / 'candidate.json'))

if __name__ == '__main__': build()
