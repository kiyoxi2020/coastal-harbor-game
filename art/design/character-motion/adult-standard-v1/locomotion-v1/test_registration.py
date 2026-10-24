import unittest,json
from pathlib import Path
from PIL import Image,ImageChops
ROOT=Path(__file__).resolve().parent
class RegistrationTests(unittest.TestCase):
 def test_no_background_alpha_above_head(self):
  for path in (ROOT/'registered').glob('*.png'):
   if '-sheet' in path.name or 'walk_west' in path.name:continue
   with self.subTest(pose=path.stem):self.assertIsNone(Image.open(path).getchannel('A').crop((0,0,512,100)).getbbox())
 def test_opaque_body_colors_preserved(self):
  data=json.loads((ROOT/'registered/registration.json').read_text())
  for entry in data['frames']:
   source=Image.open(ROOT/entry['source']).convert('RGBA');cell=entry['source_cell']
   if cell is not None:source=source.crop((cell*512,0,(cell+1)*512,768))
   positioned=Image.new('RGBA',(512,768));positioned.paste(source,tuple(entry['whole_frame_translation_px']))
   result=Image.open(ROOT/entry['output']).convert('RGBA')
   visible=result.getchannel('A').point(lambda a:255 if a>=128 else 0)
   delta=ImageChops.difference(positioned,result)
   for channel in delta.split():self.assertIsNone(ImageChops.multiply(channel,visible).getbbox(),entry['pose_id'])
if __name__=='__main__':unittest.main()
