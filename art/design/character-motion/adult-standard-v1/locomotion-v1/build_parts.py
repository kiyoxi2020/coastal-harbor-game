"""Extract actual GPT pixels at their registered coordinates; no painted repairs.

The manual regions bound every palette-assisted decision. Ownership reconstructs
sources; coverage targets only arm skin; layer order is independently declared.
West walk is a byte-preserving reuse of the approved proof, not a new extraction.
"""
import copy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / 'walk-west-proof-v1'
SIZE = (512, 768)
DIRECTIONS = ('south', 'west', 'east', 'north')
REGIONS = json.loads((ROOT / 'semantic-regions.json').read_text())


def pose_ids():
    return [f'idle_{d}_0' for d in DIRECTIONS] + [f'walk_{d}_{i}' for d in DIRECTIONS for i in range(4)]


def new_pose_ids():
    return [p for p in pose_ids() if not p.startswith('walk_west_')]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def polygon(points):
    mask = Image.new('L', SIZE)
    if points:
        ImageDraw.Draw(mask).polygon([tuple(p) for p in points], fill=255)
    return mask


def cut(image, mask):
    result = image.copy()
    result.putalpha(ImageChops.multiply(image.getchannel('A'), mask))
    return result


def garment_reference(garment, pose):
    action, direction, index = pose.split('_')
    if garment == 'A':
        return f'registered/{pose}.png'
    if action == 'idle':
        return 'sources/idle-b-v2.png'
    return f'sources/walk-{direction}-b-v2.png' if direction == 'east' else f'sources/walk-{direction}-b-v1.png'


def sheet_frame(path, cell, pose):
    sheet = Image.open(path).convert('RGBA')
    image = sheet.crop((cell*512, 0, (cell+1)*512, 768))
    offset = REGIONS['poses'].get(pose, {}).get('source_registration_px', [0,0])
    if offset != [0,0]:
        registered = Image.new('RGBA', SIZE)
        registered.alpha_composite(image, tuple(offset))
        return registered
    return image


@lru_cache(maxsize=None)
def source_frame(garment, pose):
    action, direction, index = pose.split('_')
    if garment == 'A':
        return Image.open(ROOT / garment_reference(garment, pose)).convert('RGBA')
    if action == 'walk' and direction == 'west':
        return sheet_frame(OLD / 'sources/walk-b-v1.png', int(index), pose)
    cell = DIRECTIONS.index(direction) if action == 'idle' else int(index)
    return sheet_frame(ROOT / garment_reference(garment, pose), cell, pose)


def skin(r, g, b):
    return r > 65 and r - g >= 40 and g - b >= 25


def cloth_region(image, pose, garment):
    """Source cloth inside a manually observed torso ROI, retaining dark edges.

    Palette assists only the shirt ROI; it never partitions whole characters.
    Three-pixel adjacency includes the source's black collar/hem fringe, without
    using the trouser or skin pixels adjacent to that fringe.
    """
    roi = polygon(REGIONS['poses'][pose]['torso_region'])
    seed, edge = Image.new('L', SIZE), Image.new('L', SIZE)
    bounds = roi.getbbox()
    for y in range(bounds[1], bounds[3]):
        for x in range(bounds[0], bounds[2]):
            if not roi.getpixel((x, y)):
                continue
            r, g, b, alpha = image.getpixel((x, y))
            nx0, ny0, nx1, ny1 = REGIONS['poses'][pose]['neck_region']
            if not alpha or (nx0 <= x < nx1 and ny0 <= y < ny1 and skin(r, g, b)):
                continue
            cloth = (r >= 150 and r-g < 40 and g-b < 45) if garment == 'A' else (b > r+10 and b > g+5)
            if cloth:
                seed.putpixel((x, y), 255)
            elif max(r, g, b) < 180 and not (r < 150 and r-g < 20 and g-b >= 22):
                edge.putpixel((x, y), 255)
    return ImageChops.lighter(seed, ImageChops.multiply(seed.filter(ImageFilter.MaxFilter(7)), edge))


