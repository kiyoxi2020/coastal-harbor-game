"""Register the v5 complete frames, without modifying any part's shape or scale."""
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'sources/walk-a-v5.png'
# Observed hip x positions: 234,255,254,263; the common hip is x264.
# Root remains 8 source pixels to the left of that reference hip.
OFFSETS = [30, 9, 10, 1]


def build():
    source = Image.open(SOURCE).convert('RGBA')
    assert source.size == (2048, 768)
    output = ROOT / 'registered/v5'
    output.mkdir(parents=True, exist_ok=True)
    records = []
    sheet = Image.new('RGBA', (2048, 768))
    for index, dx in enumerate(OFFSETS):
        frame = source.crop((index * 512, 0, (index + 1) * 512, 768))
        # Lossless paste of the whole registered frame, never an alpha blend.
        clipped = frame.getchannel('A').crop((512 - dx, 0, 512, 768))
        # The GPT source has isolated alpha=1 background residue at two borders.
        # No visible silhouette may be clipped; preserve original source unchanged.
        assert clipped.getextrema()[1] <= 1, 'visible source would be cropped'
        registered = Image.new('RGBA', (512, 768))
        registered.paste(frame, (dx, 0))
        path = output / f'walk_w_{index}.png'
        registered.save(path)
        sheet.paste(registered, (index * 512, 0))
        records.append({'pose_id': f'walk_w_{index}',
                        'source_box': [index * 512, 0, (index + 1) * 512, 768],
                        'source_root_anchor_px': [256 - dx, 708],
                        'source_hip_landmark_px': [264 - dx, 565],
                        'translation_px': [dx, 0], 'scale': 1,
                        'clipped_background_pixels': sum(clipped.histogram()[1:]),
                        'clipped_alpha_max': clipped.getextrema()[1],
                        'file': str(path.relative_to(ROOT)),
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    sheet.save(output / 'sheet.png')
    record = {'status': 'registered_not_motion_accepted',
              'source': str(SOURCE.relative_to(ROOT)),
              'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'canvas_px': [512, 768], 'root_anchor_px': [256, 708],
              'landmark_precision': 'manually observed hip/whole-character shift, approx +/-4 source px',
              'operation': 'whole-frame integer translation only; visible RGBA preserved; only recorded alpha<=1 border residue cropped; no part transform',
              'frames': records}
    (output / 'registration.json').write_text(json.dumps(record, indent=2) + '\n')
    print('Registered four whole frames; motion/garment acceptance remains separate.')


if __name__ == '__main__':
    build()
