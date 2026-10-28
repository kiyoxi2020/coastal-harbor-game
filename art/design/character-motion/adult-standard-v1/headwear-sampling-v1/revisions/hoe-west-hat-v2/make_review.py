"""Offline common-root preview of baked assets; not native GPU evidence."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

P = Path(__file__).resolve().parent
HEAD = P.parents[1]


def render(sample_path, frame, state, zoom=2):
    sample = json.loads(sample_path.read_text())
    image = Image.open(sample_path.parent / frame['states'][state]['file']).convert('RGBA')
    scale = frame.get('display_scale', sample['display_scale']) * zoom
    root = frame.get('root_anchor_px', sample['root_anchor_px'])
    image = image.resize(tuple(round(v * scale) for v in image.size), Image.Resampling.NEAREST)
    canvas = Image.new('RGBA', (420, 460), '#e1e6e8')
    canvas.alpha_composite(image, (210-round(root[0]*scale), 420-round(root[1]*scale)))
    ImageDraw.Draw(canvas).text((8, 8), frame['pose_id'], fill='black')
    return canvas


def main():
    paths = [HEAD/'hoe-west/sample.json', P/'sample-build/sample.json']
    sheet = Image.new('RGB', (2100, 920), '#e1e6e8')
    for row, path in enumerate(paths):
        sample = json.loads(path.read_text())
        for index, frame in enumerate([sample['idle']] + sample['frames']):
            tile = render(path, frame, 'hair_hat')
            ImageDraw.Draw(tile).text((8, 26), 'BEFORE' if row == 0 else 'AFTER / offline asset preview', fill='black')
            sheet.paste(tile, (420*index, 460*row))
    sheet.save(P/'before-after-common-root.png')
    path=paths[1];sample=json.loads(path.read_text())
    frames=[render(path, frame, 'hair_hat') for frame in sample['frames']]
    frames[0].save(P/'hoe-hair-hat-offline.gif', save_all=True, append_images=frames[1:],
                   duration=[f['duration_ms'] for f in sample['frames']], loop=0, disposal=2)
    print('Offline preview saved; native validation still required.')


if __name__ == '__main__':
    main()