@lru_cache(maxsize=None)
def ownership(pose):
    if pose.startswith('walk_west_'):
        i = int(pose.rsplit('_', 1)[1])
        return {name: Image.open(OLD / f'masks/ownership_{old}_{i}.png').convert('L')
                for name, old in [('body_base', 'base'), ('arm_right', 'far'), ('torso', 'torso'), ('arm_left', 'near')]}
    region = REGIONS['poses'][pose]
    # The neck interface belongs to A, including its actual antialiased contour.
    # B may open the collar up to 3 pixels wider. Its skin is never exported:
    # preserve the existing A neck/contour in that bounded neighborhood instead.
    nx0, ny0, nx1, ny1 = region['neck_region']
    a, b = source_frame('A', pose), source_frame('B', pose)
    a_skin = Image.new('L', SIZE)
    for y in range(ny0, ny1):
        for x in range(nx0, nx1):
            if skin(*a.getpixel((x,y))[:3]): a_skin.putpixel((x,y),255)
    keep_neck = a_skin.copy()
    near_neck = a_skin.filter(ImageFilter.MaxFilter(7))
    for y in range(ny0, ny1):
        for x in range(nx0, nx1):
            if (near_neck.getpixel((x,y)) or max(a.getpixel((x,y))[:3]) < 110) and skin(*b.getpixel((x,y))[:3]): keep_neck.putpixel((x,y),255)
    left = ImageChops.subtract(polygon(region['arms']['arm_left']), keep_neck)
    right = ImageChops.subtract(ImageChops.subtract(polygon(region['arms']['arm_right']), left), keep_neck)
    arms = ImageChops.lighter(left, right)
    torso = ImageChops.subtract(ImageChops.subtract(cloth_region(a, pose, 'A'), arms), keep_neck)
    union = ImageChops.lighter(arms, torso)
    return {'body_base': ImageChops.invert(union), 'arm_left': left, 'torso': torso, 'arm_right': right}


def partition(image, pose):
    return {key: cut(image, mask) for key, mask in ownership(pose).items()}


def split_arm(arm, pose, side, garment):
    hand = polygon(REGIONS['poses'][pose]['hands'][garment][side])
    bounds = arm.getchannel('A').getbbox()
    if bounds:
        for y in range(bounds[1], bounds[3]):
            for x in range(bounds[0], bounds[2]):
                r, g, b, alpha = arm.getpixel((x, y))
                if not alpha:
                    continue
                if skin(r, g, b):
                    hand.putpixel((x, y), 255)
                elif garment == 'B' and b > r + 12 and b > g + 8:
                    hand.putpixel((x, y), 0)
                elif garment == 'A' and r > 120 and g > 100 and b > 80 and r-g < 40 and g-b < 40:
                    hand.putpixel((x, y), 0)
    return cut(arm, hand), cut(arm, ImageChops.invert(hand))


def torso_reference(garment, pose):
    action, direction, index = pose.split('_')
    if action == 'idle':
        return f'sources/torso-fill-{garment.lower()}-v1.png', DIRECTIONS.index(direction)
    version = 2 if direction == 'east' else 1
    return f'sources/walk-{direction}-torso-{garment.lower()}-v{version}.png', int(index)


@lru_cache(maxsize=None)
def complete_torso(garment, pose):
    path, index = torso_reference(garment, pose)
    image = sheet_frame(ROOT / path, index, pose)
    # Visible cloth always comes from the actual pose, preserving its hem/collar.
    # The GPT complete shirt supplies only the independently declared arm-
    # occluded area; its shifted head, neck, trousers and visible hem never enter.
    masks = ownership(pose)
    arm_regions = ImageChops.lighter(masks['arm_left'], masks['arm_right'])
    hidden_mask = ImageChops.multiply(arm_regions, source_frame('A', pose).getchannel('A').point(lambda a: 255 if a else 0))
    hidden = cut(image, ImageChops.multiply(cloth_region(image, pose, garment), hidden_mask))
    visible = partition(source_frame(garment, pose), pose)['torso']
    return Image.alpha_composite(hidden, visible)


