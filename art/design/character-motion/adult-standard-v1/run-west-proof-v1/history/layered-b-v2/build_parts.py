"""Extract GPT run garments at original pose coordinates; no pixel painting or warp."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent
SIZE = (512, 768)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def polygon(points):
    mask = Image.new('L', SIZE)
    ImageDraw.Draw(mask).polygon([tuple(p) for p in points], fill=255)
    return mask

def cut(image, mask):
    out = image.copy()
    out.putalpha(ImageChops.multiply(image.getchannel('A'), mask))
    return out

def union(*masks):
    out = Image.new('L', SIZE)
    for mask in masks:
        out = ImageChops.lighter(out, mask)
    return out

def opaque(mask):
    return mask.point(lambda a: 255 if a else 0)

def cloth_mask(image, roi, garment):
    """Palette only assists manual semantic ROI, preserving actual dark contours."""
    seed, edges = Image.new('L',SIZE), Image.new('L',SIZE)
    bounds = roi.getbbox()
    for y in range(bounds[1],bounds[3]):
        for x in range(bounds[0],bounds[2]):
            if not roi.getpixel((x,y)):
                continue
            r,g,b,a = image.getpixel((x,y))
            if a < 16:
                continue
            is_cloth = (r >= 100 and g >= 90 and b >= 80 and r-g < 35 and g-b < 28) if garment == 'A' else (b > r+12 and b > g+5)
            if is_cloth:
                seed.putpixel((x,y),255)
            elif max(r,g,b) < 150 and not (r < 150 and r-g < 20 and g-b >= 22):
                edges.putpixel((x,y),255)
    # GPT blue source has up to six-pixel black garment contours. A three-
    # pixel adjacency dropped the outer contour and produced transparent seams.
    return union(seed,ImageChops.multiply(seed.filter(ImageFilter.MaxFilter(13)),edges))

def registered_sheet(name, index):
    sheet = Image.open(ROOT/f'sources/{name}.png').convert('RGBA')
    if sheet.size != (2048,768):
        raise ValueError(f'{name}: exact four-cell2048x768 source required')
    cell = sheet.crop((index*512,0,(index+1)*512,768))
    result = Image.new('RGBA',SIZE)
    result.paste(cell,(0,11))
    return result

def build():
    regions = json.loads((ROOT/'parts/semantic-regions.json').read_text())['poses']
    for directory in ('parts','masks','baked'):
        (ROOT/directory).mkdir(exist_ok=True)
    artifacts,recipes = [],{g:{'frames':[]} for g in ('A','B')}
    def save(image,path,**metadata):
        image.save(ROOT/path)
        artifacts.append({'path':path,'sha256':digest(ROOT/path),**metadata})
        return path
    def layer(name,path,hide=None,**extra):
        record = {'id':name,'source':path,'placement':{'mode':'full_frame','offset_px':[0,0]},**extra}
        if hide:
            record['hide_mask']=hide
        return record
    differences=[]
    for i,region in enumerate(regions):
        pose=f'run_west_{i}'
        original=Image.open(ROOT/f'registered/{pose}.png').convert('RGBA')
        sources={'A':original,'B':registered_sheet('run-west-b-v2',i)}
        near,far=polygon(region['near']),polygon(region['far'])
        far=ImageChops.subtract(far,near)
        arms=union(near,far)
        torso_roi=polygon(region['torso'])
        neck=Image.new('L',SIZE)
        nx0,ny0,nx1,ny1=region['neck']
        for y in range(ny0,ny1):
            for x in range(nx0,nx1):
                r,g,b,a=original.getpixel((x,y))
                if a and r>65 and r-g>=40 and g-b>=25:
                    neck.putpixel((x,y),255)
        # The original pose's own neck is never extracted from a garment source.
        near=ImageChops.subtract(near,neck)
        far=ImageChops.subtract(far,neck)
        arms=union(near,far)
        garment_roi=union(torso_roi,arms)
        protected_hands=union(*(polygon(p) for p in region['hands']))
        # Manual hand semantics override dark-edge colour adjacency near cuffs.
        cloth={g:ImageChops.subtract(cloth_mask(im,garment_roi,g),union(neck,protected_hands)) for g,im in sources.items()}
        torso_owner=ImageChops.subtract(cloth['A'],arms)
        base_owner=ImageChops.invert(union(arms,torso_owner))
        owners={'body_base':base_owner,'near_arm':near,'far_arm':far,'torso':torso_owner}
        for name,mask in owners.items():
            save(mask,f'masks/ownership_{i}_{name}.png',purpose='source_ownership',pose_id=pose,owner=name,source=f'registered/{pose}.png')
        body_path=save(cut(original,base_owner),f'parts/{pose}_body_base.png',owner='same_A_head_neck_pants_shoes',pose_id=pose)
        body_arms={}
        for side,mask in [('near',near),('far',far)]:
            body_mask=ImageChops.subtract(mask,cloth['A'])
            body_arms[side]=save(cut(original,body_mask),f'parts/{pose}_body_{side}.png',owner='same_A_arm_skin_and_hand',pose_id=pose)
        save(protected_hands,f'masks/protected_hands_{i}.png',purpose='same_A_hand_preservation',pose_id=pose)
        for g in ('A','B'):
            im=sources[g]
            full_source=f'sources/run-torso-{g.lower()}-v1.png'
            complete=registered_sheet(f'run-torso-{g.lower()}-v1',i)
            # Only real GPT complete cloth under arm-owned surfaces can fill.
            hidden=ImageChops.multiply(cloth_mask(complete,torso_roi,g),arms)
            visible=torso_owner if g=='A' else ImageChops.subtract(cloth[g],arms)
            hidden_path=save(hidden,f'masks/hidden_{g}_{i}.png',purpose='hidden_source_extraction',pose_id=pose,source=full_source,target=f'{g}_torso')
            torso=cut(complete,hidden)
            torso.alpha_composite(cut(im,visible))
            torso_path=save(torso,f'parts/{pose}_torso_{g}.png',owner=f'{g}_complete_torso',source=full_source,pose_id=pose)
            sleeves,coverage={},{ }
            current_arm_pixels=[]
            for side,owner in [('near',near),('far',far)]:
                sleeve_mask=ImageChops.multiply(cloth[g],owner)
                if g=='B':
                    sleeve_mask=ImageChops.subtract(sleeve_mask,protected_hands)
                sleeve=cut(im,sleeve_mask)
                sleeves[side]=save(sleeve,f'parts/{pose}_sleeve_{g}_{side}.png',owner=f'{g}_{side}_sleeve',pose_id=pose)
                cover=opaque(sleeve.getchannel('A'))
                coverage[side]=save(cover,f'masks/coverage_{g}_{i}_{side}.png',purpose='coverage',owner_part=f'{g}_{side}_sleeve',target_part=f'body_{side}',pose_id=pose)
                current_arm_pixels.append(opaque(cut(original,owner).getchannel('A')))
                current_arm_pixels.append(opaque(sleeve.getchannel('A')))
            # Hidden-fill pixels were explicitly declared occluded in this pose;
            # they remain stored complete but never leak through alpha gaps.
            occlusion=union(hidden,*current_arm_pixels)
            occlusion_path=save(occlusion,f'masks/occlusion_{g}_{i}_torso.png',purpose='current_occlusion',owner_parts=['visible_near_arm','visible_far_arm'],target_part=f'{g}_torso',pose_id=pose)
            layers=[layer('body_base',body_path),layer('far_body',body_arms['far'],coverage['far']),layer('far_sleeve',sleeves['far']),
                    layer('torso',torso_path,occlusion_path,hidden_source=full_source,hidden_mask=hidden_path),
                    layer('near_body',body_arms['near'],coverage['near']),layer('near_sleeve',sleeves['near'])]
            recipes[g]['frames'].append({'pose_id':pose,'action':'run','direction':'west','duration_ms':80,'layers':layers,'file':f'baked/{g}_{i}.png'})
            # Keep zero-alpha RGB payload, which normal alpha-over discards; visible art remains wholly layered.
            result=original.copy()
            result.putalpha(Image.new('L',SIZE))
            for record in layers:
                item=Image.open(ROOT/record['source']).convert('RGBA')
                if 'hide_mask' in record:
                    hide=Image.open(ROOT/record['hide_mask']).convert('L')
                    item.putalpha(ImageChops.multiply(item.getchannel('A'),ImageChops.invert(hide)))
                result.alpha_composite(item)
            if g=='B':
                allowed=union(cloth['A'],cloth['B'])
                allowed=ImageChops.subtract(allowed,protected_hands)
                save(allowed,f'masks/B_editable_{i}.png',purpose='garment_editable_only',pose_id=pose)
            save(result,f'baked/{g}_{i}.png',recipe=g,pose_id=pose)
            if g=='A':
                delta=ImageChops.difference(original,result)
                raw=delta.tobytes()
                differences.append({'pose_id':pose,'different_channels':sum(v!=0 for v in raw),'different_pixels':sum(any(raw[j:j+4]) for j in range(0,len(raw),4))})
    dependencies=['build_parts.py','test_parts.py','parts/semantic-regions.json','candidate.json','registration-config.json','sources/run-west-a-v4-assembled.png']
    dependencies += [f'registered/run_west_{i}.png' for i in range(4)]
    dependencies += [f'sources/{name}.png' for name in ('run-west-b-v2','run-torso-a-v1','run-torso-b-v1')]
    dependencies += [f'prompts/{name}.txt' for name in ('run-west-b-v2','run-torso-a-v1','run-torso-b-v1')]
    dependencies += [x['path'] for x in artifacts]
    inputs={path:digest(ROOT/path) for path in sorted(set(dependencies))}
    manifest={'schema_version':1,'template_id':'adult-standard-v1','motion_set_id':'run-west-proof-v1','action_id':'run','direction':'west',
              'canvas_px':[512,768],'root_anchor_px':[256,708],'display_scale':138/582,'inputs':inputs,'recipes':recipes,'artifacts':artifacts,
              'A_reconstruction':differences,'placement':'all full_frame at offset0; source sheets common whole-frame+11y only',
              'ownership_is_not_coverage':True,'hidden_scope':'Actual GPT complete shirt surfaces; no undressed universal body claimed',
              'review_status':'rework_required_B_waist_interface','user_accepted':False,'transparent_rgb_payload':'Seed original A RGB at zero alpha so invisible original pixel bytes remain intact.'}
    manifest['artifact_digest']=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    (ROOT/'parts-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'artifact_digest':manifest['artifact_digest'],'A_reconstruction':differences}))
    return manifest

if __name__=='__main__':
    build()
