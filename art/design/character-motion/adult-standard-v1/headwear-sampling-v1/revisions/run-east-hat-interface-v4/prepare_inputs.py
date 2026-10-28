"""Prepare fixed-coordinate GPT references. Guide marks are inspection-only."""
from pathlib import Path
from PIL import Image
import json,hashlib
P=Path(__file__).resolve().parent;BASE=P.parents[1]/'run-east'
def main():
 (P/'references').mkdir(exist_ok=True);(P/'sources').mkdir(exist_ok=True)
 for name,path in [('original-head-window',BASE/'references/idle_east_0-bare.png'),('old-wearing-reference',BASE/'baked/idle_east_0-hat.png')]:
  image=Image.open(path).convert('RGBA').crop((0,0,512,512));image.save(P/'references'/f'{name}-512.png');image.resize((1024,1024),Image.Resampling.NEAREST).save(P/'references'/f'{name}-1024.png')
 (P/'references/input-geometry.json').write_text(json.dumps({'template_id':'adult-standard-v1','pose_id':'idle_east_0','target_canvas_px':[512,768],'window_px':[0,0,512,512],'model_reference_px':[1024,1024],'density_projection':'whole-window nearest only','placement_px':[0,0],'base_sha256':hashlib.sha256((BASE/'references/idle_east_0-bare.png').read_bytes()).hexdigest(),'old_wearing_sha256':hashlib.sha256((BASE/'baked/idle_east_0-hat.png').read_bytes()).hexdigest(),'guide_marks_are_formal_art':False},indent=2)+'\n')
 print('Prepared original-head and existing hat reference windows at fixed coordinates; no pose fitting.')
if __name__=='__main__':main()
