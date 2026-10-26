"""Root-aligned uniform nearest diagnostic only; never used as art."""
from pathlib import Path
import hashlib,json,sys
from PIL import Image,ImageDraw
SCRIPT=Path(__file__).resolve();COLOR=SCRIPT.parent.parent;FARMING=COLOR.parent.parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build(direction):
 if direction not in ['south','north']:raise ValueError('unassigned direction')
 root=COLOR/(direction+'-B');items=[];bindings={}
 for action in ['water','harvest']:
  p=FARMING/action/(direction+'-B');c=json.loads((p/'candidate.json').read_text());f=c['frames'][0];items.append((action+' approved',p/f['file'],c['root_anchor_px']));bindings[action]={'candidate_sha256':sha(p/'candidate.json'),'texture_sha256':sha(p/f['file'])}
 c=json.loads((root/'candidate.json').read_text());bindings['hoe']={'candidate_sha256':sha(root/'candidate.json'),'texture_sha256':[f['sha256']for f in c['frames']]}
 for f in c['frames']:items.append(('hoe '+f['phase'],root/f['file'],c['root_anchor_px']))
 heights=[260,430,260,430];board=Image.new('RGB',(1600,sum(heights)));draw=ImageDraw.Draw(board)
 for row,(factor,bg) in enumerate([(1,(232,229,216)),(2,(232,229,216)),(1,(36,45,57)),(2,(36,45,57))]):
  y0=sum(heights[:row]);draw.rectangle((0,y0,1600,y0+heights[row]),fill=bg)
  for i,(label,path,anchor)in enumerate(items):
   scale=138/1164*factor;im=Image.open(path).convert('RGBA');im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST);x=round(i*266+128-anchor[0]*scale);y=round(y0+heights[row]-(55 if factor==1 else 80)-anchor[1]*scale);board.paste(im,(x,y),im);draw.text((i*266+10,y0+5),f'{factor}x '+label,fill=(10,10,10)if row<2 else(245,245,245))
 target=root/'evidence/approved-color-comparison.png';board.save(target);bindings.update(comparison_sha256=sha(target),tool_sha256=sha(SCRIPT),scope='Static CPU diagnostic 1x/2x nearest, common pixel density and recorded roots; not native evidence or new visual acceptance.')
 (root/'evidence/approved-comparison-bindings.json').write_text(json.dumps(bindings,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':build(sys.argv[1])
