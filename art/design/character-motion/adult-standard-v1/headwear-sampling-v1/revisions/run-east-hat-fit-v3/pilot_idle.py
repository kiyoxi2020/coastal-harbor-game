"""One-pose fitted-source proof. Not an active catalog or final motion delivery."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json,hashlib
P=Path(__file__).resolve().parent;BASE=P.parents[1]/'run-east'
def mask(size,points):
 m=Image.new('L',size);ImageDraw.Draw(m).polygon(points,fill=255);return m
def binary(im):return im.getchannel('A').point(lambda a:255 if a else 0)
def main():
 src=Image.open(P/'sources/idle-fitted-normalized.png').convert('RGBA');base=Image.open(BASE/'references/idle_east_0-bare.png').convert('RGBA')
 points=[(103,312),(113,297),(136,278),(145,273),(137,254),(130,239),(130,212),(140,192),(157,174),(177,157),(197,144),(215,133),(236,121),(253,116),(271,116),(275,121),(297,123),(319,136),(333,152),(343,170),(351,190),(369,192),(396,193),(416,199),(427,205),(427,217),(417,230),(400,242),(381,251),(369,255),(367,226),(341,233),(312,244),(281,254),(251,265),(220,276),(191,286),(167,296),(165,307),(170,319),(167,329),(153,332),(120,332),(111,327),(104,321)]
 own=mask(src.size,points);alpha=src.getchannel('A').point(lambda a:255 if a>=220 else 0);own=ImageChops.darker(own,alpha)
 part=Image.new('RGBA',src.size);part.paste(src,(0,0),own)
 # Actual same-pose ear arch apex, measured in the original and wearing reference.
 offset=(-2,-16);registered=Image.new('RGBA',base.size);registered.paste(part,offset)
 rear_local=mask(src.size,[(367,226),(427,205),(435,260),(367,263)])
 rear=Image.new('L',base.size);rear.paste(ImageChops.darker(rear_local,own),offset);front=ImageChops.subtract(binary(registered),rear)
 out=base.copy();behind=ImageChops.multiply(rear,ImageChops.invert(binary(base)));out.paste(registered,(0,0),behind);out.paste(registered,(0,0),front)
 own.save(P/'idle-source-ownership.png');part.save(P/'idle-hat-source-part.png');registered.save(P/'idle-hat-registered.png');front.save(P/'idle-hat-front.png');rear.save(P/'idle-hat-rear.png');out.save(P/'idle-hat-proof.png')
 # No new anatomy is used. All non-hat pixels, including transparent RGB, exact.
 edit=ImageChops.lighter(front,rear)
 for ch in ImageChops.difference(base,out).split():assert not ImageChops.multiply(ch,ImageChops.invert(edit)).getbbox()
 meta={'status':'single-pose-intermediate-proof-not-active','whole_source_density_projection':[1024,1536,512,768],'head_registration':{'source_ear_arch_px':[233,298],'target_ear_arch_px':[231,282],'integer_offset_px':list(offset)},'source_ownership_polygon':points,'layer_order':['far_brim','exact_same_pose_body','crown_and_near_brim'],'body_pixels_generated':False,'user_accepted':False}
 (P/'pilot.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
