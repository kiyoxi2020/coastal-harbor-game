extends RefCounted
## Bounded inspection manifest, using existing action IDs and trial playback.
## Only the five explicitly sampled action/direction pairs gain replacement textures.
const IDS=["walk-west","run-east","hoe-west","water-south","harvest-north"]
var samples:Array=[]
var error:=""
var catalog_sha256:=""
func reject(message:String) -> bool:
 samples.clear();catalog_sha256="";error=message;return false
func relative_file(value) -> bool:
 return value is String and not value.is_empty() and not value.is_absolute_path() and not ".." in value.split("/") and not ":" in value and not "\\" in value
func pair(value) -> bool:
 if not value is Array or value.size()!=2:return false
 for number in value:
  if not number is int and not number is float:return false
  if not is_finite(float(number)):return false
 return true
func read_json(path:String):
 if not FileAccess.file_exists(path):return null
 return JSON.parse_string(FileAccess.get_file_as_string(path))
func load_samples(project:String,path:String) -> bool:
 samples.clear();error="";catalog_sha256=""
 var catalog=read_json(path)
 if not catalog is Dictionary or catalog.get("schema_version")!=1 or catalog.get("scope")!="sampled-not-exhaustive" or not catalog.get("samples") is Array or catalog.samples.size()!=5:return reject("抽样目录必须明确包含五个样例。")
 var pending:Array=[];var seen:Array=[]
 for entry in catalog.samples:
  if not entry is Dictionary or not entry.get("id") in IDS or entry.id in seen or not relative_file(entry.get("sample")):return reject("抽样ID或路径无效。")
  var source:=project.path_join(entry.sample)
  if not FileAccess.file_exists(source) or FileAccess.get_sha256(source)!=entry.get("sha256"):return reject("抽样配置哈希不符。")
  var data=read_json(source)
  if not data is Dictionary or data.get("schema_version")!=1 or data.get("template_id")!="adult-standard-v1" or str(data.get("action_id"))+"-"+str(data.get("direction"))!=entry.id:return reject("动作或母版不符。")
  var recipe=data.get("recipe")
  if not recipe is Dictionary or not recipe.get("slots") is Dictionary:return reject("缺少衣物配方。")
  for slot in ["top","pants","shoes"]:
   if not recipe.slots.get(slot) is String or recipe.slots[slot].is_empty():return reject("缺少槽位："+slot)
  if not pair(data.get("canvas_px")) or not pair(data.get("root_anchor_px")):return reject("缺少画布或根点。")
  var size:=Vector2i(int(data.canvas_px[0]),int(data.canvas_px[1]));var anchor:=Vector2(float(data.root_anchor_px[0]),float(data.root_anchor_px[1]))
  if size.x<=0 or size.y<=0 or anchor.x<0 or anchor.y<0 or anchor.x>size.x or anchor.y>size.y or not data.get("display_scale") is float or data.display_scale<=0:return reject("画布/根点/比例无效。")
  var frames=data.get("frames");var inputs=data.get("inputs")
  if not frames is Array or frames.size()!=4 or not inputs is Dictionary or inputs.is_empty():return reject("必须有四个真实姿态及来源绑定。")
  for rel in inputs:
   if not relative_file(rel) or not FileAccess.file_exists(source.get_base_dir().path_join(rel)) or FileAccess.get_sha256(source.get_base_dir().path_join(rel))!=inputs[rel]:return reject("来源或部件哈希不符。")
  var textures:Array=[];var ids:Array=[];var durations:Array=[]
  for frame in frames:
   if not frame is Dictionary or not frame.get("pose_id") is String or frame.pose_id in ids or not relative_file(frame.get("file")) or not inputs.has(frame.file) or inputs[frame.file]!=frame.get("sha256") or not frame.get("duration_ms") is float and not frame.get("duration_ms") is int:return reject("姿态/纹理/时长无效。")
   if frame.duration_ms<=0:return reject("时长必须为正。")
   var image:=Image.load_from_file(source.get_base_dir().path_join(frame.file))
   if image==null or image.get_size()!=size:return reject("纹理尺寸不符。")
   textures.append(ImageTexture.create_from_image(image));ids.append(frame.pose_id);durations.append(frame.duration_ms)
  var idle=data.get("idle")
  if not idle is Dictionary or not relative_file(idle.get("file")) or not inputs.has(idle.file) or inputs[idle.file]!=idle.get("sha256") or not pair(idle.get("canvas_px")) or not pair(idle.get("root_anchor_px")) or idle.get("pose_id")!="idle_"+str(data.direction)+"_0":return reject("缺少同配方站姿。")
  if not idle.get("display_scale") is float and not idle.get("display_scale") is int:return reject("站姿比例无效。")
  if not is_finite(float(idle.display_scale)) or float(idle.display_scale)<=0 or idle.canvas_px[0]<=0 or idle.canvas_px[1]<=0 or idle.root_anchor_px[0]<0 or idle.root_anchor_px[1]<0 or idle.root_anchor_px[0]>idle.canvas_px[0] or idle.root_anchor_px[1]>idle.canvas_px[1]:return reject("站姿登记无效。")
  var idle_image:=Image.load_from_file(source.get_base_dir().path_join(idle.file))
  if idle_image==null or idle_image.get_size()!=Vector2i(int(idle.canvas_px[0]),int(idle.canvas_px[1])):return reject("站姿尺寸不符。")
  pending.append({"id":entry.id,"data":data,"sample_path":source,"sample_sha256":entry.sha256,"textures":textures,"pose_ids":ids,"durations_ms":durations,"canvas_px":Vector2(size),"root_anchor_px":anchor,"display_scale":float(data.display_scale),"idle_texture":ImageTexture.create_from_image(idle_image)})
  seen.append(entry.id)
 samples=pending;catalog_sha256=FileAccess.get_sha256(path);return true
