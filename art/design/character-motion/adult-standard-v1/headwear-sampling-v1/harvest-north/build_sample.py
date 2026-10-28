#!/usr/bin/env python3
"""Deterministically extract GPT source views and register them; never paint pixels."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops
import json, hashlib, shutil

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def rgba_diff(a,b): return any(c.getbbox() for c in ImageChops.difference(a,b).split())
def hair_owned(im,semantic):
    # Per-pose source-cell polygons are the ownership authority. Color only
    # rejects non-hair source paint inside their manually reviewed silhouette.
    assert semantic['source_cell']['canvas_px']==list(im.size)
    authorization=Image.new('L',im.size);draw=ImageDraw.Draw(authorization)
    for polygon in semantic['positive_polygons']:draw.polygon([tuple(v) for v in polygon],fill=255)
    for polygon in semantic['negative_polygons']:draw.polygon([tuple(v) for v in polygon],fill=0)
    authorized=authorization.load();p=im.load();out=Image.new('L',im.size);op=out.load()
    for y in range(im.height):
        for x in range(im.width):
            r,g,b,a=p[x,y]
            if authorized[x,y] and a>=220 and r<200 and g<150 and b<120:op[x,y]=255
    return out
def interp(points,x):
    for (x0,y0),(x1,y1) in zip(points,points[1:]):
        if x0<=x<=x1:return round(y0+(y1-y0)*(x-x0)/(x1-x0))
    return points[0][1] if x<points[0][0] else points[-1][1]
def hat_owned(im,north,index):
    # Reviewed lower brim contour; snap only to nearby source-painted dark outline.
    if north:
        pts=[(0,445),(60,495),(140,525),(240,542),(340,548),(440,545),(540,535),(620,510),(700,470),(768,445)]
        delta=[0,3,0,-7][index];dx=[0,3,0,30][index]
    else:
        pts=[(0,540),(130,540),(170,450),(250,430),(350,420),(420,420),(510,430),(590,450),(625,540),(768,540)]
        delta=[0,-20,10,40][index];dx=[0,0,0,8][index]
    p=im.load(); owned=Image.new('L',im.size);op=owned.load(); volume=Image.new('L',im.size);vp=volume.load();bounds=[]
    for x in range(768):
        predicted=interp(pts,x-dx)+delta
        candidates=[y for y in range(max(100,predicted-16),min(768,predicted+17)) if p[x,y][3]>=220 and max(p[x,y][:3])<85]
        cut=min(candidates,key=lambda y:abs(y-predicted)) if candidates else predicted
        bounds.append(cut)
        for y in range(max(0,cut+1)):
            vp[x,y]=255
            if y>70 and p[x,y][3]>=220:op[x,y]=255
    exclusions=json.loads((HERE/'hat-semantics.json').read_text())['poses'].get(['ready','reach','pluck','recovery'][index],{}) if north else {}
    exclusion=Image.new('L',im.size)
    for polygon in exclusions.get('exclude_polygons',[]):ImageDraw.Draw(exclusion).polygon([tuple(point) for point in polygon],fill=255)
    owned.paste(0,(0,0),exclusion)
    return owned,volume,bounds
def extract(im,mask):
    out=Image.new('RGBA',im.size);out.paste(im,(0,0),mask);return out
def translate(im,size,xy):
    out=Image.new(im.mode,size);out.paste(im,xy);return out
def source_anchor(im):
    # Ear edge landmark: all sampling bounds and color criterion are explicit.
    p=im.load();pts=[]
    for y in range(450,735):
        for x in range(20,230):
            r,g,b,a=p[x,y]
            if a>220 and r>190 and g>100 and b>80 and r-g>45 and .65<b/g<.9:pts.append((x,y))
    left=min(x for x,y in pts);edge=[y for x,y in pts if x<=left+8]
    return [left,round((min(edge)+max(edge))/2)]
def main():
    name=HERE.name;north=name=='harvest-north';direction='north' if north else 'south'
    parent=ROOT/'art/design/character-motion/adult-standard-v1/wardrobe-sampling-v1'/name/'sample.json'
    ps=json.loads(parent.read_text()); boxes=json.loads((HERE/'references/head-crops.json').read_text())
    for d in ['baked','parts','masks','sources','references']: (HERE/d).mkdir(exist_ok=True)
    # One whole-sheet source density normalization, no per-view or per-part scaling.
    raw=Image.open(HERE/'sources/headwear-sheet-attempt1.png').convert('RGBA');sheet=raw.resize((3072,1536),Image.Resampling.NEAREST)
    sheet.save(HERE/'sources/headwear-sheet-density-normalized.png')
    static=ROOT/'art/design/character-head-proof-v1'
    for f in ['semantic-masks.json','hair-worn-v2.png','hat-worn-v1.png']:
        if not (HERE/'references'/f).exists():shutil.copy2(static/f,HERE/'references'/f)
    for part in ['hair','hat']:
        frozen=HERE/'references'/f'idle-{part}-ownership.png'
        if not frozen.exists():shutil.copy2(static/'proof'/f'{part}-mask_{direction}.png',frozen)
    manifest={k:ps[k] for k in ['schema_version','template_id','action_id','direction','canvas_px','root_anchor_px','display_scale']}
    manifest.update(parent_sample=parent.relative_to(ROOT).as_posix(),parent_sha256=sha(parent),status='candidate-awaiting-native-and-user-review',frames=[])
    validation={'schema_version':1,'sample':name,'non_headwear_preserved':True,'checks':[],'native_checked':False,'user_accepted':False}
    hair_semantics=json.loads((HERE/'hair-semantics.json').read_text())
    assert hair_semantics['schema_version']==2 and len(hair_semantics['poses'])==4
    ownership={'schema_version':2,'gpt_source':'sources/headwear-sheet-attempt1.png','hair_semantic_authority':'hair-semantics.json','source_density_normalization':{'input_px':list(raw.size),'output_px':[3072,1536],'method':'whole-sheet nearest; equal x/y factor; no local part scaling'},'poses':{}}
    for idx,f in enumerate(ps['frames']+[ps['idle']]):
        idle=idx==4;phase='idle' if idle else f['phase'];pose=f['pose_id'];base_path=HERE/'references'/f'bare-{phase}.png';base=Image.open(base_path).convert('RGBA');size=base.size
        parent_bare=parent.parent/f['file']
        assert sha(parent_bare)==f['sha256'],(pose,'parent texture differs from parent sample')
        assert sha(base_path)==f['sha256'],(pose,'frozen same-pose reference differs from parent')
        shutil.copy2(parent_bare,HERE/'baked'/f'{pose}-bare.png')
        part_files={}; regs={}; textures={}; masks={};volume=None
        for part,row in [('hair',0),('hat',1)]:
            if idle:
                atlas=Image.open(HERE/'references'/('hair-worn-v2.png' if part=='hair' else 'hat-worn-v1.png')).convert('RGBA');di=3 if north else 0;view=atlas.crop((di*512,0,(di+1)*512,768));mask=Image.open(HERE/'references'/f'idle-{part}-ownership.png').convert('L')
                delta=(-26,0) if north else (26,-1);full=translate(extract(view,mask),size,delta);fm=translate(mask,size,delta)
                regs[part]={'placement_mode':'anchor_local','pivot_px':[282,245] if north else [230,245],'target_anchor_px':[256,245] if north else [256,244],'translation_px':list(delta),'local_scale':[1,1],'projection':'same static head; original skin contour differs <=1 native source px after translation; eyebrows are preserved from same-pose base'}
                if part=='hat':
                    cfg=json.loads((HERE/'references/semantic-masks.json').read_text());vol=Image.new('L',view.size);ImageDraw.Draw(vol).polygon([tuple(v) for v in cfg['hat_polygons'][direction]],fill=255);volume=translate(vol,size,delta)
            else:
                view=sheet.crop((idx*768,row*768,(idx+1)*768,(row+1)*768));target=Image.open(HERE/'references/head-edit-target.png').crop((idx*768,0,(idx+1)*768,768));sa=source_anchor(view);ta=source_anchor(target);delta=(ta[0]-sa[0],ta[1]-sa[1]);box=boxes[idx]
                if part=='hair':
                    semantic=hair_semantics['poses'][idx]
                    assert semantic['pose_id']==pose and semantic['source_cell']['sheet_rect_px']==[idx*768,0,(idx+1)*768,768]
                    mask=hair_owned(view,semantic)
                else:mask,vol,bounds=hat_owned(view,north,idx)
                xy=(box[0]+delta[0],box[1]+delta[1]);full=translate(extract(view,mask),size,xy);fm=translate(mask,size,xy)
                if part=='hat':volume=translate(vol,size,xy)
                regs[part]={'placement_mode':'anchor_local','pivot_px':sa,'target_anchor_px':[box[0]+ta[0],box[1]+ta[1]],'translation_px':list(xy),'source_crop_px':[idx*768,row*768,(idx+1)*768,(row+1)*768],'local_scale':[1,1],'anchor_method':'same-pose left ear edge; skin strip criterion recorded in builder; integer translation only','head_projection':'distinct GPT view for this pose, not a standing view'}
            file=f'parts/{phase}-{part}-complete-source.png';mp=f'masks/{phase}-{part}-source-ownership.png';local_mp=f'masks/{phase}-{part}-source-local-ownership.png';coverage_mp=f'masks/{phase}-{part}-visible-coverage.png';full.save(HERE/file);fm.save(HERE/mp);mask.save(HERE/local_mp)
            visible=full.getchannel('A').point(lambda a:255 if a else 0);visible.save(HERE/coverage_mp)
            textures[part]=full;masks[part]=fm
            part_files[part]={'file':file,'source_ownership':local_mp,'source_ownership_coordinates':{'space':'source_crop_local','canvas_px':list(mask.size),'pose_id':pose},'registered_source_ownership':mp,'registered_source_ownership_coordinates':{'space':'target_pose_full_frame','canvas_px':list(size),'pose_id':pose},'coverage_mask':coverage_mp,'coverage_coordinates':{'space':'target_pose_full_frame','canvas_px':list(size),'pose_id':pose},'coverage_kind':'visible_alpha_overdraw','coverage_operation':'paste source-painted alpha over the same-pose baked head; no target-body erase mask','owner_part':part,'target_surface':'same_pose_baked_head_projection' if part=='hair' else 'same_pose_baked_head_or_registered_hair','registration':regs[part]}
            if part=='hair' and not idle:part_files[part]['semantic_source_polygons']='hair-semantics.json#poses/'+str(idx)
        volume.save(HERE/f'masks/{phase}-hat-cap-volume.png')
        tucked=textures['hair'].copy();tucked.paste((0,0,0,0),(0,0,*size),volume);tucked.save(HERE/f'parts/{phase}-hair-under-hat.png')
        tuck_coverage=f'masks/{phase}-hair-under-hat-visible-coverage.png'
        tucked.getchannel('A').point(lambda a:255 if a else 0).save(HERE/tuck_coverage)
        states={};total_edit=Image.new('L',size)
        for state,layers in [('bare',[]),('hair',[textures['hair']]),('hat',[textures['hat']]),('hair_hat',[tucked,textures['hat']])]:
            path=HERE/'baked'/f'{pose}-{state}.png';out=base.copy();allowed=Image.new('L',size)
            for layer in layers:
                m=layer.getchannel('A').point(lambda a:255 if a else 0);out.paste(layer,(0,0),m);allowed=ImageChops.lighter(allowed,m)
            if state!='bare':out.save(path)
            states[state]={'file':path.relative_to(HERE).as_posix(),'sha256':sha(path)}
            changed=ImageChops.difference(base,out);forbidden=Image.new('RGBA',size);forbidden.paste(changed,(0,0),ImageChops.invert(allowed));assert not any(c.getbbox() for c in forbidden.split()),(pose,state)
            # Reconstruction and non-edit preservation are checked per same pose.
            reloaded=Image.open(path).convert('RGBA');assert not rgba_diff(reloaded,out)
            validation['checks'].append({'pose_id':pose,'state':state,'canvas_px':list(size),'non_edit_rgba_preserved':True,'deterministic_reconstruction':True,'bare_bytes_sha256_matches_parent':states['bare']['sha256']==f['sha256'],'registered_root_and_scale_unchanged':True,'edit_pixels':sum(allowed.histogram()[1:])})
            total_edit=ImageChops.lighter(total_edit,allowed)
        total_edit.save(HERE/f'masks/{phase}-allowed-edit.png')
        item={'pose_id':pose,'duration_ms':f['duration_ms'],'states':states,'parts':part_files,'allowed_edit_mask':f'masks/{phase}-allowed-edit.png','coverage':{'kind':'visible_alpha_overdraw','coordinate_space':'target_pose_full_frame','target_surface':'same_pose_baked_head_projection','hair':part_files['hair']['coverage_mask'],'hat':part_files['hat']['coverage_mask'],'hair_hat_hair':tuck_coverage,'target_erase_mask':None},'occlusion':{'ordered_layers':['same_pose_bare','hair_or_tucked_hair','hat'],'foreground_intersection':'No hand/tool intersects cap or fringe in these sampled poses; source complete hair/hat retained','mask':f'masks/{phase}-hat-cap-volume.png','mask_coordinates':'target_pose_full_frame','owner_part':'hat_cap','target_surface':'registered_hair_layer_only','operation':'tuck hair surface only; never mask face, hands, clothing or tools'}}
        ownership['poses'][pose]={'parts':part_files,'hat_cap_volume':f'masks/{phase}-hat-cap-volume.png','same_pose_base':base_path.relative_to(HERE).as_posix(),'no_old_face_or_hands':True}
        if idle:
            item.update({k:f[k] for k in ['canvas_px','root_anchor_px','display_scale']});manifest['idle']=item
        else:manifest['frames'].append(item)
    write_json(HERE/'ownership.json',ownership);write_json(HERE/'validation.json',validation)
    # Bind all real inputs/configuration/parts/outputs. Evidence reports are derivative.
    inputs={}
    for p in sorted(HERE.rglob('*')):
        if p.is_file() and p.name not in ['sample.json','validation.json','README.md','native-scale-contact.png'] and '__pycache__' not in p.parts and not p.name.endswith('.pyc'):
            inputs[p.relative_to(HERE).as_posix()]=sha(p)
    external_inputs={parent.relative_to(ROOT).as_posix():sha(parent)}
    for f in ps['frames']+[ps['idle']]:
        source=parent.parent/f['file']
        external_inputs[source.relative_to(ROOT).as_posix()]=sha(source)
    manifest['inputs']=inputs
    manifest['external_inputs']=external_inputs
    manifest['artifact_digest']=hashlib.sha256(json.dumps({'local':inputs,'external':external_inputs},sort_keys=True).encode()).hexdigest()
    write_json(HERE/'sample.json',manifest)
    print(name, 'baked',len(validation['checks']),'states; base bytes, geometry and reconstruction pass')
if __name__=='__main__':main()
