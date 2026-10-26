"""Same contract as west proof. Extract/copy/reflect actual GPT art, no painting."""
from pathlib import Path
import hashlib,json,shutil
from PIL import Image,ImageChops,ImageDraw,ImageFilter
ROOT=Path(__file__).resolve().parent
WEST=ROOT.parent/'run-west-proof-v1'
SIZE=(512,768)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def poly(points):
    im=Image.new('L',SIZE);ImageDraw.Draw(im).polygon([tuple(p) for p in points],fill=255);return im
def union(*masks):
    out=Image.new('L',SIZE)
    for m in masks:out=ImageChops.lighter(out,m)
    return out
def cut(im,mask):
    out=im.copy();out.putalpha(ImageChops.multiply(im.getchannel('A'),mask));return out
def binary(mask):return mask.point(lambda a:255 if a else 0)
def reflect(im):
    out=Image.new(im.mode,im.size,0);out.paste(im.transpose(Image.Transpose.FLIP_LEFT_RIGHT),(1,0));return out
def cloth(im,roi,g):
    seed=Image.new('L',SIZE);edge=Image.new('L',SIZE)
    x0,y0,x1,y1=roi.getbbox()
    for y in range(y0,y1):
        for x in range(x0,x1):
            if not roi.getpixel((x,y)):continue
            r,gr,b,a=im.getpixel((x,y))
            if a<16:continue
            ok=(r>=175 and gr>=160 and b>=140 and r-gr<40 and gr-b<40) if g=='A' else (b>r+12 and b>gr+5)
            if ok:seed.putpixel((x,y),255)
            elif max(r,gr,b)<60:edge.putpixel((x,y),255)
    return union(seed,ImageChops.multiply(seed.filter(ImageFilter.MaxFilter(13)),edge))
def sheet(name,i):
    source=Image.open(ROOT/f'sources/{name}.png').convert('RGBA')
    if source.size!=(2048,768):raise ValueError(name)
    im=Image.new('RGBA',SIZE);im.paste(source.crop((i*512,0,(i+1)*512,768)),(0,11));return im
def compose(layers,seed):
    out=seed.copy();out.putalpha(Image.new('L',SIZE))
    for l in layers:
        item=Image.open(ROOT/l['source']).convert('RGBA')
        if 'hide_mask' in l:item.putalpha(ImageChops.multiply(item.getchannel('A'),ImageChops.invert(Image.open(ROOT/l['hide_mask']).convert('L'))))
        out.alpha_composite(item)
    return out
