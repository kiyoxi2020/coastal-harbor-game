"""Validate the exact fixed-outfit candidates; never infer motion/visual acceptance."""
from pathlib import Path,PurePosixPath
from io import BytesIO
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def validate_candidate(c,directory,read=None):
 read=read or (lambda rel:(directory/rel).read_bytes())
 def require(ok,message):
  if not ok:raise ValueError(message)
 def path(rel):
  require(isinstance(rel,str) and rel and not PurePosixPath(rel).is_absolute() and '..' not in PurePosixPath(rel).parts,'unsafe relative path')
  try:return read(rel)
  except OSError as e:raise ValueError('missing '+rel) from e
 require(c.get('schema_version')==1 and c.get('template_id')=='adult-standard-v1' and c.get('action_id')=='water','wrong clip identity')
 require(c.get('direction') in ['south','west','east','north'] and c.get('garment') in ['A','B'],'unsupported capability')
 require(c.get('source_density_scale_vs_idle')==2 and abs(c.get('display_scale',0)-138/1164)<1e-12,'wrong density/display scale')
 frames=c.get('frames',[]);require(len(frames)==4 and [f.get('phase') for f in frames]==['ready','raise','pour','recovery'],'missing or reordered real phases')
 require(len({f.get('pose_id') for f in frames})==4 and len({f.get('sha256') for f in frames})==4,'duplicate pose or texture')
 require(all(type(f.get('duration_ms'))is int and f['duration_ms']>0 for f in frames),'invalid timing')
 require(800<=sum(f['duration_ms'] for f in frames)<=1200,'duration outside clip contract')
 for rel,digest in c.get('inputs',{}).items():require(sha(path(rel))==digest,'input hash mismatch '+rel)
 for f in frames:
  require(f['source'] in c['inputs'] and c['inputs'][f['source']]==f['source_sha256'],'unbound source')
  require(sha(path(f['source']))==f['source_sha256'] and sha(path(f['file']))==f['sha256'],'frame/source hash mismatch')
  source=Image.open(BytesIO(path(f['source']))).convert('RGBA');actual=Image.open(BytesIO(path(f['file']))).convert('RGBA')
  box=f['source_box_px'];require(len(box)==4 and all(type(v)is int for v in box),'invalid source box')
  require(0<=box[0]<box[2]<=source.width and 0<=box[1]<box[3]<=source.height,'source box outside actual image')
  cell=source.crop(tuple(box));require(cell.size==(1024,1536),'not native2x cell')
  require(cell.getchannel('A').getextrema()[0]==0,'missing transparent negative space')
  dx,dy=f['whole_frame_translation_px'];require(type(dx)is int and type(dy)is int and dx>=0 and dy>=0,'not integer whole-frame placement')
  require(dx+cell.width<=c['canvas_px'][0] and dy+cell.height<=c['canvas_px'][1],'source pixels cropped')
  expected=Image.new('RGBA',tuple(c['canvas_px']));expected.paste(cell,(dx,dy))
  require(actual.size==tuple(c['canvas_px']) and actual.tobytes()==expected.tobytes(),'source pixels edited/scaled/mirrored')
 require(not c.get('modular') and not c.get('accepted') and not c.get('native_checked') and not c.get('gameplay_available'),'proof scope falsely elevated')
 return True
def main():
 clips=[]
 for direction in ['south','west','east','north']:
  for garment in ['A','B']:
   directory=ROOT/(direction+'-'+garment);candidate=directory/'candidate.json';c=json.loads(candidate.read_text());validate_candidate(c,directory)
   clips.append(dict(direction=direction,garment=garment,candidate=candidate.relative_to(ROOT).as_posix(),sha256=sha(candidate.read_bytes()),canvas_px=c['canvas_px'],root_anchor_px=c['root_anchor_px'],duration_ms=sum(f['duration_ms'] for f in c['frames']),frames=4))
 result=dict(scope='Structure, provenance and exact whole-frame RGBA registration only; visual/grip/contact/rigidity/native and modular acceptance not implied',clips=clips,clip_count=len(clips),frame_count=sum(c['frames'] for c in clips),all_valid=True)
 (ROOT/'validation-summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('WATER valid clips=',len(clips),'frames=',result['frame_count'])
if __name__=='__main__':main()
