"""Same-coordinate GPT slot extraction. No RGB painting or part transforms.

The existing approved pose masks supply exact interfaces; observed polygons
bound lower slots. Hidden torso remains complete, with occlusion only at bake.
"""
from pathlib import Path
import hashlib, json, shutil, sys
from PIL import Image, ImageDraw, ImageChops

SIZE=(512,768)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def poly(points):
    im=Image.new('L',SIZE);ImageDraw.Draw(im).polygon([tuple(p) for p in points],fill=255);return im

def project(d,name):
    src=d/'sources'/name;im=Image.open(src).convert('RGBA')
    if im.size!=(1024,1536):raise ValueError(f'wrong density {src}: {im.size}')
    dest=d/'projected'/name;im.resize(SIZE,Image.Resampling.NEAREST).save(dest);return Image.open(dest).convert('RGBA')

def binary(im): return im.point(lambda x:255 if x else 0)
def count(im): return sum(v>0 for v in im.getdata())
def difference(a,b):
    c=ImageChops.difference(a,b);out=Image.new('L',SIZE)
    for ch in c.split():out=ImageChops.lighter(out,ch)
    return binary(out)

# Manually observed shoe/ankle contours, native512 coordinates, not fitted boxes.
SHOES={
'idle_west_0':[[[158,641],[205,648],[214,664],[210,700],[164,707],[126,696],[125,670]],[[199,654],[254,655],[270,666],[270,705],[205,710],[164,697],[166,673]]],
'walk_west_0':[[[145,643],[203,665],[213,674],[211,711],[177,721],[115,698],[92,675],[100,651]],[[340,625],[369,637],[396,665],[390,684],[348,718],[300,719],[277,702],[278,680],[317,661]]],
'walk_west_1':[[[210,661],[274,664],[282,676],[282,711],[259,720],[179,721],[155,704],[156,683],[179,670]],[[332,583],[360,592],[389,614],[389,639],[365,677],[343,697],[320,686],[317,661],[329,630]]],
'walk_west_2':[[[148,646],[201,666],[214,679],[211,711],[179,722],[115,699],[92,679],[99,651]],[[340,624],[370,635],[397,663],[389,686],[349,718],[299,720],[276,701],[278,680],[317,661]]],
'walk_west_3':[[[210,660],[275,663],[282,676],[282,711],[260,720],[179,721],[156,703],[156,681],[180,669]],[[333,583],[361,594],[390,614],[389,640],[365,677],[343,696],[320,686],[317,661],[329,628]]],
'idle_east_0':[[[280,645],[310,641],[341,655],[359,676],[358,699],[320,704],[286,690]],[[191,658],[257,655],[288,665],[311,682],[310,706],[283,714],[205,714],[184,702],[183,676]]],
'run_east_0':[[[78,509],[95,514],[111,535],[103,573],[87,607],[70,627],[42,625],[30,606],[32,579],[46,539]],[[312,653],[365,639],[395,632],[423,639],[441,658],[444,682],[426,698],[350,716],[317,710],[306,690]]],
'run_east_1':[[[83,519],[106,523],[120,545],[113,580],[94,611],[74,631],[47,627],[34,609],[38,580],[55,539]],[[258,554],[285,566],[317,571],[342,590],[348,612],[331,630],[307,633],[272,620],[242,600],[239,580]]],
'run_east_2':[[[87,459],[115,460],[137,482],[137,501],[119,526],[87,542],[58,536],[45,517],[48,495],[66,474]],[[310,652],[364,637],[395,632],[421,640],[440,661],[441,684],[422,698],[348,715],[317,709],[304,689]]],
'run_east_3':[[[76,483],[101,485],[121,505],[121,525],[103,557],[83,579],[52,582],[30,562],[32,535],[47,501]],[[291,568],[327,576],[361,583],[386,602],[395,622],[378,643],[353,650],[314,639],[282,620],[270,600]]],
}

# Exact same-pose ankle interfaces, refined on independent slot board.
SHOES.update({
'run_east_1':[[[60,505],[132,517],[141,529],[131,577],[140,590],[140,640],[60,640]],[[275,549],[304,551],[356,563],[383,565],[410,585],[410,640],[270,640]]],
'run_east_2':[[[70,443],[154,443],[178,470],[177,481],[164,488],[150,497],[141,507],[138,522],[140,548],[70,548]],[[314,678],[324,675],[384,645],[390,632],[427,627],[464,647],[466,724],[310,724]]],
'run_east_3':[[[70,478],[143,477],[165,503],[139,551],[149,568],[130,605],[70,605]],[[296,575],[323,575],[380,581],[412,588],[445,608],[445,655],[296,655]]],
})