def main():
    for d in ['parts','masks','baked','sources/west']:(ROOT/d).mkdir(parents=True,exist_ok=True)
    artifacts=[];recipes={g:{'frames':[]} for g in ['A','B']};reconstruction=[]
    def save(im,path,**meta):
        (ROOT/path).parent.mkdir(parents=True,exist_ok=True);im.save(ROOT/path);artifacts.append({'path':path,'sha256':sha(ROOT/path),**meta});return path
    def layer(id,path,hide=None,**meta):
        r={'id':id,'source':path,'placement':{'mode':'full_frame','offset_px':[0,0]},**meta}
        if hide:r['hide_mask']=hide
        return r
    west=json.loads((WEST/'parts-manifest.json').read_text());shutil.copyfile(WEST/'parts-manifest.json',ROOT/'sources/west/parts-manifest.json')
    # Preserve all actual west component/mask source art and exact current bakes.
    for a in west['artifacts']:
        p=a['path'];dst=ROOT/'sources/west'/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(WEST/p,dst)
        if p.startswith(('parts/','masks/')):
            save(Image.open(dst),f'{p.split("/")[0]}/west/{p.split("/")[-1]}',purpose='copied west real layered asset',source_sha256=sha(dst))
            save(reflect(Image.open(dst)),f'{p.split("/")[0]}/east/{p.split("/")[-1]}',purpose='entire-frame reflection of west real layered asset',source_sha256=sha(dst))
    for name in ['run-torso-a-v1.png','run-torso-b-v1.png','run-west-b-v2.png']:
        shutil.copyfile(WEST/'sources'/name,ROOT/'sources/west'/name)
    for d in ['west','east']:
        for g in ['A','B']:
            for i,f in enumerate(west['recipes'][g]['frames']):
                layers=[]
                for original in f['layers']:
                    l=dict(original);l['source']=l['source'].replace('parts/','parts/'+d+'/')
                    if 'hide_mask' in l:l['hide_mask']=l['hide_mask'].replace('masks/','masks/'+d+'/')
                    if 'hidden_mask' in l:l['hidden_mask']=l['hidden_mask'].replace('masks/','masks/'+d+'/')
                    if 'hidden_source' in l:l['hidden_source']='sources/west/'+Path(l['hidden_source']).name
                    layers.append(l)
                src=Image.open(WEST/f['file']).convert('RGBA');result=src if d=='west' else reflect(src)
                path=save(result,f'baked/{g}_{d}_{i}.png',pose_id=f'run_{d}_{i}',recipe=g)
                recipes[g]['frames'].append({'pose_id':f'run_{d}_{i}','action':'run','direction':d,'duration_ms':80,'layers':layers,'file':path})
    for i,r in enumerate(json.loads((ROOT/'semantic-regions.json').read_text())['poses']):
        pose=r['pose_id'];original=Image.open(ROOT/f'registered/{pose}.png').convert('RGBA');sources={'A':original,'B':sheet('run-north-b-v1',i)}
        owners={side:poly(r[side]) for side in ['left','right']};owners['right']=ImageChops.subtract(owners['right'],owners['left']);arms=union(*owners.values());torso_roi=poly(r['torso'])
        neck=Image.new('L',SIZE)
        for y in range(r['neck'][1],r['neck'][3]):
            for x in range(r['neck'][0],r['neck'][2]):
                red,gr,b,a=original.getpixel((x,y))
                if a and red-gr>=40 and gr-b>=25:neck.putpixel((x,y),255)
        for side in owners:owners[side]=ImageChops.subtract(owners[side],neck)
        arms=union(*owners.values());hands=union(*(poly(p) for p in r['hands']))
        # Explicitly reviewed entire garment extent, including shoulder caps
        # beyond the arm/torso split lines; palette only assists this ROI.
        roi=poly([[50,330],[460,330],[460,550],[50,550]])
        clothes={g:ImageChops.subtract(cloth(im,roi,g),union(neck,hands)) for g,im in sources.items()}
        torso_owner=ImageChops.subtract(clothes['A'],arms);base_owner=ImageChops.invert(union(arms,torso_owner))
        save(base_owner,f'masks/{pose}_ownership_base.png',purpose='source_ownership',owner='same_A_head_neck_pants_shoes',pose_id=pose)
        base=save(cut(original,base_owner),f'parts/{pose}_body_base.png',purpose='same_A_head_neck_pants_shoes',pose_id=pose)
        body={}
        for side,owner in owners.items():
            save(owner,f'masks/{pose}_ownership_{side}.png',purpose='source_ownership',owner=f'body_{side}',pose_id=pose)
            body[side]=save(cut(original,ImageChops.subtract(owner,clothes['A'])),f'parts/{pose}_body_{side}.png',purpose='same_A_skin_hand',pose_id=pose)
        save(hands,f'masks/{pose}_protected_hands.png',purpose='same_A_hand_protection',pose_id=pose)
        for g in ['A','B']:
            complete=sheet(f'run-north-torso-{g.lower()}-v1',i)
            hidden=ImageChops.multiply(cloth(complete,torso_roi,g),arms)
            hidden_path=save(hidden,f'masks/{pose}_hidden_{g}.png',purpose='hidden_source_extraction',source=f'sources/run-north-torso-{g.lower()}-v1.png',target=f'{g}_torso',pose_id=pose)
            torso=cut(complete,hidden);torso.alpha_composite(cut(sources[g],torso_owner if g=='A' else ImageChops.subtract(clothes[g],arms)))
            torso_path=save(torso,f'parts/{pose}_torso_{g}.png',purpose='complete_GPT_torso',source=f'sources/run-north-torso-{g.lower()}-v1.png',pose_id=pose)
            sleeves={};coverage={}
            for side,owner in owners.items():
                sleeve=cut(sources[g],ImageChops.multiply(clothes[g],owner))
                sleeves[side]=save(sleeve,f'parts/{pose}_sleeve_{g}_{side}.png',purpose='GPT_sleeve',pose_id=pose)
                coverage[side]=save(binary(sleeve.getchannel('A')),f'masks/{pose}_coverage_{g}_{side}.png',purpose='coverage',owner_part=f'{g}_{side}_sleeve',target_part=f'body_{side}',pose_id=pose)
            occlusion=union(hidden,*(binary(cut(original,o).getchannel('A')) for o in owners.values()),*(binary(Image.open(ROOT/p).getchannel('A')) for p in sleeves.values()))
            occlusion_path=save(occlusion,f'masks/{pose}_occlusion_{g}_torso.png',purpose='current_occlusion',target=f'{g}_torso',pose_id=pose)
            far='right' if r['near']=='left' else 'left';near=r['near']
            layers=[layer('body_base',base),layer('far_body',body[far],coverage[far]),layer('far_sleeve',sleeves[far]),layer('torso',torso_path,occlusion_path,hidden_source=f'sources/run-north-torso-{g.lower()}-v1.png',hidden_mask=hidden_path),layer('near_body',body[near],coverage[near]),layer('near_sleeve',sleeves[near])]
            result=compose(layers,original);path=save(result,f'baked/{g}_north_{i}.png',pose_id=pose,recipe=g)
            recipes[g]['frames'].append({'pose_id':pose,'action':'run','direction':'north','duration_ms':80,'layers':layers,'file':path})
            if g=='A':reconstruction.append({'pose_id':pose,'different_channels':sum(v!=0 for v in ImageChops.difference(result,original).tobytes())})
            else:save(ImageChops.subtract(union(clothes['A'],clothes['B']),hands),f'masks/{pose}_B_editable.png',purpose='garment_editable_only',pose_id=pose)
    inputs={str(p.relative_to(ROOT)):sha(p) for d in ['sources','prompts','parts','masks','baked'] for p in sorted((ROOT/d).rglob('*')) if p.is_file()}
    for n in ['build_parts.py','semantic-regions.json','candidate.json']:inputs[n]=sha(ROOT/n)
    manifest={'schema_version':1,'template_id':'adult-standard-v1','motion_set_id':'run-four-directions-v1','action_id':'run','canvas_px':[512,768],'root_anchor_px':[256,708],'inputs':inputs,'recipes':recipes,'artifacts':artifacts,'A_reconstruction':reconstruction,'placement':'full_frame offset0; west copied; east whole-frame reflection+1x; north sheets whole-frame+11y','hidden_scope':'actual GPT complete shirt sources only; not universal undressed body','source_ownership_is_not_coverage':True,'user_accepted':False,'review_status':'candidate_pending_source_interface_checks'}
    manifest['artifact_digest']=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    (ROOT/'parts-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'A_reconstruction':reconstruction,'artifact_digest':manifest['artifact_digest']}))
if __name__=='__main__':main()
