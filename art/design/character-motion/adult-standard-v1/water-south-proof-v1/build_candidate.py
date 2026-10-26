"""Two-pose proof only: preserve whole generated RGBA frames; no resizing/retouch."""
from pathlib import Path
import hashlib,json,math
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,value):(ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def translated(points,dx,dy):return {k:None if v is None else [v[0]+dx,v[1]+dy] for k,v in points.items()}
def build():
 cfg=json.loads((ROOT/'registration-config.json').read_text());frames=[];poses=[]
 for i,f in enumerate(cfg['frames']):
  im=Image.open(ROOT/f['source']).convert('RGBA')
  if list(im.size)!=cfg['source_canvas_expected_px']:raise ValueError('unexpected generated source size')
  dx,dy=[a-b for a,b in zip(cfg['root_anchor_px'],f['source_root_px'])]
  if not all(type(n)is int for n in (dx,dy)):raise ValueError('integer whole-frame placement required')
  if dx<0 or dy<0 or dx+im.width>cfg['canvas_px'][0] or dy+im.height>cfg['canvas_px'][1]:raise ValueError('full RGBA source does not fit')
  out=Image.new('RGBA',tuple(cfg['canvas_px']));out.paste(im,(dx,dy));file=f'registered/water_south_key_{i}.png';out.save(ROOT/file)
  pid=f'water_south_key_{i}'
  frames.append(dict(pose_id=pid,phase=f['phase'],file=file,source=f['source'],source_sha256=sha(ROOT/f['source']),source_box_px=[0,0,im.width,im.height],duration_ms=f['duration_ms'],whole_frame_translation_px=[dx,dy],sha256=sha(ROOT/file)))
  pose=dict(pose_id=pid,phase=f['phase'],source=f['source'],source_root_px=f['source_root_px'],whole_frame_translation_px=[dx,dy],anatomical_side_mapping='front: character right=image left; character left=image right',hidden_regions_status='not delivered',landmark_method='manual visible surfaces ±8 source px; hidden joints null; not inferred from body-height percentages')
  for group,key in [('landmarks','landmarks_source_px'),('visible_foot_points','visible_foot_points_source_px'),('tool','tool_source_px')]:
   pose['source_'+group+'_px']=f[key];pose['registered_'+group+'_px']=translated(f[key],dx,dy)
  poses.append(pose)
 dump('poses.json',dict(schema_version=1,coordinate_space='unscaled source and registered pixels',poses=poses))
 inputs={p.relative_to(ROOT).as_posix():sha(p) for folder in ['sources','references','prompts'] for p in sorted((ROOT/folder).glob('*')) if p.is_file()}
 for name in ['registration-config.json','poses.json','measurements.json','provenance.json','build_candidate.py','measure_candidate.py','test_candidate.py','native_review.gd']:
  p=ROOT/name
  if p.exists():inputs[name]=sha(p)
 data={k:cfg[k] for k in ['schema_version','template_id','motion_set_id','revision_id','action_id','direction','garment','status','canvas_px','root_anchor_px','display_scale','source_density_scale_vs_idle','root_method']}
 data.update(accepted=False,native_checked=False,modular=False,gameplay_available=False,frames=frames,loop=False,review_repeat=True,events=[],move_policy='diagnostic_only_no_world_or_gameplay',inputs=inputs,scope='Two south garment-A key poses only; no full action, layers, clothing/body hidden regions, gameplay, approved support/grip trajectory or user acceptance.')
 data['artifact_digest']=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest();dump('candidate.json',data)
 dump('source-manifest.json',dict(generator='built-in image_gen',exact_generation_model='tool does not return model ID; not inferred',input_artifacts=inputs,source_pixel_policy='original complete RGBA kept; integer whole-frame translation only; no face/hand replacement, no local scaling or pixel repaint'))
 # Review evidence is a diagnostic visualization, never a new art source. Uniform nearest display only.
 board=Image.new('RGB',(1540,740),(35,45,50));draw=ImageDraw.Draw(board)
 for theme,bg in enumerate([(229,216,189),(35,45,50)]):
  for i,f in enumerate(frames):
   x=20+(theme*2+i)*380;draw.rectangle([x,35,x+370,730],fill=bg)
   im=Image.open(ROOT/f['file']).convert('RGBA');s=cfg['display_scale'];small=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.NEAREST)
   board.paste(small,(x+25,80),small);big=im.resize((round(im.width*s*2),round(im.height*s*2)),Image.Resampling.NEAREST)
   # Separate large board avoids fitting any character to a bbox.
   draw.text((x+10,15),f['phase']+' 1x + 2x / light' if theme==0 else f['phase']+' 1x + 2x / dark',fill='white')
   board.paste(big,(x+25,300),big)
 board.save(ROOT/'evidence/static-review.png')
 html='''<!doctype html><html lang="zh"><meta charset="utf-8"><title>南向浇水两姿态</title><style>body{font:16px system-ui;background:#263238;color:#eee;padding:24px}button{padding:10px}section{display:inline-flex;padding:12px;gap:20px;vertical-align:top}img{image-rendering:pixelated}figure{margin:0}.light{background:#e5d8bd;color:#222}.dark{background:#263238}p{max-width:900px}</style><h1>南向浇水 A：ready / pour</h1><p>仅完整GPT两关键姿态，未通过动作/接触/用户验收。完整源图、段比例、握点与脚点差异均保留；禁止据此扩完整动作。原生世界、动态换衣和玩法未验证。</p><button id="toggle">交替播放</button><button id="ready">ready</button><button id="pour">pour</button><span id="phase"></span><main></main><p><a href="measurements.json">实际测量</a> · <a href="candidate.json">candidate / hash</a> · <a href="implementation-report.md">实施报告</a></p><script>const C=CONFIG;let idx=0,timer;for(const theme of ['light','dark']){let section=document.createElement('section');section.className=theme;for(const scale of [1,2]){let figure=document.createElement('figure');figure.innerHTML='<figcaption>'+scale+'×统一显示</figcaption><img>';let im=figure.querySelector('img');im.width=C.canvas_px[0]*C.display_scale*scale;im.height=C.canvas_px[1]*C.display_scale*scale;section.append(figure)}document.querySelector('main').append(section)}function show(){document.querySelectorAll('img').forEach(im=>im.src=C.frames[idx].file);document.querySelector('#phase').textContent=C.frames[idx].phase}function stop(i){clearInterval(timer);timer=null;idx=i;show()}document.querySelector('#ready').onclick=()=>stop(0);document.querySelector('#pour').onclick=()=>stop(1);document.querySelector('#toggle').onclick=()=>{if(timer){clearInterval(timer);timer=null}else timer=setInterval(()=>{idx=1-idx;show()},500)};show()</script>'''.replace('CONFIG',json.dumps(data,ensure_ascii=False))
 (ROOT/'review.html').write_text(html)
 print(data['artifact_digest'])
if __name__=='__main__':build()
