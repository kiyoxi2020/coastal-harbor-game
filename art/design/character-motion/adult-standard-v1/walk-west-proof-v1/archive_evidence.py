import hashlib,json,shutil,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
out=ROOT/'evidence';out.mkdir(exist_ok=True)
report={'artifact_digest':json.loads((ROOT/'baked/export-manifest.json').read_text())['artifact_digest'],'user_accepted':False,'captures':{}}
for name,metadata in [('native','capture.json'),('travel','travel-capture.json')]:
 src=Path('/private/tmp/coastal-motion-delivery-'+name)
 data=json.loads((src/metadata).read_text());seq=[x for x in data['captures'] if x['kind']=='continuous']
 shutil.copy2(src/metadata,out/metadata)
 with zipfile.ZipFile(out/(name+'-originals.zip'),'w',zipfile.ZIP_DEFLATED) as z:
  for f in sorted(src.iterdir()):
   if f.suffix in ('.png','.json'):z.write(f,f.name)
 lines=['ffconcat version 1.0']
 for i,s in enumerate(seq):
  lines += ["file '"+str(src/s['file'])+"'",'option framerate 1000']
  if i+1<len(seq):lines+=['duration '+str((seq[i+1]['elapsed_ms']-s['elapsed_ms'])/1000)]
 concat=Path('/private/tmp/coastal-'+name+'-video.ffconcat');concat.write_text('\n'.join(lines)+'\n')
 subprocess.run(['/opt/homebrew/bin/ffmpeg','-hide_banner','-loglevel','error','-y','-safe','0','-f','concat','-i',str(concat),'-fps_mode','vfr','-c:v','libx264','-crf','17','-pix_fmt','yuv420p','-video_track_timescale','1000',str(out/(name+'.mp4'))],check=True)
 report['captures'][name]={'continuous_count':len(seq),'first_elapsed_ms':seq[0]['elapsed_ms'],'last_elapsed_ms':seq[-1]['elapsed_ms'],'captured_files':len(data['captures']),'metadata':metadata,'originals':name+'-originals.zip','video':name+'.mp4','video_timing':'VFR from actual consecutive elapsed_ms; PNG demux timebase 1ms; no duplicated cycles','resets':data.get('resets',[])}
for file in ['still_light_0.png','still_light_1.png','still_light_2.png','still_light_3.png','still_dark_1.png','inspect_mask.png','inspect_source.png']:
 p=Path('/private/tmp/coastal-motion-delivery-native')/file
 if p.exists():shutil.copy2(p,out/file)
report['files']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file() and p.name!='summary.json'}
(out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:{a:b for a,b in v.items() if a not in ['resets']} for k,v in report['captures'].items()},indent=2))
