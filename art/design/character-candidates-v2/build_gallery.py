from pathlib import Path
import json,html
A=Path(__file__).resolve().parent
c=json.loads((A/'catalog.json').read_text());names={'body':'人体母版','hair':'头发','top':'上衣','pants':'下装','shoes':'鞋子','hat':'帽子'}
css='''body{font:16px system-ui;margin:28px;background:#172127;color:#eee}button,select{padding:10px;margin:4px}section{margin:30px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(400px,1fr));gap:16px}article{background:#26343a;padding:16px;border-radius:8px}.frames{display:flex}.frames a{width:25%}.frames img{width:100%;image-rendering:pixelated;background:transparent}a{color:#9fd4eb}small{color:#bbb}body.light{background:#e8e0ce;color:#172127}body.light article{background:#f4ecdf}body.light a{color:#185471}'''
parts=['<!doctype html><meta charset="utf-8"><title>人物组件候选库</title><style>'+css+'</style><h1>人物组件候选库</h1><p>六类各10款。南／西／东／北；点击图片查看原尺寸。候选供挑选，不代表跨体型适配或动画完成。</p><button onclick="document.body.classList.toggle(\'light\')">明暗背景</button><select id="mode" onchange="document.querySelectorAll(\'img\').forEach(i=>i.src=i.dataset[this.value])"><option value="preview">穿戴预览</option><option value="component">透明组件</option></select>']
for cat,items in c['categories'].items():
 parts.append('<section><h2>'+names[cat]+f' · {len(items)}款</h2><div class="grid">')
 for e in items:
  parts.append('<article><b>'+html.escape(e['id']+' · '+e['label'])+'</b><div class="frames">')
  for d in ['south','west','east','north']:
   pre='../../../'+e['previews'][d];co=e['components'][d];co=co[0] if isinstance(co,list) else co;co='../../../'+co
   parts.append(f'<a target="_blank" href="{pre}"><img alt="{d}" src="{pre}" data-preview="{pre}" data-component="{co}"></a>')
  parts.append('</div><small>兼容模板：'+html.escape(e['template_id'])+'</small><br><a href="../../../'+e['source']+'">GPT原图</a> · <a href="../../../'+e['prompt']+'">提示词</a></article>')
 parts.append('</div></section>')
parts.append('<script>document.querySelector("#mode").addEventListener("change",function(){document.querySelectorAll(".frames a").forEach(a=>a.href=a.querySelector("img").src)})</script>')
(A/'gallery.html').write_text('\n'.join(parts))
print('gallery.html generated from catalog, preserves native source files')
