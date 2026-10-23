"""Register GPT-authored age-specific anatomy; never shrink an adult into a child."""
from pathlib import Path
from PIL import Image
import statistics,json
ROOT=Path(__file__).resolve().parents[3];ART=Path(__file__).resolve().parent;OUT=ROOT/'godot2d/assets/character-library-v1/proportions'
OUT.mkdir(parents=True,exist_ok=True)
DIRS=['south','west','east','north'];YS=[0,315,605,915,1166,1402]
FAMILIES=[('adult_woman',.97),('elder_man',.94),('elder_woman',.91),('boy',.75),('girl',.74)]
im=Image.open(ART/'family-proportions-original.png').convert('RGBA');w,h=im.size
ref_heights=[]
for d in DIRS:
 r=Image.open(ROOT/'godot2d/assets/player-unified-v4'/('walk_'+d+'_0.png')).convert('RGBA')
 b=r.getchannel('A').point(lambda a:255 if a>64 else 0).getbbox();ref_heights.append(2*(b[3]-b[1]))
height=statistics.median(ref_heights)
meta={'source':'family-proportions-original.png','canvas':[768,768],'anchor':[384,672],'world_scale':.075,'reference_adult_height':height,'families':{}}
for row,(family,ratio) in enumerate(FAMILIES):
 front=im.crop((0,YS[row],w//4,YS[row+1]));b=front.getchannel('A').point(lambda a:255 if a>64 else 0).getbbox()
 factor=height*ratio/(b[3]-b[1]);meta['families'][family]={'ratio':ratio,'uniform_scale':factor,'frames':{}}
 for col,d in enumerate(DIRS):
  source_box=(col*w//4,YS[row],(col+1)*w//4,YS[row+1]);tile=im.crop(source_box)
  b=tile.getchannel('A').point(lambda a:255 if a>64 else 0).getbbox()
  foot=tile.crop((0,b[3]-20,tile.width,b[3])).getchannel('A').point(lambda a:255 if a>64 else 0).getbbox();center=(foot[0]+foot[2])/2
  scaled=tile.resize((round(tile.width*factor),round(tile.height*factor)),Image.Resampling.NEAREST)
  pos=(round(384-center*factor),round(672-b[3]*factor));frame=Image.new('RGBA',(768,768));frame.alpha_composite(scaled,pos)
  path=OUT/(family+'_'+d+'.png');frame.save(path)
  meta['families'][family]['frames'][d]={'source_box':source_box,'source_bbox':b,'position':pos,'file':str(path.relative_to(ROOT/'godot2d')),'output_bbox':frame.getchannel('A').point(lambda a:255 if a>64 else 0).getbbox()}
(ART/'family-metadata.json').write_text(json.dumps(meta,indent=2))
# Source-resolution proof sheet, male + the five new families, four directions.
sheet=Image.new('RGBA',(768*6,768*4))
for row,d in enumerate(DIRS):
 r=Image.open(ROOT/'godot2d/assets/player-unified-v4'/('walk_'+d+'_0.png')).convert('RGBA').resize((768,768),Image.Resampling.NEAREST);sheet.alpha_composite(r,(0,row*768))
 for col,(family,_) in enumerate(FAMILIES,1):sheet.alpha_composite(Image.open(OUT/(family+'_'+d+'.png')),(col*768,row*768))
sheet.save(ART/'family-review-full.png');sheet.resize((2304,1536),Image.Resampling.NEAREST).save(ART/'family-review.png')
print('Registered 5 age/body-family samples x 4 directions; each family retains its own anatomy.')
