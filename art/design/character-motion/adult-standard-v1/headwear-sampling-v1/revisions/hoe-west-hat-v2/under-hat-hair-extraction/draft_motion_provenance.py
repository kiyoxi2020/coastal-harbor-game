"""Hat-compatible source-owned west hoe visible hair; default frozen reconstruction."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import json,hashlib,sys,shutil,importlib.util
P=Path(__file__).resolve().parent;V=P.parent;SRC=V/'under-hat-hair-sources'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
polygons={
0:[(160,320),(626,532),(626,582),(609,586),(607,619),(594,611),(587,633),(579,632),(565,650),(557,644),(548,663),(539,657),(527,677),(521,672),(521,684),(500,686),(491,680),(481,686),(475,679),(468,682),(469,674),(481,656),(490,642),(497,625),(497,602),(490,579),(479,566),(462,553),(445,548),(428,553),(417,563),(410,579),(405,614),(400,618),(397,606),(398,586),(401,574),(405,554),(402,538),(405,523),(407,502),(400,481),(389,496),(380,498),(379,478),(370,465),(362,451),(353,442),(345,436),(332,426),(329,433),(324,435),(313,433),(307,445),(296,443),(283,434),(267,417),(253,405),(244,391),(233,414),(227,436),(226,455),(217,456),(211,449),(205,440),(198,429),(196,420),(194,408),(185,404),(175,408),(167,411),(152,410),(146,405),(154,398),(166,391),(174,376),(182,357)],
2:[(149,377),(623,580),(625,593),(612,610),(613,651),(601,650),(586,669),(584,658),(572,680),(568,677),(558,694),(552,690),(542,708),(535,701),(526,719),(516,718),(509,731),(497,730),(487,740),(476,740),(468,747),(459,744),(449,748),(443,745),(444,737),(457,725),(468,714),(479,696),(489,677),(498,655),(496,635),(490,618),(476,608),(458,602),(439,605),(421,613),(407,628),(397,640),(392,674),(384,675),(381,662),(379,650),(382,639),(381,625),(377,612),(373,615),(365,616),(360,608),(361,590),(361,572),(359,554),(354,536),(348,530),(342,531),(329,520),(320,510),(311,506),(304,503),(300,500),(301,494),(290,492),(280,485),(276,482),(269,480),(268,498),(264,514),(257,519),(254,511),(248,505),(240,500),(232,489),(224,476),(214,470),(209,476),(205,488),(196,499),(188,513),(184,533),(176,534),(168,525),(161,511),(159,497),(154,480),(150,462),(140,455),(126,456),(117,451),(123,444),(134,437),(142,425),(150,409)],
3:[(145,326),(621,533),(620,568),(622,595),(607,599),(609,607),(590,607),(583,625),(572,637),(564,636),(553,651),(544,653),(536,663),(522,666),(513,664),(504,671),(492,670),(483,675),(470,671),(464,675),(454,671),(452,664),(459,657),(471,644),(483,631),(493,610),(493,588),(486,574),(476,563),(460,552),(443,549),(425,555),(411,568),(402,582),(397,605),(392,609),(390,600),(392,582),(394,570),(391,555),(390,542),(394,535),(393,522),(391,505),(381,499),(373,490),(366,476),(354,466),(346,452),(337,441),(324,429),(313,418),(305,409),(299,410),(298,441),(291,440),(286,444),(279,440),(275,431),(273,416),(267,412),(266,445),(265,454),(257,453),(250,448),(244,439),(238,428),(235,414),(229,406),(223,399),(216,405),(211,422),(209,444),(204,463),(197,466),(188,456),(184,443),(178,431),(175,420),(170,423),(165,428),(153,432),(145,430),(143,424),(146,414),(149,395),(151,371),(154,351)]}
# Authored anatomical feature boxes in the returned WINDOW, not inferred from total height.
ears={0:(398,538,510,668),2:(378,598,505,733),3:(388,533,506,664)}
brows={0:(230,458,334,488),2:(210,517,307,543),3:(231,450,327,485)}

def build(i,draft=False):
 pose=f'hoe_west_key_{i}';D=P/pose;D.mkdir(exist_ok=True);H=V/f'extraction/{pose}';srcfile=SRC/f'{pose}-v1-full-frame.png';source=Image.open(srcfile).convert('RGBA');window=Image.open(SRC/f'{pose}-v1-window.png').convert('RGBA');shutil.copyfile(srcfile,D/'source-full-frame.png');wp=window.load();formalnear=Image.open(H/'hat-near.png').convert('RGBA');np=formalnear.load()
 if draft:
  semantic=Image.new('L',window.size);ImageDraw.Draw(semantic).polygon(polygons[i],fill=255);sem=semantic.load();brown=Image.new('L',window.size);bp=brown.load()
  for y in range(310,760):
   for x in range(110,640):
    r,g,b,a=wp[x,y]
    if sem[x,y] and 25<r<190 and 13<g<145 and 1.48*g<r<2.5*g and .42*g<b<.99*g:bp[x,y]=255
  proximity=brown.filter(ImageFilter.MaxFilter(15)).load();tight=brown.filter(ImageFilter.MaxFilter(5)).load();mask=Image.new('L',window.size);mp=mask.load();ex0,ey0,ex1,ey1=ears[i]
  for y in range(310,760):
   for x in range(110,640):
    r,g,b,a=wp[x,y];ear=ex0<=x<=ex1 and ey0<=y<=ey1;forehead_edge=x<215 and y>(545 if i==2 else 475)
    if sem[x,y] and (bp[x,y] or (max(r,g,b)<70 and (tight[x,y] if forehead_edge else proximity[x,y]) and not ear)):mp[x,y]=255
    if np[x+240,y+80][3]>=200 and max(r,g,b)<70:mp[x,y]=0
  bx0,by0,bx1,by1=brows[i]
  for y in range(by0,by1):
   for x in range(bx0,bx1):
    r,g,b,a=wp[x,y]
    if g>55 and r<1.68*g:mp[x,y]=0
  if i==2:
   # The extra stroke lies on generated FOREHEAD SKIN between fringe tips,
   # above the original-body eyebrow; it is not a hair-internal highlight.
   poly=[(252,488),(269,485),(286,491),(305,501),(307,513),(281,509),(258,503),(251,499)]
   ImageDraw.Draw(mask).polygon(poly,fill=0)
  # Source body contour under the visible ear/nape is excluded anatomically;
  # it is not a horizontal cap-volume or compatibility hair trim.
  body_paths={0:[(424,654),(450,654),(460,663),(468,672),(470,682),(474,687),(481,690)],2:[(401,718),(424,716),(439,728),(446,737),(445,743),(450,749)],3:[(425,650),(440,651),(454,656),(458,663),(455,671),(465,677)]}
  ImageDraw.Draw(mask).line(body_paths[i],fill=0,width=7,joint='curve')
  if i==2:ImageDraw.Draw(mask).polygon([(444,741),(461,738),(476,741),(487,747),(487,760),(444,760)],fill=0)
  # Remove disconnected generation/body fragments; real hair blocks are much larger.
  chosen={(x,y) for y in range(310,760) for x in range(110,640) if mp[x,y]};seen=set()
  for seed in list(chosen):
   if seed in seen:continue
   q=[seed];seen.add(seed);c=[]
   while q:
    xx,yy=q.pop();c.append((xx,yy))
    for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)]:
     z=(xx+dx,yy+dy)
     if z in chosen and z not in seen:seen.add(z);q.append(z)
   if len(c)<100:
    for xx,yy in c:mp[xx,yy]=0
  full=Image.new('L',source.size);full.paste(mask,(240,80));m=full.load();rows=[]
  for y in range(source.height):
   runs=[];x=0
   while x<source.width:
    if m[x,y]:
     lo=x
     while x<source.width and m[x,y]:x+=1
     runs.append([lo,x-1])
    else:x+=1
   if runs:rows.append({'y':y,'inclusive_x_runs':runs})
  js(D/'source-contours.json',{'pose_id':pose,'space':'1536x1792 returned source full frame','source_window_return_px':[240,80],'window_return_is_part_registration':False,'source_full_frame_sha256':sha(srcfile),'compatible_hat_manifest_sha256':sha(H/'manifest.json'),'draft_window_anatomical_envelope_px':polygons[i],'generated_ear_arc_window_roi':ears[i],'generated_original_brow_window_roi':brows[i],'extra_generated_forehead_stroke_excluded':i==2,'rows':rows,'authority':'Frozen reviewed rows, not colors, alpha, or a max-y hair trim.'})
 c=json.loads((D/'source-contours.json').read_text());assert c['source_full_frame_sha256']==sha(srcfile) and c['compatible_hat_manifest_sha256']==sha(H/'manifest.json');mask=Image.new('L',source.size);dr=ImageDraw.Draw(mask)
 for row in c['rows']:
  for lo,hi in row['inclusive_x_runs']:dr.line((lo,row['y'],hi,row['y']),fill=255)
 mask.save(D/'source-ownership.png');mask.save(D/'registered-ownership.png');plate=Image.new('RGBA',source.size);plate.paste(source,(0,0),mask);plate.save(D/'hair-registered.png')
 spec=importlib.util.spec_from_file_location('same_v5_composer_motion',V.parent/'run-east-hat-approved-v5/build_approved.py');std=importlib.util.module_from_spec(spec);spec.loader.exec_module(std);body=Image.open(H/'original-body.png').convert('RGBA');far=Image.open(H/'hat-far.png').convert('RGBA');comp,_=std.compose(body,formalnear,far,plate);comp.save(D/'hair-hat-composite.png')
 board=Image.new('RGB',(2520,590),(220,228,234));d=ImageDraw.Draw(board)
 for col,(im,name) in enumerate([(source,'generated source'),(plate,'true source-owned visible hair'),(comp,'formal hat + original body + new hair')]):
  bg=Image.new('RGBA',im.size,(220,228,234,255));bg.alpha_composite(im);crop=bg.crop((340,380 if i==2 else 330,970,840 if i==2 else 800));crop.thumbnail((840,560),Image.Resampling.NEAREST);board.paste(crop.convert('RGB'),(col*840,25));d.text((col*840+3,4),pose+' '+name,fill='black')
 board.save(D/'source-mask-composite-head.png');print(pose,'frozen source view reconstructed at zero part registration')
if __name__=='__main__':
 if '--draft' not in sys.argv or '--allow-replace-frozen' not in sys.argv: raise SystemExit('Draft provenance only; frozen source reconstruction uses extract_motion.py. Explicit replacement requires a new audit.')
 args=[int(x) for x in sys.argv[1:] if not x.startswith('--')]
 for i in args:build(i,'--draft' in sys.argv)