ANKLE_BANDS={
'idle_east_0':[[[278,638],[316,638],[316,660],[278,660]],[[195,650],[270,650],[270,670],[195,670]]],
'run_east_0':[[[92,528],[111,528],[111,575],[92,575]],[[320,635],[385,635],[385,663],[320,663]]],
'run_east_1':[[[128,528],[145,528],[145,581],[128,581]],[[300,548],[362,548],[362,570],[300,570]]],
'run_east_2':[[[140,482],[184,482],[184,523],[140,523]],[[324,633],[386,633],[386,670],[324,670]]],
'run_east_3':[[[137,501],[166,501],[166,552],[137,552]],[[320,575],[382,575],[382,590],[320,590]]],
}

def build(d):
    idx=json.loads((d/'references/pose-index.json').read_text()); originals=json.loads((d/'references/original-layer-index.json').read_text()); action=idx['action_id'];iswalk=action=='walk'; cfg={'coordinate_system':'native512x768; all parts full frame; no offsets or part fitting','poses':{}}
    frames=[];checks=[]
    for f in idx['frames']:
        p=f['pose_id']; original=Image.open(d/f['original']).convert('RGBA'); raw=project(d,p+'-outfit-v1.png'); torso_pose='walk_west_0' if p.startswith('walk_') else p;torso_name=torso_pose+('-complete-torso-v2.png' if p=='run_east_3' else '-complete-torso-v1.png');torso=project(d,torso_name); layers=next(x['layers'] for x in originals if x['pose_id']==p)
        label=Image.new('L',SIZE);newlayers=[];part_arrays={}
        for i,l in enumerate(layers):
            a=Image.open(d/l['source']).convert('RGBA');alpha=a.getchannel('A');visible=binary(alpha)
            if 'hide_mask' in l:visible=ImageChops.multiply(visible,ImageChops.invert(binary(Image.open(d/l['hide_mask']).convert('L'))))
            garment=('sleeve' in l['id'] or l['id'] in ['shirt_torso','torso'])
            if garment:
                istorso=l['id'] in ['shirt_torso','torso'];rgb=torso if istorso else raw
                b=rgb.copy();b.putalpha(alpha);part=f'parts/{p}-top-{i}.png';b.save(d/part);part_arrays[i+1]=b
                label.paste(i+1,(0,0),visible)
                newlayers.append({'id':l['id'],'slot':'top','file':part,'source':'projected/'+(torso_name if istorso else p+'-outfit-v1.png'),'ownership_alpha':l['source'],'occlusion_mask':l.get('hide_mask'),'offset_px':[0,0],'complete_source_no_hand_holes':istorso})
            else:label.paste(0,(0,0),visible)
        topvisible=binary(label);base=Image.open(d/layers[0]['source']).convert('RGBA');lowpoly=poly([[0,525 if iswalk or p.startswith('idle') else (440 if p=='run_east_2' else 480)],[512,525 if iswalk or p.startswith('idle') else (440 if p=='run_east_2' else 480)],[512,768],[0,768]])
        if p=='run_east_2':
            lower_contour=[[190,498],[206,511],[296,511],[335,555],[387,633],[418,629],[449,645],[452,681],[427,697],[355,713],[325,701],[312,671],[259,592],[237,575],[214,590],[184,584],[158,561],[137,527],[107,543],[86,529],[77,508],[91,485],[120,460],[151,449],[171,462],[188,486]];lowpoly=poly(lower_contour)
        lower=ImageChops.multiply(binary(base.getchannel('A')),lowpoly);lower=ImageChops.subtract(lower,topvisible)
        skin=Image.new('L',SIZE);skin.putdata([255 if r-g>=35 and g-b>=20 else 0 for r,g,b,a in original.getdata()]);lower=ImageChops.subtract(lower,skin)
        shoe=Image.new('L',SIZE)
        for points in SHOES[p]:shoe=ImageChops.lighter(shoe,poly(points))
        shoe=ImageChops.multiply(shoe,lower)
        pants_palette=Image.new('L',SIZE);pants_palette.putdata([255 if r-g<23 and g-b>=20 and r>50 else 0 for r,g,b,a in original.getdata()])
        band=Image.new('L',SIZE)
        for points in ANKLE_BANDS[p]:band=ImageChops.lighter(band,poly(points))
        shoe=ImageChops.subtract(shoe,ImageChops.multiply(band,pants_palette));pants=ImageChops.subtract(lower,shoe)
        cfg['poses'][p]={'top_envelope':[[50,350],[450,350],[450,575],[50,575]],'lower_envelope':[[0,525 if iswalk or p.startswith('idle') else (440 if p=='run_east_2' else 480)],[512,525 if iswalk or p.startswith('idle') else (440 if p=='run_east_2' else 480)],[512,768],[0,768]],'shoe_polygons':SHOES[p],'ankle_interface_polygons':ANKLE_BANDS[p],'ankle_boundary_palette_assist':'within manually observed interface only: r-g<23,g-b>=20,r>50 identifies old olive pants' ,'interface_source':'references/original-layer-index.json','top_exact_support':'original same-pose garment alpha; torso full before occlusion','skin_excluded_from_lower':True,'lower_exact_mask':'manual envelope intersect same-pose body-base alpha; run_east_2 folded-leg contour separately observed','lower_contour_override':lower_contour if p=='run_east_2' else None}
        owner=ImageChops.lighter(topvisible,pants if iswalk else shoe);out=original.copy()
        for lid,b in part_arrays.items():
            m=label.point(lambda x:255 if x==lid else 0);out.paste(b,(0,0),m)
            maskpath=f'masks/{p}-top-layer-{lid}.png';m.save(d/maskpath)
            next(x for x in newlayers if x['file']==f'parts/{p}-top-{lid-1}.png')['visible_mask']=maskpath
        out.paste(raw,(0,0),pants if iswalk else shoe);out.putalpha(original.getchannel('A'))
        for slot,mask,source in [('pants',pants,raw if iswalk else original),('shoes',shoe,original if iswalk else raw)]:
            a=source.copy();a.putalpha(ImageChops.multiply(mask,original.getchannel('A')));path=f'parts/{p}-{slot}.png';a.save(d/path);newlayers.insert(0,{'id':slot,'slot':slot,'file':path,'source':f'projected/{p}-outfit-v1.png' if (iswalk and slot=='pants') or (not iswalk and slot=='shoes') else f['original'],'offset_px':[0,0]})
        masks={}
        for slot,mask in [('top-visible',topvisible),('pants',pants),('shoes',shoe),('changed-clothing',owner)]:
            path=f'masks/{p}-{slot}.png';mask.save(d/path);masks[slot]=path
        body=original.copy();allslots=ImageChops.lighter(topvisible,ImageChops.lighter(pants,shoe));body.putalpha(ImageChops.multiply(original.getchannel('A'),ImageChops.invert(allslots)));bodypath=f'parts/{p}-shared-body.png';body.save(d/bodypath)
        alpha_path=f'masks/{p}-frame-alpha.png';original.getchannel('A').save(d/alpha_path)
        file=f'baked/{p}.png';out.save(d/file);diff=difference(out,original)
        report={'pose_id':p,'changed_pixels':count(diff),'non_clothing_RGBA_diff':count(ImageChops.subtract(diff,owner)),'alpha_diff':count(difference(out.getchannel('A').convert('RGBA'),original.getchannel('A').convert('RGBA'))),'top_pixels':count(topvisible),'pants_pixels':count(pants),'shoe_pixels':count(shoe),'source_rgb_sampling':'same coordinate; no RGB arithmetic'};checks.append(report)
        rec={'pose_id':p,'duration_ms':f['duration_ms'],'file':file,'sha256':sha(d/file),'source':f'sources/{p}-outfit-v1.png','layers':newlayers,'masks':masks,'shared_body':bodypath,'frame_alpha':alpha_path,'original_layer_order':layers,'composition':'same-coordinate slot ownership; original per-pose arm depth; preserve original alpha and all non-owner RGBA'}
        if f.get('idle'):idle=rec|{'canvas_px':list(SIZE),'root_anchor_px':[256,708],'display_scale':138/582}
        else:frames.append(rec)
    write(d/'ownership.json',cfg);write(d/'evidence/pixel-audit.json',checks)
    spec={'schema_version':1,'template_id':'adult-standard-v1','action_id':action,'direction':idx['direction'],'recipe':{'id':('navy-stripes-denim-original-shoes' if iswalk else 'brick-cable-original-pants-buckle-shoes'),'slots':{'top':'top03' if iswalk else 'top04','pants':'pants02' if iswalk else 'original-olive-pants-v1','shoes':'original-brown-shoes-v1' if iswalk else 'shoes04'}},'canvas_px':list(SIZE),'root_anchor_px':[256,708],'display_scale':138/582,'source_density_scale_vs_idle':1,'frames':frames,'idle':idle,'status':'sampled-not-exhaustive','native_checked':False,'user_accepted':False,'capability_scope':'one fixed sampled recipe / direction / four poses and matching idle; no exhaustive wardrobe or alternate-body claim','projection':idx['projection'],'inputs':{}}
    for pth in sorted(d.rglob('*')):
        if pth.is_file() and pth.name not in ['sample.json','README.md','implementation-report.md'] and '__pycache__' not in str(pth):spec['inputs'][str(pth.relative_to(d))]=sha(pth)
    write(d/'sample.json',spec)
    return checks

if __name__=='__main__':
    print(json.dumps(build(Path(sys.argv[1]).resolve()),indent=2))