def build():
    # Every build binds current on-disk registered inputs, including serial
    # registration updates made before this invocation.
    source_frame.cache_clear()
    ownership.cache_clear()
    complete_torso.cache_clear()
    for name in ['parts', 'masks', 'recipes', 'baked']:
        (ROOT / name).mkdir(exist_ok=True)
    records, dependencies = [], set()
    def save(image, relative, **metadata):
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path)
        records.append({'path': relative, 'sha256': digest(path), **metadata})
        return relative
    copied = {}
    def reuse(relative):
        if relative not in copied:
            dest = f'{Path(relative).parts[0]}/west-proof/' + '/'.join(Path(relative).parts[1:])
            (ROOT / dest).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(OLD / relative, ROOT / dest)
            records.append({'path': dest, 'sha256': digest(ROOT / dest), 'purpose': 'exact_approved_west_reuse',
                            'origin': f'../walk-west-proof-v1/{relative}', 'origin_sha256': digest(OLD / relative)})
            copied[relative] = dest
        return copied[relative]
    old_motion = json.loads((OLD / 'motion.json').read_text())
    recipes = {g: {'frames': []} for g in ['A', 'B']}
    for pose in pose_ids():
        if pose.startswith('walk_west_'):
            index = int(pose.rsplit('_', 1)[1])
            for name in ['base', 'near', 'far', 'torso']:
                reuse(f'masks/ownership_{name}_{index}.png')
            for g in recipes:
                frame = copy.deepcopy(old_motion['recipes'][g]['frames'][index])
                frame['pose_id'] = pose
                for layer in frame['layers']:
                    layer['source'] = reuse(layer['source'])
                    if 'hide_mask' in layer:
                        layer['hide_mask'] = reuse(layer['hide_mask'])
                recipes[g]['frames'].append(frame)
            continue
        region = REGIONS['poses'][pose]
        original = source_frame('A', pose)
        parts = partition(original, pose)
        body_path = save(parts['body_base'], f'parts/{pose}/body_base.png', owner='head_neck_pants_shoes', pose_id=pose, source=f'registered/{pose}.png')
        for name, mask in ownership(pose).items():
            save(mask, f'masks/ownership_{pose}_{name}.png', purpose='source_ownership', owner_part=name, pose_id=pose)
        for side in ['arm_left', 'arm_right']:
            body, _ = split_arm(parts[side], pose, side, 'A')
            save(body, f'parts/{pose}/body_{side}.png', owner=f'body_{side}', source=f'registered/{pose}.png', pose_id=pose)
        for garment in recipes:
            source = source_frame(garment, pose)
            own = partition(source, pose)
            torso_path, cell = torso_reference(garment, pose)
            dependencies.add(torso_path)
            visible_source = garment_reference(garment, pose)
            visible_cell = 0 if garment == 'A' else (DIRECTIONS.index(pose.split('_')[1]) if pose.startswith('idle_') else int(pose.rsplit('_',1)[1]))
            visible_mask_path = save(ownership(pose)['torso'], f'masks/visible_{pose}_{garment}_torso.png',
                                     purpose='visible_source_extraction', source=visible_source, source_cell=visible_cell,
                                     target_part=f'top_{garment}_torso', pose_id=pose)
            fill = sheet_frame(ROOT / torso_path, cell, pose)
            hidden = ImageChops.multiply(ImageChops.lighter(ownership(pose)['arm_left'], ownership(pose)['arm_right']),
                                        original.getchannel('A').point(lambda a: 255 if a else 0))
            hidden = ImageChops.multiply(hidden, cloth_region(fill, pose, garment))
            hidden_mask_path = save(hidden, f'masks/hidden_fill_{pose}_{garment}_torso.png',
                                    purpose='hidden_source_extraction', source=torso_path, source_cell=cell,
                                    target_part=f'top_{garment}_torso', pose_id=pose)
            save(complete_torso(garment, pose), f'parts/{pose}/torso_{garment}.png',
                 owner=f'top_{garment}_torso', source=torso_path, source_cell=cell, pose_id=pose,
                 complete_hidden_cloth=True, visible_source=visible_source, visible_source_cell=visible_cell,
                 visible_mask=visible_mask_path, hidden_mask=hidden_mask_path,
                 hidden_source_registration_px=region.get('source_registration_px',[0,0]),
                 visible_source_registration_px=(region.get('source_registration_px',[0,0]) if garment=='B' else [0,0]),
                 occlusion_mask=f'masks/occlusion_{pose}_{garment}_torso.png',
                 hidden_region='actual source arm surfaces intersected with GPT complete cloth; no body repair')
            occlusion = Image.new('L', SIZE)
            for side in ['arm_left', 'arm_right']:
                body_arm, _ = split_arm(parts[side], pose, side, 'A')
                _, sleeve = split_arm(own[side], pose, side, garment)
                occlusion = ImageChops.lighter(occlusion, ImageChops.lighter(body_arm.getchannel('A'), sleeve.getchannel('A')).point(lambda a: 255 if a else 0))
                save(sleeve, f'parts/{pose}/sleeve_{garment}_{side}.png', owner=f'top_{garment}_{side}', pose_id=pose, source=garment_reference(garment, pose), source_registration_px=(region.get('source_registration_px',[0,0]) if garment=='B' else [0,0]))
                coverage = sleeve.getchannel('A').point(lambda a: 255 if a >= 240 else 0)
                save(coverage, f'masks/coverage_{pose}_{garment}_{side}.png', purpose='coverage', owner_part=f'top_{garment}_{side}', target_part=f'body_{side}', pose_id=pose)
            occlusion_path = save(occlusion, f'masks/occlusion_{pose}_{garment}_torso.png', purpose='current_occlusion', owner_parts=['body_arm_left','body_arm_right',f'top_{garment}_arm_left',f'top_{garment}_arm_right'], target_part=f'top_{garment}_torso', pose_id=pose, derivation='actual positive-alpha visible arm surfaces; preserves source antialiasing on foreground')
            def layer(name, source, mask=None):
                result = {'id': name, 'source': source, 'offset_px': [0, 0]}
                if mask: result['hide_mask'] = mask
                return result
            layers = [layer('body_head_neck_lower', body_path)]
            def add_arm(side):
                layers.append(layer(f'body_{side}', f'parts/{pose}/body_{side}.png', f'masks/coverage_{pose}_{garment}_{side}.png'))
                layers.append(layer(f'{garment}_{side}_sleeve', f'parts/{pose}/sleeve_{garment}_{side}.png'))
            for side in region['behind_torso']: add_arm(side)
            layers.append(layer('shirt_torso', f'parts/{pose}/torso_{garment}.png', occlusion_path))
            for side in ['arm_left', 'arm_right']:
                if side not in region['behind_torso']: add_arm(side)
            recipes[garment]['frames'].append({'pose_id': pose, 'layers': layers})
    inputs = ['build_parts.py', 'semantic-regions.json', 'template.json', 'poses.json', 'register_sources.py', 'register_pose_observations.py', 'registered/registration.json', 'symmetry-review.json']
    inputs += [f'registered/{p}.png' for p in pose_ids()]
    inputs += [garment_reference('B', pose) for pose in new_pose_ids()]
    inputs += sorted(dependencies)
    # Bind extraction/ownership/occlusion masks too, even when not read directly
    # as a compositor layer: semantic review depends on these actual files.
    inputs += [record['path'] for record in records]
    inputs += [str(p.relative_to(ROOT)) for p in (ROOT / 'masks').glob('source_background*')]
    registration = json.loads((ROOT / 'registered/registration.json').read_text())
    inputs += [f['source'] for f in registration['frames'] if '..' not in Path(f['source']).parts]
    inputs += [str(Path(p).with_suffix('.json')) for p in list(inputs) if Path(p).suffix=='.png' and (ROOT / Path(p).with_suffix('.json')).is_file()]
    source_contract = {p: digest(ROOT / p) for p in sorted(set(inputs))}
    frames, actions = [], {}
    for action, count in [('idle',1),('walk',4)]:
        actions[action] = {'loop': True, 'directions': {}}
        for d in DIRECTIONS:
            poses = [f'{action}_{d}_{i}' for i in range(count)]
            actions[action]['directions'][d] = poses
            frames += [{'pose_id': p, 'duration_ms': 200 if action=='idle' else 80, 'action': action, 'direction': d} for p in poses]
    motion = {'schema_version':2,'template_id':'adult-standard-v1','motion_set_id':'locomotion-v1',
              'canvas_px':list(SIZE),'root_anchor_px':[256,708],'display_scale':138/582,
              'frames':frames,'actions':actions,'move_policy':{'idle':{'base_world_speed':0,'playback_rate':1},'walk':{'base_world_speed':72,'playback_rate':0.75}},
              'source_contract':source_contract,'recipes':recipes,'review_status':'unverified',
              'scope':'draft 20-pose shared A body; GPT complete shirts and per-pose sleeves A/B; west walk exact accepted reuse; strict landmark freeze and native visual approval pending'}
    for garment, recipe in recipes.items():
        (ROOT / f'recipes/{garment}.json').write_text(json.dumps(recipe, indent=2)+'\n')
    (ROOT / 'motion.json').write_text(json.dumps(motion,indent=2)+'\n')
    (ROOT / 'parts-manifest.json').write_text(json.dumps({'schema_version':2,'inputs':source_contract,'artifacts':records,
        'placement':'full_frame offset0; no part translation/scale','source_ownership_is_not_coverage':True,
        'hidden_scope':'real complete torso supplied by GPT; visible A body plus sleeve coverage, not universal undressed body',
        'review_status':'unverified','user_accepted':False},indent=2)+'\n')
    spec = importlib.util.spec_from_file_location('coastal_compose', OLD / 'tools/compose.py')
    compositor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(compositor)
    baked = compositor.compose(ROOT / 'motion.json')
    return {'review_status':'unverified','artifact_digest':baked['artifact_digest']}


if __name__ == '__main__':
    print(json.dumps(build()))
