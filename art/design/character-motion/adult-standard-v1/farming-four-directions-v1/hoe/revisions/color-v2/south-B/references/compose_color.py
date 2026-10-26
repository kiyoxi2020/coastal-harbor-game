"""Extract GPT-authored shirt color through manually declared same-pose ownership.
No procedural recolor, local scaling or pose replacement. Original alpha and all
pixels outside the eligible shirt mask are preserved exactly.
"""
from PIL import Image,ImageDraw,ImageChops,ImageOps
import hashlib

def cool_mask(image,source=True):
 r,g,b,a=image.convert('RGBA').split()
 one=ImageChops.subtract(b,r).point(lambda v:255 if v>(25 if source else 10) else 0)
 two=ImageChops.subtract(b,g).point(lambda v:255 if v>(8 if source else 3) else 0)
 opaque=a.point(lambda v:255 if v>0 else 0)
 return ImageChops.multiply(ImageChops.multiply(one,two),opaque)

def compose(original,gpt,manual_polygons,max_fallback_fraction=0.05):
 original=original.convert('RGBA');gpt=gpt.convert('RGBA')
 if original.size!=gpt.size:raise ValueError('complete same-pose canvas mismatch')
 if not manual_polygons:raise ValueError('manual shirt surface ownership required')
 surface=Image.new('L',original.size);draw=ImageDraw.Draw(surface)
 for polygon in manual_polygons:
  if len(polygon)<3:raise ValueError('shirt polygon must enclose actual surface')
  draw.polygon([tuple(p) for p in polygon],fill=255)
 # Color assists contour extraction only within explicitly authored garment surfaces.
 owned=ImageChops.multiply(surface,cool_mask(original,True))
 owned_count=owned.histogram()[255]
 if not owned_count:raise ValueError('no actual original blue cloth in declared surfaces')
 paint=ImageChops.multiply(owned,cool_mask(gpt,False));paint_count=paint.histogram()[255]
 fallback_fraction=1-paint_count/owned_count
 if fallback_fraction>max_fallback_fraction:raise ValueError(f'GPT garment moved/nonblue within original surface: {fallback_fraction:.4%}')
 target=gpt.copy();target.putalpha(original.getchannel('A'))
 out=Image.composite(target,original,paint)
 if out.getchannel('A').tobytes()!=original.getchannel('A').tobytes():raise ValueError('original alpha changed')
 outside=ImageChops.multiply(ImageChops.difference(out,original).convert('RGB'),ImageOps.invert(paint).convert('RGB'))
 if outside.getbbox() is not None:raise ValueError('non-owned source RGBA changed')
 info={'manual_surface_ownership':True,'owned_blue_pixels':owned_count,'gpt_color_pixels_applied':paint_count,'original_edge_pixels_retained':owned_count-paint_count,'fallback_fraction':fallback_fraction,'max_fallback_fraction':max_fallback_fraction,'outside_mask_rgba_differences':0,'original_alpha_unchanged':True,'original_alpha_sha256':hashlib.sha256(original.getchannel('A').tobytes()).hexdigest(),'operation':'GPT garment RGB extraction through manual same-pose shirt ownership; preserve original alpha and all other source RGBA'}
 return out,paint,info
