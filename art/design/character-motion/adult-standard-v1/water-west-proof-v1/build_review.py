"""Build a standalone review page from exact registered GPT frames."""
from pathlib import Path
import base64
import json

ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / 'candidate.json').read_text())
frames = ['data:image/png;base64,' + base64.b64encode((ROOT / f['file']).read_bytes()).decode() for f in data['frames']]
payload = json.dumps({'images': frames, 'durations': [f['duration_ms'] for f in data['frames']], 'digest': data['artifact_digest'], 'canvas': data['canvas_px']})
html = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>西向浇水完整帧候选</title>
<style>body{font:15px system-ui;background:#242d31;color:#eee;margin:30px}button,input{margin:8px}canvas{image-rendering:pixelated;border:1px solid #888}p{max-width:880px}.row{display:flex;gap:24px;flex-wrap:wrap}.panel{display:grid;gap:8px}code{word-break:break-all}</style>
<h1>西向浇水 · 未获用户批准的完整帧候选</h1><p>同一成年母版，奶油短袖、橄榄裤、棕鞋。只评审提壶→倾倒→出水→回收；没有接入玩法、分层换装或生产发布。</p>
<p>原生目标按源像素138/582显示（扩宽画布约182×182 CSS像素），并列4倍诊断。明暗背景均来自同一纹理。扩宽画布根点[384,708]；该候选人物高约644源像素、显示约153像素，比walk基准约138像素偏大，比例仍需返工。单次动作会停在末帧；默认重复只供首尾检查。</p>
<button id="play">暂停</button><button id="restart">重播</button><label><input id="repeat" type="checkbox" checked>重复评审</label><label>速度<input id="speed" type="range" min="25" max="150" value="100"><span id="rate">100%</span></label><label>停帧<input id="frame" type="range" min="0" max="3" value="0"></label><span id="state"></span>
<div class="row"><div class="panel"><b>原生比例 · 明</b><canvas id="light" width="183" height="183"></canvas></div><div class="panel"><b>原生比例 · 暗</b><canvas id="dark" width="183" height="183"></canvas></div><div class="panel"><b>4倍诊断</b><canvas id="large" width="732" height="732"></canvas></div></div>
<p>所有帧：</p><div id="all" class="row"></div><p>artifact <code id="digest"></code></p>
<script>const DATA=__PAYLOAD__;let images=DATA.images.map(src=>{let i=new Image;i.src=src;return i}),playing=true,index=0,elapsed=0,last=performance.now(),cycles=0;
const el=id=>document.getElementById(id);el('digest').textContent=DATA.digest;
function draw(c,img,bg,scale){let ctx=c.getContext('2d');ctx.imageSmoothingEnabled=false;ctx.fillStyle=bg;ctx.fillRect(0,0,c.width,c.height);ctx.drawImage(img,0,0,DATA.canvas[0]*scale,DATA.canvas[1]*scale)}
function render(){if(!images[index].complete)return;draw(el('light'),images[index],'#e5d8bd',138/582);draw(el('dark'),images[index],'#273238',138/582);draw(el('large'),images[index],'#667b69',138/582*4);el('frame').value=index;el('state').textContent=`帧 ${index} / ${images.length-1} · ${DATA.durations[index]}ms · 已重复 ${cycles} 次`}
el('play').onclick=()=>{playing=!playing;el('play').textContent=playing?'暂停':'播放'};el('restart').onclick=()=>{index=elapsed=cycles=0;playing=true;render()};el('frame').oninput=e=>{playing=false;index=+e.target.value;elapsed=0;el('play').textContent='播放';render()};el('speed').oninput=e=>el('rate').textContent=e.target.value+'%';
Promise.all(images.map(i=>i.decode())).then(()=>{images.forEach((img,i)=>{let box=document.createElement('div'),c=document.createElement('canvas');c.width=183;c.height=183;draw(c,img,i%2?'#273238':'#e5d8bd',138/582);box.append(c,document.createTextNode(' '+i));el('all').append(box)});render()});
function tick(now){if(playing){elapsed+=(now-last)*el('speed').value/100;while(elapsed>=DATA.durations[index]){elapsed-=DATA.durations[index];index++;if(index===images.length){cycles++;if(el('repeat').checked)index=0;else{index=images.length-1;playing=false;break}}}render()}last=now;requestAnimationFrame(tick)}requestAnimationFrame(tick);</script></html>'''
(ROOT / 'review.html').write_text(html.replace('__PAYLOAD__', payload))
print('Built self-contained review.html')
