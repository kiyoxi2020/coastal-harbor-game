#!/usr/bin/env python3
"""Extract fixed-template wearable candidates. Never grants visual or user acceptance.

Usage: python3 art/design/character-candidates-v2/build_wearable_candidates.py --id top02
       python3 art/design/character-candidates-v2/build_wearable_candidates.py --all
Only generated layers/previews/owner masks/metadata and wearables-built.json are written.
"""
from __future__ import annotations
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[3]
ART = Path(__file__).resolve().parent
DIRECTIONS = ('south', 'west', 'east', 'north')
CATEGORIES = ('top', 'pants', 'shoes')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def polygons(size: tuple[int, int], shapes: list) -> Image.Image:
    mask = Image.new('L', size)
    draw = ImageDraw.Draw(mask)
    for shape in shapes:
        draw.polygon([tuple(point) for point in shape], fill=255)
    return mask


def warm_skin(pixel: tuple) -> bool:
    r, g, b, a = pixel
    return a >= 200 and r > 185 and r > g + 25 and g > b + 12


def waist_top_mask(base: Image.Image) -> Image.Image:
    """Template-only waist seam registration, never classify a new garment's color."""
    mask = Image.new('L', base.size)
    bp, mp = base.load(), mask.load()
    for y in range(519, 546):
        for x in range(512):
            r, g, b, a = bp[x, y]
            if a >= 200 and r > 165 and g > 145 and r - b > 12:
                mp[x, y] = 255
    nearby = mask.filter(ImageFilter.MaxFilter(5)).load()
    for y in range(519, 546):
        for x in range(512):
            if nearby[x, y] and bp[x, y][3] >= 200 and max(bp[x, y][:3]) < 100:
                mp[x, y] = 255
    return mask


def local_anatomy_override(source: Image.Image, owner: Image.Image, item_id: str, policy: dict) -> Image.Image:
    """Explicit design/material/ankle domain; dark anatomy may join bright skin seeds."""
    mask = Image.new('L', source.size)
    rule = policy.get('source_skin_overrides', {}).get(item_id)
    if not rule:
        return mask
    points, seeds = set(), []
    sp, op = source.load(), owner.load()
    for y in range(rule['y_start'], rule['y_stop']):
        for x in range(source.width):
            r, g, b, a = sp[x, y]
            if op[x, y] and a >= policy['alpha_min'] and r > rule['r_min'] and g > rule['g_min'] and r > g + rule['rg_min'] and g > b + rule['gb_min']:
                points.add((x, y))
                if r > rule.get('seed_r_min', 0) and g > rule.get('seed_g_min', 0):
                    seeds.append((x, y))
    if rule.get('connected_to_bright_skin'):
        pending, reached = deque(seeds), set(seeds)
        while pending:
            x, y = pending.popleft()
            for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if neighbor in points and neighbor not in reached:
                    reached.add(neighbor)
                    pending.append(neighbor)
        points = reached
    pixels = mask.load()
    for point in points:
        pixels[point] = 255
    return mask


