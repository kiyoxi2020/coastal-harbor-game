"""Derived review only. Never modifies source or registered raster pixels."""
from pathlib import Path
import json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
def build():
 c=json.loads((ROOT/'candidate.json').read_text());scale=c['display_scale'];canvas=tuple(c['canvas_px']);root=c['root_anchor_px']
 for mult in [1,2]:
  cellw=round(canvas[0]*scale*mult)+30;cellh=round(canvas[1]*scale*mult)+45
  board=Image.new('RGB',(cellw*4,cellh*2));draw=ImageDraw.Draw(board)
  for row,color in enumerate([(232,229,216),(36,45,57)]):
   draw.rectangle((0,row*cellh,board.width,(row+1)*cellh),fill=color)
   for i,f in enumerate(c['frames']):
    for g in ['A','B']:
     col=i*2+(g=='B');dx,dy=f['whole_frame_translation_px']
     if g=='A':
      source=Image.open(ROOT/('references/approved-hoe-'+f['phase']+'-A.png')).convert('RGBA')
      refcfg=json.loads((ROOT/'references/approved-hoe-v4-registration-config.json').read_text());ref=next(v for v in refcfg['frames']if v['phase']==f['phase']);dx,dy=[root[j]-ref['source_root_px'][j]for j in [0,1]]
      src=Image.new('RGBA',canvas);src.paste(source,(dx,dy))
     else:src=Image.open(ROOT/f['file']).convert('RGBA')
     size=tuple(round(v*scale*mult)for v in canvas);src=src.resize(size,Image.Resampling.NEAREST)
     x=col*cellw+15;y=row*cellh+25;board.paste(src,(x,y),src)
     ink=(10,10,10)if row==0 else(240,240,240);draw.text((col*cellw+10,row*cellh+7),f['phase']+' '+g+' '+str(mult)+'x',fill=ink)
     rx=x+round(root[0]*scale*mult);ry=y+round(root[1]*scale*mult)
     draw.line((rx-3,ry,rx+3,ry),fill=(220,60,60));draw.line((rx,ry-3,rx,ry+3),fill=(220,60,60))
  board.save(ROOT/f'evidence/pose-comparison-{mult}x.png')
 cards=[]
 for f in c['frames']:
  cards.append('<figure><figcaption>'+f['phase']+' · B · '+f['pose_id']+'</figcaption><img src="'+f['file']+'" style="width:'+str(canvas[0]*scale*2)+'px;height:'+str(canvas[1]*scale*2)+'px"></figure>')
 (ROOT/'review.html').write_text('''<!doctype html><html lang="zh"><meta charset="utf-8"><title>西向锄地长袖B两关键姿态</title><style>body{font:16px sans-serif;background:#e8e5d8;color:#182b39;margin:24px}button,a{margin-right:12px}main{display:flex;gap:20px}img{image-rendering:pixelated}figure{margin:0}figcaption{padding:10px}body.dark{background:#242d39;color:#eee}</style><h1>西向锄地长袖B：ready/contact</h1><p>完整GPT姿态诊断，未分层，未用户认可。缺lift/recovery，不播放成完整动作循环。显示为既定密度2倍，无bbox拟合。</p><button onclick="document.body.classList.toggle('dark')">明暗背景</button><a href="README.md">说明</a><a href="measurements.json">测量</a><main>'''+''.join(cards)+'''</main><p>红色root十字仅见对照证据板；HTML展示完整原RGBA。</p><a href="evidence/pose-comparison-1x.png">1x A/B对照板</a><a href="evidence/pose-comparison-2x.png">2x A/B对照板</a></html>''')
if __name__=='__main__':build()
