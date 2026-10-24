#!/usr/bin/env python3
"""Create diagnostic rectangles only. This fixture is deliberately not artwork."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw
from compose import compose


def make_fixture(destination):
    root = Path(destination).resolve()
    if not str(root).startswith('/private/tmp/coastal-'):
        raise ValueError('fixture destination must be /private/tmp/coastal-*')
    root.mkdir(parents=True, exist_ok=True)
    for name, color in [('base', (220, 130, 60, 255)), ('A', (30, 110, 220, 255)), ('B', (180, 70, 130, 255))]:
        image = Image.new('RGBA', (120, 240), color)
        image.save(root / f'{name}.png')
    mask = Image.new('L', (512, 768))
    ImageDraw.Draw(mask).rectangle((240, 400, 290, 450), fill=255)
    mask.save(root / 'mask.png')
    Image.new('RGBA', (40, 40), (250, 220, 80, 255)).save(root / 'front.png')
    data = {'schema_version': 1, 'canvas_px': [512, 768], 'root_anchor_px': [256, 708], 'display_scale': .2371134,
            'frames': [{'pose_id': f'walk_w_{i}', 'duration_ms': t} for i, t in enumerate([140, 180, 140, 180])], 'recipes': {}}
    for recipe in ('A', 'B'):
        data['recipes'][recipe] = {'frames': [{'layers': [
            {'id': 'target', 'source': 'base.png', 'offset_px': [196, 468 - i * 8], 'hide_mask': 'mask.png'},
            {'id': 'garment', 'source': f'{recipe}.png', 'offset_px': [196 + i * 10, 300]},
            {'id': 'front', 'source': 'front.png', 'offset_px': [240, 400]},
        ]} for i in range(4)]}
    motion = root / 'motion.json'
    motion.write_text(json.dumps(data, indent=2) + '\n')
    compose(motion)
    return root / 'baked/export-manifest.json'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='/private/tmp/coastal-motion-tools-fixture')
    print(make_fixture(parser.parse_args().output))