def register_pants_hem(source: Image.Image, semantic_owner: Image.Image, item_id: str,
                       direction: str, policy: dict) -> tuple[Image.Image, dict]:
    """Register the real garment hem once; all pixels below it belong to anatomy.

    Palette cues assist only in the manually bounded hem search area. They do not
    erase burgundy/plum/utility fabric pixels from the final component.
    """
    rule = policy.get('pants_hem_registration', {}).get(item_id, {}).get(direction)
    if rule is None:
        raise ValueError(f'{item_id}/{direction}: missing reviewed hem search domain')
    low, high = rule['search_band']
    source_pixels, allowed = source.load(), semantic_owner.load()
    def local_skin(pixel):
        r, g, b, a = pixel
        return a >= policy['alpha_min'] and r > g + 8 and g > b + 6 and g - b > (r - g) * 0.25
    def material_cue(pixel):
        r, g, b, _ = pixel
        cue = rule.get('material_cue')
        if cue == 'blue':
            return b >= r and b >= g - 8
        if cue == 'green':
            return g >= r and g >= b
        if cue == 'teal':
            return g >= r and b >= r
        if cue == 'burgundy_plum':
            return b >= g
        if cue == 'gray':
            return max(r, g, b) - min(r, g, b) <= 30
        raise ValueError(f'{item_id}/{direction}: unknown material cue')
    cores = [None] * source.width
    for x in range(source.width):
        for y in range(low, high):
            value = source_pixels[x, y]
            if allowed[x, y] and value[3] >= policy['alpha_min'] and max(value[:3]) > rule['material_rgb_min'] and material_cue(value) and not local_skin(value):
                cores[x] = y
    if not any(value is not None for value in cores):
        raise ValueError(f'{item_id}/{direction}: no garment material in hem search band; review source/domain')
    boundary = [low - 1] * source.width
    for x, bottom in enumerate(cores):
        if bottom is None:
            neighbors = [cores[n] for n in range(max(0, x - 4), min(source.width, x + 5)) if cores[n] is not None]
            if not neighbors:
                continue
            bottom = max(neighbors)
        end = min(high - 1, bottom + rule['outline_extension'])
        for y in range(bottom + 1, end + 1):
            value = source_pixels[x, y]
            if value[3] < policy['alpha_min'] or local_skin(value):
                end = y - 1
                break
        boundary[x] = end
    result = semantic_owner.copy()
    output = result.load()
    for x, bottom in enumerate(boundary):
        for y in range(bottom + 1, source.height):
            output[x, y] = 0
    return result, {'search_band': [low, high], 'boundary_y_by_x': boundary,
                    'method': 'fixed-source hem silhouette; no anatomy below garment contour',
                    'source_dimensions': list(source.size)}


def assert_preserved(base: Image.Image, preview: Image.Image, owner: Image.Image,
                     protected: Image.Image) -> dict:
    base_pixels, out_pixels = base.load(), preview.load()
    own_pixels, protected_pixels = owner.load(), protected.load()
    nonowner = protected_changed = 0
    for y in range(base.height):
        for x in range(base.width):
            if base_pixels[x, y] != out_pixels[x, y]:
                nonowner += not bool(own_pixels[x, y])
                protected_changed += bool(protected_pixels[x, y])
    if nonowner or protected_changed:
        raise ValueError(f'RGBA preservation failed: nonowner={nonowner}; protected={protected_changed}')
    return {'non_owner_rgba_unchanged': True, 'head_and_hands_rgba_unchanged': True,
            'non_owner_mismatch_pixels': nonowner, 'protected_mismatch_pixels': protected_changed}


