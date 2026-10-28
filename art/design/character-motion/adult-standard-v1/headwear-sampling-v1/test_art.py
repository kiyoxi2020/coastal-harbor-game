"""Regression for reviewed non-hat source strokes outside the reach silhouette."""
from pathlib import Path
import unittest
from PIL import Image,ImageChops
HERE=Path(__file__).resolve().parent
class HeadwearArtTests(unittest.TestCase):
 def test_reach_atlas_edge_stroke_not_exported(self):
  folder=HERE/'harvest-north'
  # Reviewed source-cell edge, disjoint from the real hat (which ends x=1063).
  box=(1121,627,1123,670)
  for suffix in ['hat','hair_hat']:
   part=Image.open(folder/'parts/reach-hat-complete-source.png').convert('RGBA')
   self.assertIsNone(part.getchannel('A').crop(box).getbbox())
   bare=Image.open(folder/'baked/harvest_north_B_reach-bare.png').convert('RGBA').crop(box)
   final=Image.open(folder/f'baked/harvest_north_B_reach-{suffix}.png').convert('RGBA').crop(box)
   self.assertFalse(any(channel.getbbox() for channel in ImageChops.difference(bare,final).split()))
if __name__=='__main__':unittest.main()
