from pathlib import Path
from PIL import Image,ImageChops
import json,hashlib
A=Path(__file__).resolve().parent;R=A.parents[2];D=['south','west','east','north'];O=A/'second-set-swap';O.mkdir(exist_ok=True)
B=R/'art/design/character-bodies/adult-standard-v1/revisions/directional-brows-v3';C=R/'art/design/character-clothing-proof-v1';H=R/'art/design/character-head-proof-v1/proof'
states=['baseline','top','pants','shoes','top_pants','top_shoes','pants_shoes','top_pants_shoes']
for d in D:
 for state in states:
  im=Image.open(B/(d+'.png')).convert('RGBA')
  for cat in ['pants','top','shoes']:
   new=cat in state.split('_');folder=A/cat/(cat+'02')
   part=Image.open(folder/'components'/(d+'.png') if new else C/'parts'/(cat+'_'+d+'.png')).convert('RGBA')
   owner=Image.open(folder/'owners'/(d+'.png') if new else C/'parts'/(cat+'-owner_'+d+'.png')).convert('L')
   im.paste(part,(0,0),owner)
  im.save(O/(state+'_'+d+'.png'))
  if state=='top_pants_shoes':
   for name in ['full_hair','full_hair_hat']:
    head=Image.open(B/'proof'/((('hair_hat' if name.endswith('_hat') else 'hair'))+'_'+d+'.png')).convert('RGBA');bare=Image.open(B/(d+'.png')).convert('RGBA')
    changed=ImageChops.difference(head,bare).convert('RGB').convert('L').point(lambda x:255 if x else 0)
    out=im.copy();out.paste(head,(0,0),changed);out.save(O/(name+'_'+d+'.png'))
print('32 clothing combinations plus 8 head combinations, fixed original frames')