def extract(base: Image.Image, source: Image.Image, category: str, item_id: str,
            direction: str, policy: dict) -> tuple:
    if base.size != (512, 768) or source.size != base.size:
        raise ValueError('frame size must be 512x768; do not resize or move components')
    key = 'skirt' if item_id in policy['skirt_ids'] else 'boot' if item_id in policy['boot_ids'] else category
    semantic = polygons(base.size, policy[key][direction])
    owner = semantic.copy()
    hands = polygons(base.size, policy['protected_hands'][direction])
    protected = hands.copy()
    ImageDraw.Draw(protected).rectangle(tuple(policy['head_protected_box']), fill=255)
    neck_domain = polygons(base.size, policy.get('neck_skin_domains', {}).get(direction, [policy['protected_neck'][direction]]))
    neck_skin = Image.new('L', base.size)
    bp, np, nd = base.load(), neck_skin.load(), neck_domain.load()
    source_pixels = source.load()
    source_neck_pixels = 0
    for y in range(355, 407):
        for x in range(512):
            r, g, b, a = bp[x, y]
            if nd[x, y] and a >= 200 and r > 80 and r > g + 40 and g > b + 10:
                np[x, y] = 255
            if category == 'top' and nd[x, y]:
                sr, sg, sb, sa = source_pixels[x, y]
                if sa >= 200 and sr > 200 and sg > 120 and sr > sg + 40 and sg > sb + 18:
                    np[x, y] = 255
                    source_neck_pixels += 1
    near = neck_skin.filter(ImageFilter.MaxFilter(5)).load()
    for y in range(355, 407):
        for x in range(512):
            if nd[x, y] and near[x, y] and max(bp[x, y][:3]) < 90:
                np[x, y] = 255
    if category == 'top':
        patch_domain = polygons(base.size, policy.get('source_neck_skin_patches', {}).get(item_id, {}).get(direction, []))
        pp = patch_domain.load()
        for y in range(355, 414):
            for x in range(512):
                sr, sg, sb, sa = source_pixels[x, y]
                if pp[x, y] and sa >= 200 and sr > 100 and sg > 40 and sr > sg + 35 and sg > sb + 12:
                    np[x, y] = 255
        protected = ImageChops.lighter(protected, neck_skin)
    hand_fringe_pixels = 0
    hand_fringe_domain = None
    if category == 'pants':
        hand_rule = policy['pants_hand_fringe']
        hand_fringe_domain = hands.filter(ImageFilter.MaxFilter(hand_rule['domain_expansion']))
        hand_domain_pixels = hand_fringe_domain.load()
        source_hand_skin = Image.new('L', base.size)
        hsp = source_hand_skin.load()
        for y in range(490, 580):
            for x in range(512):
                r, g, b, a = source_pixels[x, y]
                if hand_domain_pixels[x, y] and a >= 200 and r > 80 and g > 30 and r > g + 20 and g > b + 8:
                    hsp[x, y] = 255
                    hand_fringe_pixels += 1
        near_hand_skin = source_hand_skin.filter(ImageFilter.MaxFilter(hand_rule['outline_neighborhood'])).load()
        for y in range(490, 580):
            for x in range(512):
                if hand_domain_pixels[x, y] and near_hand_skin[x, y] and source_pixels[x, y][3] >= 200 and max(source_pixels[x, y][:3]) < 90:
                    hsp[x, y] = 255
        protected = ImageChops.lighter(protected, source_hand_skin)
    owner = ImageChops.subtract(owner, protected)
    old_shirt = waist_top_mask(base).load()
    op, sp = owner.load(), source.load()
    removed_skin = 0
    removed_body_outline = 0
    for y in range(519, 546):
        for x in range(512):
            if category == 'top' and not old_shirt[x, y]:
                op[x, y] = 0
            elif category == 'pants' and old_shirt[x, y]:
                op[x, y] = 0
    hem_registration = None
    if category == 'pants':
        unclipped_owner = owner.copy()
        owner, hem_registration = register_pants_hem(source, owner, item_id, direction, policy)
        protected = ImageChops.lighter(protected, ImageChops.subtract(unclipped_owner, owner))
        op = owner.load()
    if category == 'shoes':
        skin_start = policy['pants_skin_start'].get(item_id, 645) if category == 'pants' else 620
        # A local exposed-shin/ankle exclusion, only inside a reviewed garment envelope.
        # Tops (including brick-red fabric) never pass through this color test.
        override_pixels = local_anatomy_override(source, owner, item_id, policy).load()
        source_skin = Image.new('L', base.size)
        base_skin = Image.new('L', base.size)
        ss, bs = source_skin.load(), base_skin.load()
        for y in range(skin_start, 768):
            for x in range(512):
                if op[x, y] and (warm_skin(sp[x, y]) or override_pixels[x, y]):
                    ss[x, y] = 255
                    op[x, y] = 0
                    removed_skin += 1
                if warm_skin(bp[x, y]):
                    bs[x, y] = 255
        # Corroborated old shin contour is anatomy, not a fabric/shoe layer. Keep the
        # template contour rather than importing a second source anatomy outline.
        sn = source_skin.filter(ImageFilter.MaxFilter(5)).load()
        bn = base_skin.filter(ImageFilter.MaxFilter(5)).load()
        for y in range(skin_start, min(665, 768)):
            for x in range(512):
                if op[x, y] and sn[x, y] and bn[x, y] and bp[x, y][3] >= 200 and max(bp[x, y][:3]) < 100 and max(sp[x, y][:3]) < 100:
                    op[x, y] = 0
                    removed_body_outline += 1
    clean = source.copy()
    clean.putalpha(clean.getchannel('A').point(lambda alpha: alpha if alpha >= policy['alpha_min'] else 0))
    component = Image.new('RGBA', base.size)
    component.paste(clean, (0, 0), owner)
    preview = base.copy()
    # Replace the whole owned surface including transparent pixels: no doubled alpha edges.
    preview.paste(component, (0, 0), owner)
    checks = assert_preserved(base, preview, owner, protected)
    if hem_registration is not None:
        checks['garment_hem_registration'] = hem_registration
        checks['anatomy_below_hem_owned_pixels'] = 0
        checks['source_hand_fringe_guard_pixels'] = hand_fringe_pixels
        lcp = component.load()
        hdp = hand_fringe_domain.load()
        hand_leaks = sum(1 for y in range(490, 580) for x in range(512) if hdp[x, y] and lcp[x, y][3] >= 200 and lcp[x, y][0] > 80 and lcp[x, y][1] > 30 and lcp[x, y][0] > lcp[x, y][1] + 20 and lcp[x, y][1] > lcp[x, y][2] + 8)
        if hand_leaks:
            raise ValueError(f'{item_id}/{direction}: source hand-skin remains in lower garment')
        checks['source_hand_fringe_leak_pixels'] = hand_leaks
    if category == 'top':
        lp = component.load()
        leaks = sum(1 for y in range(355, 407) for x in range(512) if nd[x, y] and lp[x, y][3] >= 200 and lp[x, y][0] > 200 and lp[x, y][1] > 120 and lp[x, y][0] > lp[x, y][1] + 40 and lp[x, y][1] > lp[x, y][2] + 18)
        if leaks:
            raise ValueError(f'{item_id}/{direction}: {leaks} source neck-skin pixels remain in garment layer')
        checks['neck_source_skin_leak_pixels'] = leaks
        patch_leaks = sum(1 for y in range(355, 414) for x in range(512) if pp[x, y] and lp[x, y][3] >= 200 and lp[x, y][0] > 100 and lp[x, y][1] > 40 and lp[x, y][0] > lp[x, y][1] + 35 and lp[x, y][1] > lp[x, y][2] + 12)
        if patch_leaks:
            raise ValueError(f'{item_id}/{direction}: source dark skin remains in reviewed neck patch')
        checks['neck_dark_patch_leak_pixels'] = patch_leaks
        checks['neckline_visual_fit'] = 'unverified; preserve original template RGBA; no hidden chest anatomy invented'
    if component.getchannel('A').getbbox() is None:
        raise ValueError(f'{item_id}/{direction}: extracted component is empty')
    checks.update({'owner_box': list(owner.getbbox()), 'component_box': list(component.getchannel('A').getbbox()),
                   'source_neck_skin_guard_pixels': source_neck_pixels, 'local_source_skin_pixels_excluded': removed_skin, 'corroborated_shin_outline_pixels_excluded': removed_body_outline,
                   'transform': 'identity; exact 512x768 source column; no part translation/resizing',
                   'semantic_visual_review': 'unverified'})
    return component, owner, preview, semantic, protected, checks


