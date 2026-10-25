from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent

def build():
    manifest = json.loads((ROOT/'registered/registration.json').read_text())
    html = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>西向采收完整帧候选</title>
<style>body{margin:24px;background:#192822;color:#eee;font:16px system-ui;line-height:1.6}h1{font-size:23px}button,input{margin:6px;padding:8px}canvas{display:block;max-width:100%;image-rendering:pixelated;border:1px solid #777}#still{display:flex;gap:24px;flex-wrap:wrap;margin-top:24px}.pose{background:#ece4cf;color:#222;padding:12px}.pose img{image-rendering:pixelated;width:121.402px;height:182.103px}a{color:#d0ebac}</style>
<h1>西向 harvest · 已拒绝的完整帧试稿 · 未获用户批准</h1><p>蹲身伸手 → 握取 → 收回 → 起身的采收语义可见，但密度与支撑检查失败：末帧644px高，对照582px偏大10.7%；同一比例下实际约153px，对照138px。起身时鞋子明显左移。<br>所有人物与萝卜像素均来自GPT；仅整帧向上13px注册，没有缩放补救。采收为一次性动作；本页重播从结束姿态直接返回首帧，仅用于反复评审。握取事件只作视觉标记，不执行业务事务。</p>
<button id="play">暂停</button><button id="prev">上一帧</button><button id="next">下一帧</button>
<label>速度 <input id="speed" type="range" min="0.25" max="1.5" value="1" step="0.05"><output id="speedValue">100%</output></label><label>停帧 <input id="scrub" type="range" min="0" max="3" value="0" step="1"></label><p id="state"></p>
<canvas id="view" width="1080" height="390"></canvas><div id="still"></div>
<p><a href="__SOURCE__">完整GPT原图</a> · <a href="registered/registration.json">整帧登记</a> · <a href="poses.json">姿态观察</a> · <a href="evidence/validation.json">验证结果</a> · <a href="README.md">来源与边界</a></p>
<script>const M=__MANIFEST__;const images=M.frames.map(f=>{let i=new Image;i.src=f.output;return i});const c=document.querySelector('#view'),ctx=c.getContext('2d');ctx.imageSmoothingEnabled=false;let elapsed=0,prior=0,playing=true,index=0,replays=0;const scale=138/582;
function phaseAt(t){let sum=0;for(let i=0;i<M.frames.length;i++){sum+=M.frames[i].duration_ms;if(t<sum)return i}return M.frames.length-1}
function draw(){ctx.fillStyle='#25352c';ctx.fillRect(0,0,540,390);ctx.fillStyle='#eee6d1';ctx.fillRect(540,0,540,390);ctx.font='16px sans-serif';ctx.fillStyle='white';ctx.fillText('暗背景 · 同一源图比例',25,32);ctx.fillStyle='#222';ctx.fillText('明背景 · scale 138/582',565,32);for(let x of [200,740]){ctx.strokeStyle='#9b9278';ctx.beginPath();ctx.moveTo(x-15,70+708*scale);ctx.lineTo(x+150,70+708*scale);ctx.stroke();if(images[index].complete)ctx.drawImage(images[index],x,70,512*scale,768*scale)}document.querySelector('#state').textContent=`${M.status} · 帧 ${index} / ${M.frames[index].phase} · ${M.frames[index].duration_ms}ms · 已重播 ${replays} 次 · 握取相位${M.event.time_ms}ms`;document.querySelector('#scrub').value=index}
function tick(now){if(prior&&playing){elapsed+=(now-prior)*+document.querySelector('#speed').value;while(elapsed>=M.cycle_duration_ms){elapsed-=M.cycle_duration_ms;replays++}index=phaseAt(elapsed)}prior=now;draw();requestAnimationFrame(tick)}
document.querySelector('#play').onclick=()=>{playing=!playing;document.querySelector('#play').textContent=playing?'暂停':'播放'};
function select(i){playing=false;document.querySelector('#play').textContent='播放';index=(i+M.frames.length)%M.frames.length;elapsed=M.frames.slice(0,index).reduce((s,f)=>s+f.duration_ms,0);draw()}
document.querySelector('#prev').onclick=()=>select(index-1);document.querySelector('#next').onclick=()=>select(index+1);document.querySelector('#scrub').oninput=e=>select(+e.target.value);document.querySelector('#speed').oninput=e=>document.querySelector('#speedValue').textContent=Math.round(e.target.value*100)+'%';
M.frames.forEach((f,i)=>{const d=document.createElement('div');d.className='pose';d.innerHTML=`<div>帧${i}: ${f.phase}</div><img src="${f.output}"><div>${f.duration_ms}ms</div>`;document.querySelector('#still').append(d)});requestAnimationFrame(tick);</script></html>'''
    html=html.replace('__MANIFEST__',json.dumps(manifest)).replace('__SOURCE__',manifest['frames'][0]['source'])
    (ROOT/'review.html').write_text(html)
    print('Built independent harvest review with play, step, speed, light/dark display.')

if __name__=='__main__':
    build()
