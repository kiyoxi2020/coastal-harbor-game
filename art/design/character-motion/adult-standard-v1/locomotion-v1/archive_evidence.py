"""Archive native captures, preserving real timing and original PNGs."""
from pathlib import Path
import json,hashlib,shutil,subprocess,zipfile
ROOT=Path(__file__).resolve().parent
VISUAL=Path('/private/tmp/coastal-locomotion-visual')
NATIVE=Path('/private/tmp/coastal-locomotion-art-native')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=ROOT/'evidence';out.mkdir(exist_ok=True)
 manifest=json.loads((ROOT/'baked/export-manifest.json').read_text())
 data=json.loads((VISUAL/'capture.json').read_text());native=json.loads((NATIVE/'metadata.json').read_text())
 assert data['artifact_digest']==native['artifact_digest']==manifest['artifact_digest']
 report={'artifact_digest':manifest['artifact_digest'],'visual_acceptance':'pending user review','scope':'stationary native ten-cycle animation plus separate real harbor keyboard controls; not strict foot-lock or full pipeline approval','clips':{}}
 for g in ['A','B']:
  for d in ['south','west','east','north']:
   key=f'{g}-{d}';seq=[s for s in data['samples'] if s['file'].startswith('sequence-'+key+'-')]
   assert len(seq)>40
   times=[s['elapsed_usec'] for s in seq];assert times[-1]-times[0]>=4266666
   assert {s['pose_id'] for s in seq}=={f'walk_{d}_{i}' for i in range(4)}
   gaps=[b-a for a,b in zip(times,times[1:])]
   assert max(gaps)<106667, (key,'sampling missed possible frame',max(gaps))
   lines=['ffconcat version 1.0']
   for i,s in enumerate(seq):
    lines += ["file '"+str(VISUAL/s['file'])+"'",'option framerate 1000']
    if i+1<len(seq):lines += ['duration '+str((times[i+1]-times[i])/1000000)]
   concat=Path('/private/tmp/coastal-locomotion-'+key+'.ffconcat');concat.write_text('\n'.join(lines)+'\n')
   subprocess.run(['/opt/homebrew/bin/ffmpeg','-hide_banner','-loglevel','error','-y','-safe','0','-f','concat','-i',str(concat),'-fps_mode','vfr','-c:v','libx264','-crf','17','-pix_fmt','yuv420p','-video_track_timescale','1000',str(out/(key+'.mp4'))],check=True)
   report['clips'][key]={'samples':len(seq),'elapsed_usec':[times[0],times[-1]],'max_sample_gap_usec':max(gaps),'video':key+'.mp4'}
 for folder,label in [(VISUAL,'visual'),(NATIVE,'harbor-controls')]:
  with zipfile.ZipFile(out/(label+'-originals.zip'),'w',zipfile.ZIP_DEFLATED) as archive:
   for p in sorted(folder.iterdir()):
    if p.suffix in ['.png','.json']:archive.write(p,p.name)
  for p in folder.glob('*.json'):shutil.copy2(p,out/(label+'-'+p.name))
 for p in VISUAL.glob('still-*.png'):shutil.copy2(p,out/p.name)
 for p in VISUAL.glob('idle-*.png'):shutil.copy2(p,out/p.name)
 report['files']={p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='summary.json'}
 (out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report['clips'],indent=2))
if __name__=='__main__':main()
