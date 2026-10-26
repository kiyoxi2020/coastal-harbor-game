"""Preserve complete GPT frames by integer whole-frame registration only."""
from pathlib import Path
import hashlib,json,math,shutil
from PIL import Image
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def build():
 cfg=json.loads((ROOT/'registration-config.json').read_text())
 frames=[]
 for idx,f in enumerate(cfg['frames']):
  im=Image.open(ROOT/f['source']).convert('RGBA')
  if list(im.size)!=cfg['source_canvas_expected_px']:raise ValueError('unexpected source canvas')
  dx=cfg['root_anchor_px'][0]-f['source_root_px'][0];dy=cfg['root_anchor_px'][1]-f['source_root_px'][1]
  if not all(type(x)is int for x in [dx,dy]):raise ValueError('noninteger placement')
  if dx<0 or dy<0 or im.width+dx>cfg['canvas_px'][0] or im.height+dy>cfg['canvas_px'][1]:raise ValueError('entire source, including low-alpha pixels, must fit')
  out=Image.new('RGBA',tuple(cfg['canvas_px']));out.paste(im,(dx,dy))
  target=ROOT/f'registered/{cfg["action_id"]}_west_key_{idx}.png';out.save(target)
  frames.append(dict(pose_id=f'{cfg["action_id"]}_west_key_{idx}',file=target.relative_to(ROOT).as_posix(),duration_ms=f['duration_ms'],source=f['source'],source_sha256=sha(ROOT/f['source']),source_box_px=[0,0,im.width,im.height],whole_frame_translation_px=[dx,dy],sha256=sha(target)))
 inputs={p.relative_to(ROOT).as_posix():sha(p) for sub in ['sources','references','prompts'] for p in sorted((ROOT/sub).glob('*')) if p.is_file()}
 for name in ['registration-config.json','poses.json','measurements.json','provenance.json','build_candidate.py','native_review.gd','test_candidate.py']:
  p=ROOT/name
  if p.exists():inputs[name]=sha(p)
 dump(ROOT/'source-manifest.json',dict(generator='built-in image_gen',exact_generation_model='not returned by tool; not inferred',input_artifacts=inputs,source_pixel_policy='Complete RGBA source retained; no redrawing, local scaling, local translation or retouch; integer whole-frame paste only.'))
 data={k:cfg[k] for k in ['schema_version','template_id','motion_set_id','revision_id','action_id','direction','status','canvas_px','root_anchor_px','display_scale','source_density_scale_vs_idle','root_method','accepted','native_checked','modular','gameplay_available']}
 data.update(frames=frames,loop=False,review_repeat=True,events=[],move_policy='diagnostic_only_no_world_or_gameplay',inputs=inputs,scope='One/two key poses only; missing full action phases. No clothing layers, hidden body, grips, support trajectory or release acceptance.')
 data['artifact_digest']=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 dump(ROOT/'candidate.json',data)
 html='''<!doctype html><html lang="zh"><meta charset="utf-8"><title>KEY POSE PROOF</title><style>body{background:#253238;color:#eee;font:16px system-ui;margin:24px}button{padding:8px;margin:5px} .board{display:inline-flex;gap:24px;padding:24px;vertical-align:top}.light{background:#e5d8bd;color:#222}.dark{background:#273238}img{image-rendering:pixelated;display:block}figure{margin:0;text-align:center}p{max-width:1000px}input{width:200px}</style><h1>KEY POSES — 未通过动作验收</h1><p>仅完整GPT关键姿态；无插帧、无世界接触、无玩法事务，不代表动作或换装完成。近鞋后缘观察仅用于整帧登记，另一鞋的差异保持原样。原始尺寸、段比例、关节未知项、工具测量见 measurements.json / poses.json / implementation-report.md。</p><button id="play">诊断交替播放</button><button id="stop">停止</button><input id="frame" type="range" min="0"><span id="name"></span><main id="boards"></main><p><a href="candidate.json">candidate/hash</a> · <a href="measurements.json">actual measurements</a> · <a href="implementation-report.md">implementation report</a></p><script>const C=CONFIG;let frame=0,timer;document.querySelector('#frame').max=C.frames.length-1;for(const theme of ['light','dark']){let b=document.createElement('div');b.className='board '+theme;for(const scale of [1,2]){let f=document.createElement('figure');f.innerHTML='<figcaption>'+scale+'× 原生显示比例</figcaption><img>';let im=f.querySelector('img');im.width=C.canvas_px[0]*C.display_scale*scale;im.height=C.canvas_px[1]*C.display_scale*scale;b.append(f)}document.querySelector('#boards').append(b)}function show(){document.querySelectorAll('img').forEach(i=>i.src=C.frames[frame].file);document.querySelector('#name').textContent=C.frames[frame].pose_id;document.querySelector('#frame').value=frame}document.querySelector('#frame').oninput=e=>{frame=+e.target.value;show()};document.querySelector('#play').onclick=()=>{clearInterval(timer);timer=setInterval(()=>{frame=(frame+1)%C.frames.length;show()},500)};document.querySelector('#stop').onclick=()=>clearInterval(timer);show();</script>'''.replace('CONFIG',json.dumps(data,ensure_ascii=False))
 (ROOT/'review.html').write_text(html)
 print(cfg['action_id'],data['status'],data['artifact_digest'])
if __name__=='__main__':build()
