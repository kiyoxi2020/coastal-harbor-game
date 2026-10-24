"""Extract registered GPT pixels via reviewed ownership polygons; never draw anatomy."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parent
REGIONS = json.loads((ROOT / 'semantic-regions.json').read_text())
SIZE = (512, 768)


def polygon(points):
    mask = Image.new('L', SIZE)
    ImageDraw.Draw(mask).polygon([tuple(p) for p in points], fill=255)
    return mask


def cut(image, mask):
    result = image.copy()
    result.putalpha(ImageChops.multiply(image.getchannel('A'), mask))
    return result


def neck_skin(image):
    # Color only assists ownership INSIDE the manually reviewed neck/collar region.
    # It never classifies the face, hair, hands, or the whole source globally.
    mask = Image.new('L', SIZE)
    for y in range(365, 415):
        for x in range(190, 305):
            r, g, b, alpha = image.getpixel((x, y))
            if alpha and r > 100 and r - g > 35 and g - b > 25:
                mask.putpixel((x, y), 255)
    return mask


def ownership(index):
    near = polygon(REGIONS['near'][index])
    far = ImageChops.subtract(polygon(REGIONS['far'][index]), near)
    torso = ImageChops.subtract(polygon(REGIONS['torso']), ImageChops.lighter(near, far))
    torso = ImageChops.subtract(torso, neck_skin(source_frame('A', index)))
    union = ImageChops.lighter(ImageChops.lighter(near, far), torso)
    return {'base': ImageChops.invert(union), 'far': far, 'torso': torso, 'near': near}


def partition(image, index):
    return {key: cut(image, mask) for key, mask in ownership(index).items()}


def split_arm(arm, index, side, garment):
    hand = polygon(REGIONS[f'hands_{garment}_{side}'][index])
    # The hand polygon decides contour ownership. Inside the already reviewed
    # arm region, source palette distinguishes actual wrist skin from cloth;
    # this prevents a cuff boundary approximation from exporting skin as fabric.
    bounds = arm.getchannel('A').getbbox()
    if bounds:
        for y in range(bounds[1], bounds[3]):
            for x in range(bounds[0], bounds[2]):
                r, g, b, alpha = arm.getpixel((x, y))
                if not alpha:
                    continue
                if r > 65 and r - g >= 28 and g - b >= 12:
                    hand.putpixel((x, y), 255)
                elif garment == 'B' and b > r + 12 and b > g + 8:
                    hand.putpixel((x, y), 0)
                elif garment == 'A' and r > 120 and g > 100 and b > 80 and r - g < 28 and g - b < 35:
                    hand.putpixel((x, y), 0)
    return cut(arm, hand), cut(arm, ImageChops.invert(hand))


def source_frame(garment, index):
    if garment == 'A':
        return Image.open(ROOT / f'registered/v5/walk_w_{index}.png').convert('RGBA')
    sheet = Image.open(ROOT / 'sources/walk-b-v1.png').convert('RGBA')
    return sheet.crop((index * 512, 0, (index + 1) * 512, 768))


def complete_torso(garment):
    # GPT supplied real hidden cloth. Keep all source sheets intact.
    # Use one complete same-coordinate shirt surface, without patching differently
    # shaded source rectangles together. No invented pixels or part relocation.
    sheet = Image.open(ROOT / 'sources/torso-fill-v2.png').convert('RGBA')
    index = 0 if garment == 'A' else 2
    fill = sheet.crop((index * 512, 0, (index + 1) * 512, 768))
    return cut(fill, ImageChops.subtract(polygon(REGIONS['filled_torso']), neck_skin(fill)))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    parts_dir = ROOT / 'parts'
    masks_dir = ROOT / 'masks'
    for path in [parts_dir, masks_dir]:
        path.mkdir(exist_ok=True)
    records = []
    def save(image, relative, **metadata):
        path = ROOT / relative
        image.save(path)
        records.append({'path': relative, 'sha256': digest(path), **metadata})
        return relative
    for garment in ['A', 'B']:
        save(complete_torso(garment), f'parts/torso_{garment}.png',
             part_id=f'top_{garment}_torso', view_id=f'torso_w_{garment}',
             source='sources/torso-fill-v2.png, full torso cell 0 / 2',
             reused_by=[f'walk_w_{i}' for i in range(4)])
    recipes = {key: {'frames': []} for key in ['A', 'B']}
    for index in range(4):
        a = source_frame('A', index)
        a_parts = partition(a, index)
        b_parts = partition(source_frame('B', index), index)
        save(a_parts['base'], f'parts/body_{index}.png', owner='body_head_neck_lower', pose_id=f'walk_w_{index}')
        for part, mask in ownership(index).items():
            save(mask, f'masks/ownership_{part}_{index}.png', purpose='source_ownership', source=f'registered/v5/walk_w_{index}.png', owner_part=part, pose_id=f'walk_w_{index}')
        for side in ['far', 'near']:
            body, a_sleeve = split_arm(a_parts[side], index, side, 'A')
            _, b_sleeve = split_arm(b_parts[side], index, side, 'B')
            save(body, f'parts/body_{side}_{index}.png', owner=f'body_{side}_arm', pose_id=f'walk_w_{index}', source=f'registered/v5/walk_w_{index}.png')
            for garment, sleeve in [('A', a_sleeve), ('B', b_sleeve)]:
                save(sleeve, f'parts/sleeve_{garment}_{side}_{index}.png', owner=f'top_{garment}_{side}_sleeve', pose_id=f'walk_w_{index}')
                # Binary opaque-interior coverage only on the intended skin surface;
                # edge alpha is not multiplied against itself a second time.
                coverage = sleeve.getchannel('A').point(lambda alpha: 255 if alpha >= 240 else 0)
                save(coverage, f'masks/coverage_{garment}_{side}_{index}.png', purpose='coverage', owner_part=f'top_{garment}_{side}_sleeve', target_part=f'body_{side}_arm', pose_id=f'walk_w_{index}')
        for garment in ['A', 'B']:
            def layer(name, source, mask=None):
                value = {'id': name, 'source': source, 'offset_px': [0, 0]}
                if mask:
                    value['hide_mask'] = mask
                return value
            layers = [layer('body_head_neck_lower', f'parts/body_{index}.png')]
            # Far arm is behind the complete torso. Near arm/hand stays in front.
            for side in ['far', 'near']:
                if side == 'near':
                    layers.append(layer('shirt_torso', f'parts/torso_{garment}.png'))
                layers.append(layer(f'body_{side}_arm', f'parts/body_{side}_{index}.png', f'masks/coverage_{garment}_{side}_{index}.png'))
                layers.append(layer(f'{side}_sleeve', f'parts/sleeve_{garment}_{side}_{index}.png'))
            recipes[garment]['frames'].append({'pose_id': f'walk_w_{index}', 'layers': layers})
    inputs = [ROOT / 'semantic-regions.json', Path(__file__), ROOT / 'sources/torso-fill-v2.png', ROOT / 'sources/walk-b-v1.png', ROOT / 'registered/v5/registration.json']
    inputs += [ROOT / f'registered/v5/walk_w_{i}.png' for i in range(4)]
    source_contract = {str(p.relative_to(ROOT)): digest(p) for p in inputs}
    motion = {'schema_version': 1, 'template_id': 'adult-standard-v1',
              'source_contract': source_contract,
              'motion_set_id': 'walk-west-proof-v1', 'canvas_px': list(SIZE),
              'root_anchor_px': [256, 708], 'display_scale': 138 / 582,
              'frames': [{'pose_id': f'walk_w_{i}', 'duration_ms': 80} for i in range(4)],
              'recipes': recipes, 'review_status': 'unverified',
              'scope': 'body01 west four poses; fixed bald head, common trousers/shoes, cream short sleeve A / blue long sleeve B; not production'}
    (ROOT / 'motion.json').write_text(json.dumps(motion, indent=2) + '\n')
    (ROOT / 'parts-manifest.json').write_text(json.dumps({'schema_version': 1,
        'inputs': source_contract,
        'artifacts': records, 'placement': 'full_frame, offset=0; no local movement or scaling',
        'hidden_scope': 'complete torso surface supplied by GPT; only pose-visible body surfaces needed by these two sleeve lengths; no universal undressed body',
        'source_ownership_is_not_coverage': True, 'user_accepted': False}, indent=2) + '\n')
    print('Built source parts and two four-pose recipes; visual review required.')


if __name__ == '__main__':
    build()
