"""Generate a file://-friendly review page from the actual baked manifest."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
HEADER='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>四向步行与换衣评审</title><style>
body{font:16px system-ui;background:#202830;color:#eee;margin:32px}button,select,input{font:inherit;margin:8px;padding:8px}canvas{image-rendering:pixelated;background:#e5e0d2;border-radius:8px}section{display:flex;gap:24px;flex-wrap:wrap}small{color:#b9c4ce}a{color:#a4d7ff}</style>
<h1>四向步行与站姿 · 两套上衣</h1><p>75%速度已认可。此页为新素材评审候选，尚不代表完整人体发布。</p>
<label>动作 <select id="action"><option value="walk">行走</option><option value="idle">站立</option></select></label>
<label>方向 <select id="direction"><option value="south">南</option><option value="west">西</option><option value="east">东</option><option value="north">北</option></select></label>
<button id="pause">暂停</button><button id="step">下一帧</button><label>速度 <input id="speed" type="range" min="50" max="100" value="75"><span id="rate">75%</span></label><button id="background">明暗背景</button>
<section><div><p>奶油短袖 A</p><canvas id="A" width="384" height="576"></canvas></div><div><p>蓝色长袖 B</p><canvas id="B" width="384" height="576"></canvas></div></section><p id="state"></p>
<p><a href="launch-game-trial.command">启动港口试玩（macOS）</a> · WASD / 方向键移动，1 / 2 换衣，R 回起点。</p>
<p><small>预览按源图统一缩放，不调整局部部件。游戏中人物高度约138渲染像素；本页放大检查。固定裤鞋；完整关节冻结、严格脚点误差、跑步和农事动作仍待完成。</small></p><small id="digest"></small><script>const manifest='''
SCRIPT=''';
const elements=Object.fromEntries(['action','direction','pause','step','speed','rate','background','state','digest'].map(id=>[id,document.getElementById(id)]));
let elapsed=0,playing=true,last=performance.now(),dark=false;
const images={};for(const g of ['A','B']){images[g]={};for(const f of manifest.recipes[g].frames){const im=new Image();im.src='baked/'+f.file;images[g][f.pose_id]=im;}}
function clip(){return manifest.actions[elements.action.value].directions[elements.direction.value]}
function duration(id){return manifest.frames.find(f=>f.pose_id===id).duration_ms}
function current(){let t=elapsed%clip().reduce((v,id)=>v+duration(id),0);for(const id of clip()){if(t<duration(id))return id;t-=duration(id)}return clip()[0]}
function draw(now){if(playing)elapsed+=(now-last)*Number(elements.speed.value)/100;last=now;const id=current();for(const g of ['A','B']){const c=document.getElementById(g),ctx=c.getContext('2d');ctx.clearRect(0,0,c.width,c.height);ctx.imageSmoothingEnabled=false;const im=images[g][id];if(im.complete&&im.naturalWidth)ctx.drawImage(im,0,0,c.width,c.height)}elements.state.textContent=id+' · '+(duration(id)/(Number(elements.speed.value)/100)).toFixed(1)+' ms/帧';requestAnimationFrame(draw)}
elements.pause.onclick=()=>{playing=!playing;elements.pause.textContent=playing?'暂停':'播放'};
elements.step.onclick=()=>{playing=false;elements.pause.textContent='播放';let i=(clip().indexOf(current())+1)%clip().length;elapsed=clip().slice(0,i).reduce((v,id)=>v+duration(id),0)};
for(const e of [elements.action,elements.direction])e.onchange=()=>elapsed=0;
elements.speed.oninput=()=>elements.rate.textContent=elements.speed.value+'%';
elements.background.onclick=()=>{dark=!dark;for(const g of ['A','B'])document.getElementById(g).style.background=dark?'#15202b':'#e5e0d2'};
elements.digest.textContent='artifact '+manifest.artifact_digest;requestAnimationFrame(draw);
</script></html>'''
if __name__=='__main__':
 m=json.loads((ROOT/'baked/export-manifest.json').read_text());(ROOT/'review.html').write_text(HEADER+json.dumps(m,ensure_ascii=False).replace('</','<\\/')+SCRIPT)
 print('Review page binds',m['artifact_digest'])