def source_geometry_issues(base: Image.Image, source: Image.Image, category: str) -> list[str]:
    if category != 'pants':
        return []
    # The source must retain the old cream shirt at its waist; cannot repair raised belts
    # by silently covering the source with the old shirt after extraction.
    bp, sp = base.load(), source.load()
    changed = total = 0
    for y in range(503, 532):
        for x in range(512):
            r, g, b, a = bp[x, y]
            if a >= 200 and r > 165 and g > 145 and r - b > 12:
                total += 1
                sr, sg, sb, sa = sp[x, y]
                if sa < 200 or not (sr > 155 and sg > 135 and sr - sb > 8):
                    changed += 1
    return [f'cream shirt waist displaced: {changed}/{total} template shirt pixels replaced in y503..531'] if total and changed > max(100, total * 0.12) else []


def build_one(job: dict, policy: dict, master: Image.Image, template_path: Path,
              selection_path: Path, registration: dict) -> dict:
    item_id, category = job['id'], job['category']
    directory = Path(job['directory']).resolve()
    expected_dir = ART / category / item_id
    if directory != expected_dir.resolve() or category not in CATEGORIES or not 2 <= int(item_id[len(category):]) <= 10:
        raise ValueError('job is outside assigned wearable output directories')
    source_path = directory / 'source.png'
    prompt_path = directory / 'prompt.txt'
    record = {'id': item_id, 'design_id': item_id, 'category': category, 'label': job['label'],
              'status': 'candidate', 'build_status': 'pending_source',
              'template_id': policy['template_id'], 'template_hash': sha(template_path),
              'body_template': relative(template_path), 'source': relative(source_path),
              'prompt': relative(prompt_path), 'compatibility': {'body_ids': ['body01'], 'pose': 'standing_0'},
              'visual_review': 'unverified; not user accepted', 'errors': []}
    if not source_path.is_file() or not prompt_path.is_file():
        record['errors'].append('source.png or prompt.txt not yet present')
        return record
    if sha(source_path) in policy.get('rejected_source_sha256', {}).get(item_id, []):
        record.update(build_status='rework_required', errors=[policy['rejected_reasons'][item_id]])
        return record
    with Image.open(source_path) as image:
        source = image.convert('RGBA')
    if source.size != tuple(policy['atlas']):
        record.update(build_status='rework_required', errors=[f'source size {source.size}; expected 2048x768; no auto resize/crop'])
        return record
    for index, direction in enumerate(DIRECTIONS):
        box = (index * 512, 0, (index + 1) * 512, 768)
        record['errors'].extend(f'{direction}: {issue}' for issue in source_geometry_issues(master.crop(box), source.crop(box), category))
    if record['errors']:
        record['build_status'] = 'rework_required'
        return record
    hashes = {}
    for path in (source_path, prompt_path, template_path, selection_path, Path(__file__), ART / 'wearables-mask-policy.json', ROOT / policy['source_policy'], ROOT / 'art/design/character-bodies/adult-standard-v1/registration/registration.json'):
        hashes[relative(path)] = sha(path)
    record.update(previews={}, components={}, owners={}, semantics={}, protected={}, checks={},
                  display={'scale': 0.2371134, 'root_anchors': {}}, hashes=hashes)
    for name in ('components', 'previews', 'owners'):
        (directory / name).mkdir(parents=True, exist_ok=True)
    for index, direction in enumerate(DIRECTIONS):
        box = (index * 512, 0, (index + 1) * 512, 768)
        component, owner, preview, semantic, protected, checks = extract(master.crop(box), source.crop(box), category, item_id, direction, policy)
        regression = policy.get('source_bound_regressions', {}).get(item_id)
        if regression:
            if sha(source_path) != regression['source_sha256']:
                checks['source_bound_regression'] = 'stale_source; exact-pixel regressions require review'
            else:
                for point in regression.get('transparent_component_points', {}).get(direction, []):
                    if component.getpixel(tuple(point))[3] != 0:
                        raise ValueError(f'{item_id}/{direction}: known anatomy leak regression at {point}')
                source_frame = source.crop(box)
                for point in regression.get('retained_source_points', {}).get(direction, []):
                    if component.getpixel(tuple(point)) != source_frame.getpixel(tuple(point)):
                        raise ValueError(f'{item_id}/{direction}: garment seam/color changed at {point}')
                checks['source_bound_regression'] = 'passed for exact source_sha256'
        outputs = [('components', component, direction), ('previews', preview, direction),
                   ('owners', owner, direction), ('semantics', semantic, 'semantic-' + direction),
                   ('protected', protected, 'protected-' + direction)]
        for key, image, stem in outputs:
            folder = key if key in ('components', 'previews') else 'owners'
            path = directory / folder / (stem + '.png')
            image.save(path)
            record[key][direction] = relative(path)
            record['hashes'][relative(path)] = sha(path)
        record['checks'][direction] = checks
        record['display']['root_anchors'][direction] = registration['frames'][direction]['root_anchor']
    record['build_status'] = 'built_candidate'
    record['geometry_status'] = 'nonowner/head/hand byte invariants checked; semantic fit remains unverified'
    record['canvas'] = [512, 768]
    record['metadata'] = relative(directory / 'metadata.json')
    # Metadata excludes its own path/hash from the recursive digest and is included by caller.
    payload = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    record['build_artifact_digest'] = hashlib.sha256(payload).hexdigest()
    (directory / 'metadata.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    record['hashes'][record['metadata']] = sha(directory / 'metadata.json')
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--id', help='one top/pants/shoes candidate 02..10')
    group.add_argument('--all', action='store_true', help='build all 27; missing/rework sources remain explicitly incomplete')
    args = parser.parse_args()
    policy = json.loads((ART / 'wearables-mask-policy.json').read_text())
    jobs = [job for job in json.loads((ART / 'jobs.json').read_text()) if job['category'] in CATEGORIES]
    selected = [job for job in jobs if args.all or job['id'] == args.id]
    if not selected:
        parser.error('id must identify a top/pants/shoes job in jobs.json')
    body_dir = ROOT / 'art/design/character-bodies/adult-standard-v1'
    selection_path = body_dir / 'selection.json'
    selection = json.loads(selection_path.read_text())
    revision = selection['active_revision']
    template_path = body_dir / revision['source']
    if revision['id'] != policy['active_revision'] or sha(template_path) != revision['source_sha256']:
        parser.error('template revision/hash does not match approved selection and mask policy; do not reuse stale masks')
    with Image.open(template_path) as image:
        master = image.convert('RGBA')
    if master.size != tuple(policy['atlas']):
        parser.error('mother atlas must be 2048x768')
    registration_path = body_dir / 'registration/registration.json'
    registration = json.loads(registration_path.read_text())
    summary_path = ART / 'wearables-built.json'
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {'schema_version': 1, 'entries': {}}
    for job in selected:
        try:
            record = build_one(job, policy, master, template_path, selection_path, registration)
        except (OSError, ValueError, KeyError) as exc:
            record = {'id': job['id'], 'category': job['category'], 'status': 'candidate',
                      'build_status': 'rework_required', 'errors': [str(exc)]}
        summary['entries'][job['id']] = record
        print(job['id'], record['build_status'], '; '.join(record.get('errors', [])))
    summary.update(builder_sha256=sha(Path(__file__)), policy_sha256=sha(ART / 'wearables-mask-policy.json'),
                   template_sha256=sha(template_path), selection_sha256=sha(selection_path),
                   registration_sha256=sha(registration_path),
                   scope='27 independent wearable designs only; four directions/layers are not new designs. No source alteration, gameplay changes, native or user approval.')
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    return 1 if any(summary['entries'][j['id']]['build_status'] != 'built_candidate' for j in selected) else 0

if __name__ == '__main__':
    raise SystemExit(main())
