"""Exact whole-frame source registration; never draw/resize body or tool pixels."""
from pathlib import Path
import hashlib
import json
from PIL import Image
from PIL import ImageFilter, ImageChops
from collections import deque

ROOT = Path(__file__).resolve().parent
FRAME_COUNT = 4
CANVAS = (768, 768)
ROOT_PX = (384, 708)
DURATIONS_MS = [230, 120, 230, 320]
PHASES = ['raised_apex', 'downswing', 'contact', 'recovery']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def build():
    source = ROOT / 'sources/hoe-west-v3.png'
    im = Image.open(source).convert('RGBA')
    assert im.size == (2048, 768), f'Unreviewed source canvas {im.size}; no automatic resampling allowed'
    frames = []
    sheet = Image.new('RGBA', (CANVAS[0] * FRAME_COUNT, CANVAS[1]))
    for index, phase in enumerate(PHASES):
        # GPT's blade crosses a nominal 512px cell edge by about 10px.
        # Padded crop + reviewed complete connected subject preserves that blade
        # and excludes only unrelated neighbor fragments/background alpha noise.
        crop = [max(0, 512 * index - 24), 0, min(2048, 512 * (index + 1) + 24), 768]
        cut = im.crop(crop)
        alpha = cut.getchannel('A')
        core = alpha.point(lambda a: 255 if a >= 128 else 0)
        px = core.load()
        components = []
        for y in range(cut.height):
            for x in range(cut.width):
                if not px[x, y]:
                    continue
                queue = deque([(x, y)])
                points = []
                px[x, y] = 0
                while queue:
                    xx, yy = queue.popleft()
                    points.append((xx, yy))
                    for nx, ny in [(xx-1, yy), (xx+1, yy), (xx, yy-1), (xx, yy+1)]:
                        if 0 <= nx < cut.width and 0 <= ny < cut.height and px[nx, ny]:
                            px[nx, ny] = 0
                            queue.append((nx, ny))
                components.append(points)
        main = max(components, key=len)
        assert len(main) > 90000
        mask = Image.new('L', cut.size)
        for point in main:
            mask.putpixel(point, 255)
        mask = mask.filter(ImageFilter.MaxFilter(5))
        cut.putalpha(ImageChops.multiply(alpha, mask))
        dx, dy = 36 + crop[0] - 512 * index, 8
        frame = Image.new('RGBA', CANVAS)
        frame.paste(cut, (dx, dy))
        output = ROOT / f'registered/hoe_west_{index}.png'
        frame.save(output)
        sheet.paste(frame, (CANVAS[0] * index, 0))
        frames.append({'pose_id': f'hoe_west_{index}', 'phase': phase,
                       'source': 'sources/hoe-west-v3.png', 'source_sha256': sha(source),
                       'source_rect_px': crop, 'whole_frame_translation_from_nominal_cell_px': [36, 8],
                       'background_extraction': {'method': 'reviewed complete person+tool connected alpha>=128 component + 2px original-alpha fringe', 'retained_component_pixels': len(main), 'discarded_disconnected_opaque_pixels': sum(map(len, components))-len(main)},
                       'scale': 1, 'output': str(output.relative_to(ROOT)),
                       'sha256': sha(output), 'alpha_bbox_px': frame.getchannel('A').getbbox(),
                       'duration_ms': DURATIONS_MS[index]})
    sheet.save(ROOT / 'registered/hoe-west-a-sheet.png')
    manifest = {'schema_version': 1, 'template_id': 'adult-standard-v1',
                'motion_set_id': 'hoe-west-proof-v1', 'action_id': 'hoe', 'direction': 'west',
                'status': 'rework_required', 'user_accepted': False,
                'canvas_px': CANVAS, 'root_anchor_px': ROOT_PX,
                'display_scale': 138 / 582, 'nominal_standing_character_display_height_px': 138,
                'density_check': 'failed: source standing height about566px vs582px reference; head about207px vs236px reference; no resampling performed',
                'canvas_expansion_reason': 'tool extends left of nominal512px cells; preserve complete tool with padded source crops and expand all frames to768x768 root384,708',
                'cycle_duration_ms': sum(DURATIONS_MS),
                'move_policy': 'stationary proof; no gameplay execution',
                'event': {'id': 'visual_contact_only', 'frame_index': 2,
                          'time_ms': sum(DURATIONS_MS[:2]), 'gameplay_transaction': False},
                'registration_script_sha256': sha(Path(__file__)), 'frames': frames}
    (ROOT / 'registered/registration.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'frames': len(frames), 'canvas': CANVAS, 'source_sha256': sha(source)}))

if __name__ == '__main__':
    build()
