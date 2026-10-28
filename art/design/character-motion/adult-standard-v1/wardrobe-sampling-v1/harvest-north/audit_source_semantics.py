"""Source semantic gate at manually reviewed neckline/cuff regions.

Peach skin belongs to shared same-pose foreground, never a garment surface.
The numeric diagnostic supplements the retained enlarged visual source review.
"""
from pathlib import Path
from PIL import Image
import json,sys

def audit(directory):
    d=Path(directory);rows=[]
    for phase in ['ready','reach','pluck','recovery','idle']:
        raw=Image.open(d/f'parts/{phase}/top-complete-source.png').convert('RGBA')
        top=Image.open(d/f'masks/{phase}-top-visible-coverage.png').convert('L')
        points=[]
        for y in range(raw.height):
            for x in range(raw.width):
                r,g,b,a=raw.getpixel((x,y))
                if top.getpixel((x,y)) and r>220 and g>140 and 80<b<180 and r-g>35:points.append((x,y))
        rows.append({'phase':phase,'new_peach_pixels_owned_by_top':len(points),'bbox_px':[min(x for x,y in points),min(y for x,y in points),max(x for x,y in points)+1,max(y for x,y in points)+1] if points else None})
    return {'classification':'actual top slot inside visible ownership; manual-reviewed peach incursions R>220,G>140,80<B<180,R-G>35; rejected unused raw red tops are not adopted','poses':rows,'passed':all(not r['new_peach_pixels_owned_by_top'] for r in rows)}
if __name__=='__main__':
    result=audit(sys.argv[1]);print(json.dumps(result,indent=2));sys.exit(0 if result['passed'] else 1)
