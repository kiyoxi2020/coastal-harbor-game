from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def record(p):
    im=Image.open(p).convert('RGBA');alpha=im.getchannel('A').point(lambda a:255 if a>=128 else 0)
    box=alpha.crop((0,0,512,345)).getbbox()
    return {'path':str(p.relative_to(ROOT.parents[4])),'sha256':sha(p),'opaque_bbox_px':list(alpha.getbbox()),'head_band_bbox_px':list(box),'head_band_width_px':box[2]-box[0]}
def main():
    rows=[];board=Image.new('RGB',(1250,450),(45,50,54));draw=ImageDraw.Draw(board)
    for row,d in enumerate(['south','north']):
        idle=ROOT.parent/f'locomotion-v1/registered/idle_{d}_0.png'
        entries=[record(idle)]+[record(ROOT/f'registered/run_{d}_{i}.png') for i in range(4)]
        baseline=entries[0]['head_band_width_px']
        for e in entries[1:]:e['width_ratio_to_idle']=e['head_band_width_px']/baseline
        rows.append({'direction':d,'approved_idle':entries[0],'run':entries[1:],'status':'identity_proportions_pending_review_with_rework_risk'})
        for col,e in enumerate(entries):
            p=ROOT.parents[4]/e['path'];im=Image.open(p).convert('RGBA');im=im.resize((122,182),Image.Resampling.NEAREST)
            x=col*250+64;y=row*225+24;board.paste(im,(x,y),im)
            label=f'{d} '+('approved idle' if col==0 else f'run{col-1}')+f' / band {e["head_band_width_px"]}px'
            draw.text((col*250+8,row*225+208),label,fill=(235,235,235))
    report={'roi_px':[0,0,512,345],'threshold':'alpha>=128','meaning':'width of upper silhouette band including ears; not isolated skull/joint measurement; arms below this band except upper shoulder/hand tips do not set horizontal extrema in reviewed images','native_display_scale':0.23711340206185566,'rows':rows,'interpretation':'south run upper silhouette about12.5-12.8% wider than approved idle, north9.4-10.5% wider. Source proportions cannot be declared matched from smaller thumbnail review. Do not explain away this measured head-band width as full-body pose projection. Candidate remains technical/native review only; identity/proportion visual review and possible source rework required. No local head scaling permitted.'}
    (ROOT/'evidence/geometry-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');board.save(ROOT/'evidence/scale-comparison.png')
if __name__=='__main__':main()
