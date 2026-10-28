"""Single-owner RGBA assembly in original frame coordinates; no synthesized color."""
from PIL import Image,ImageChops
def binary(image):return image.getchannel('A').point(lambda value:255 if value else 0)
def intersects(a,b):return ImageChops.darker(a,b).getbbox() is not None
def assemble_hat(source,source_owned,patch,patch_owned,allowed_edit,remove_old,frozen):
 size=source.size
 if any(im.size!=size for im in [source_owned,patch,patch_owned,allowed_edit,remove_old,frozen]):raise ValueError('Source/masks must share original frame coordinates.')
 outside=ImageChops.invert(allowed_edit)
 if intersects(patch_owned,outside) or intersects(remove_old,outside):raise ValueError('Selected modification escapes authorized contact band.')
 if intersects(patch_owned,frozen) or intersects(remove_old,frozen):raise ValueError('Selected modification touches frozen hat surface.')
 if ImageChops.subtract(frozen,source_owned).getbbox():raise ValueError('Frozen real hat pixels missing from old source ownership.')
 kept=ImageChops.subtract(source_owned,remove_old)
 hat=Image.new('RGBA',size);hat.paste(source,(0,0),kept);hat.paste(patch,(0,0),patch_owned)
 tags=Image.new('L',size);tags.paste(3,(0,0,*size),kept);tags.paste(4,(0,0,*size),patch_owned)
 for old,new,mask in zip(source.get_flattened_data(),hat.get_flattened_data(),frozen.get_flattened_data()):
  if mask and old!=new:raise ValueError('Frozen hat RGBA changed.')
 return hat,tags
def render(base,hat,hat_tags,rear,hair=None,hair_visible=None):
 if base.size!=hat.size or rear.size!=base.size:raise ValueError('No fitting transform permitted.')
 owned=binary(hat)
 if ImageChops.subtract(rear,owned).getbbox():raise ValueError('Rear classification includes non-hat pixels.')
 body=binary(base);front=ImageChops.subtract(owned,rear);behind=ImageChops.darker(rear,ImageChops.invert(body))
 out=base.copy();out.paste(hat,(0,0),behind)
 tags=Image.new('L',base.size);tags.paste(1,(0,0,*base.size),body);tags.paste(hat_tags,(0,0),behind)
 edit=owned.copy()
 if hair is not None:
  if hair.size!=base.size or hair_visible is None or hair_visible.size!=base.size:raise ValueError('Hair needs explicit same-pose visible mask.')
  if ImageChops.subtract(hair_visible,binary(hair)).getbbox():raise ValueError('Hair mask fabricates pixels.')
  out.paste(hair,(0,0),hair_visible);tags.paste(2,(0,0,*base.size),hair_visible);edit=ImageChops.lighter(edit,hair_visible)
 out.paste(hat,(0,0),front);tags.paste(hat_tags,(0,0),front)
 return out,tags,edit
