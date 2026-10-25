"""Build a local HTML proof; all character/tool pixels come from the GPT source."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent

def build():
    registration = json.loads((ROOT / 'registered/registration.json').read_text())
    html = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>西向锄地完整帧候选</title>
<style>body{margin:24px;background:#172420;color:#eee;font:16px system-ui}h1{font-size:23px}button,input{margin:6px;padding:8px}canvas{display:block;max-width:100%;image-rendering:pixelated;border:1px solid #777}.note{max-width:1000px;line-height:1.6}#still{display:flex;gap:18px;flex-wrap:wrap;margin-top:24px}.pose{background:#ece4cf;color:#222;padding:12px}.pose img{image-rendering:pixelated;width:182.103px;height:182.103px}a{color:#cde9b6}</style>
<h1>西向 hoe · 奶油短袖 A · 待返工、未获用户批准的完整帧候选</h1>
<p class="note">本页仅供完整动作评审。头部约215px，对照母版236px；工具长度随帧变化，须返工。所有帧统一扩画布到768×768、根点[384,708]以保留锄头。角色源图不缩放、不分件挪动；原生显示比例为138/582（参考站立138px；当前候选约135px，密度未通过）。接触相位仅为视觉标记，不执行玩法事务。无分层、换装、四向或生产接入声明。</p>
<button id="play">暂停</button><button id="prev">上一帧</button><button id="next">下一帧</button>
<label>速度 <input id="speed" type="range" min="0.25" max="1.5" value="1" step="0.05"><output id="speedValue">100%</output></label>
<label>停帧 <input id="scrub" type="range" min="0" max="3" value="0" step="1"></label>
<p id="state"></p><canvas id="view" width="1080" height="440"></canvas><div id="still"></div>
<p><a href="sources/hoe-west-v3.png">完整 GPT 原图</a> · <a href="registered/registration.json">整帧登记</a> · <a href="poses.json">姿态观察</a> · <a href="README.md">来源与边界</a></p>
<script>const M=__REGISTRATION__;const imgs=M.frames.map(f=>{let i=new Image;i.src=f.output;return i});const c=document.querySelector('#view'),ctx=c.getContext('2d');ctx.imageSmoothingEnabled=false;let elapsed=0,prior=0,playing=true,index=0,loops=0;const scale=138/582;
const phaseAt=t=>{let sum=0;for(let i=0;i<M.frames.length;i++){sum+=M.frames[i].duration_ms;if(t<sum)return i}return M.frames.length-1};
function draw(){ctx.fillStyle='#25352c';ctx.fillRect(0,0,540,440);ctx.fillStyle='#eee6d1';ctx.fillRect(540,0,540,440);ctx.font='16px sans-serif';ctx.fillStyle='white';ctx.fillText('暗背景 · 原生138px人物尺度',25,32);ctx.fillStyle='#222';ctx.fillText('明背景 · 相同源图与尺度',565,32);for(let x of [200,740]){ctx.strokeStyle='#9b9278';ctx.beginPath();ctx.moveTo(x-30,80+708*scale);ctx.lineTo(x+160,80+708*scale);ctx.stroke();if(imgs[index].complete)ctx.drawImage(imgs[index],x,80,768*scale,768*scale)}document.querySelector('#state').textContent=`帧 ${index} / ${M.frames[index].phase} · ${M.frames[index].duration_ms}ms · 已完整播放 ${loops} 循环 · 接触帧 ${M.event.frame_index}`;document.querySelector('#scrub').value=index}
function tick(now){if(prior&&playing){elapsed+=(now-prior)*+document.querySelector('#speed').value;while(elapsed>=M.cycle_duration_ms){elapsed-=M.cycle_duration_ms;loops++}index=phaseAt(elapsed)}prior=now;draw();requestAnimationFrame(tick)}
document.querySelector('#play').onclick=()=>{playing=!playing;document.querySelector('#play').textContent=playing?'暂停':'播放'};
function select(i){playing=false;document.querySelector('#play').textContent='播放';index=(i+M.frames.length)%M.frames.length;elapsed=M.frames.slice(0,index).reduce((s,f)=>s+f.duration_ms,0);draw()}
document.querySelector('#prev').onclick=()=>select(index-1);document.querySelector('#next').onclick=()=>select(index+1);document.querySelector('#scrub').oninput=e=>select(+e.target.value);document.querySelector('#speed').oninput=e=>document.querySelector('#speedValue').textContent=Math.round(e.target.value*100)+'%';
M.frames.forEach((f,i)=>{const d=document.createElement('div');d.className='pose';d.innerHTML=`<div>帧${i}: ${f.phase}</div><img src="${f.output}"><div>${f.duration_ms}ms</div>`;document.querySelector('#still').append(d)});requestAnimationFrame(tick);</script></html>'''
    (ROOT / 'review.html').write_text(html.replace('__REGISTRATION__', json.dumps(registration)))
    print('Built review.html with play/pause, frame step, speed, light/dark display.')

if __name__ == '__main__':
    build()
