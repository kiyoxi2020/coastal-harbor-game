extends RefCounted
const ResourcePaths = preload("res://dev/characters/character_resource_paths.gd")
## Bounded headwear views. Everything resolves against an exact accepted pose.
const IDS=["run-east","hoe-west","water-south","harvest-north"]
const STATES=["bare","hair","hat","hair_hat"]
var samples:Array=[]
var error:=""
var catalog_sha256:=""
func reject(message:String) -> bool:
 samples.clear();catalog_sha256="";error=message;return false
func relative_file(value: Variant) -> bool:
 return ResourcePaths.relative_file(value)

func number(value) -> bool:
 return (value is int or value is float) and is_finite(float(value))
func geometry(data) -> bool:
 if not data is Dictionary:return false
 for key in ["canvas_px","root_anchor_px"]:
  if not data.get(key) is Array or data[key].size()!=2:return false
  for value in data[key]:
   if not number(value):return false
 for value in data.canvas_px:
  if value<=0 or value!=floor(value):return false
 if data.root_anchor_px[0]<0 or data.root_anchor_px[1]<0 or data.root_anchor_px[0]>data.canvas_px[0] or data.root_anchor_px[1]>data.canvas_px[1]:return false
 return number(data.get("display_scale")) and data.display_scale>0
func same_geometry(left:Dictionary,right:Dictionary) -> bool:
 return geometry(left) and geometry(right) and left.canvas_px==right.canvas_px and left.root_anchor_px==right.root_anchor_px and is_equal_approx(float(left.display_scale),float(right.display_scale))
func read_json(path:String):
 if not FileAccess.file_exists(path):return null
 return JSON.parse_string(FileAccess.get_file_as_string(path))
func dependencies(base:String,data:Dictionary) -> bool:
 if not data.get("inputs") is Dictionary or data.inputs.is_empty():return false
 for path in data.inputs:
  if not relative_file(path) or not data.inputs[path] is String or not FileAccess.file_exists(base.path_join(path)) or FileAccess.get_sha256(base.path_join(path))!=data.inputs[path]:return false
 return true
func state_textures(base:String,frame:Dictionary,inputs:Dictionary,size:Vector2i) -> Dictionary:
 if not frame.get("states") is Dictionary or frame.states.size()!=STATES.size():return {}
 var result:Dictionary={}
 for state in STATES:
  var entry=frame.states.get(state)
  if not entry is Dictionary or not relative_file(entry.get("file")) or not inputs.has(entry.file) or entry.get("sha256")!=inputs[entry.file]:return {}
  var picture:=Image.load_from_file(base.path_join(entry.file))
  if picture==null or picture.get_size()!=size:return {}
  result[state]=ImageTexture.create_from_image(picture)
 return result
func load_samples(project:String,path:String) -> bool:
 samples.clear();error="";catalog_sha256=""
 var catalog=read_json(path)
 if not catalog is Dictionary or catalog.get("schema_version")!=1 or catalog.get("template_id")!="adult-standard-v1" or catalog.get("scope")!="sampled-headwear-not-exhaustive" or not catalog.get("samples") is Array or catalog.samples.size()!=IDS.size():return reject("发帽目录必须明确包含四个抽样。")
 if ResourcePaths.base(project,path,catalog).is_empty():return reject("发帽目录资源根无效。")
 var pending:Array=[];var seen:Array=[]
 for entry in catalog.samples:
  if not entry is Dictionary or not entry.get("id") in IDS or entry.id in seen or not relative_file(entry.get("sample")):return reject("发帽ID或路径无效。")
  var source:=project.path_join(entry.sample);var data=read_json(source)
  if not data is Dictionary or FileAccess.get_sha256(source)!=entry.get("sha256") or data.get("schema_version")!=1 or data.get("template_id")!="adult-standard-v1" or str(data.get("action_id"))+"-"+str(data.get("direction"))!=entry.id:return reject("发帽来源或母版不符。")
  if catalog.has("resource_root") and not data.has("resource_root"):return reject("发帽资源根缺失。")
  var base:=ResourcePaths.base(project,source,data)
  if base.is_empty():return reject("发帽资源根无效。")
  if not relative_file(data.get("parent_sample")):return reject("原衣装路径无效。")
  var parent_path:=project.path_join(data.parent_sample);var parent=read_json(parent_path)
  if not parent is Dictionary or FileAccess.get_sha256(parent_path)!=data.get("parent_sha256"):return reject("原衣装依赖或哈希失效。")
  if data.has("resource_root") and not parent.has("resource_root"):return reject("原衣装资源根缺失。")
  var parent_base:=ResourcePaths.base(project,parent_path,parent)
  if parent_base.is_empty() or not dependencies(parent_base,parent):return reject("原衣装资源根或依赖失效。")
  if not same_geometry(data,parent) or not dependencies(base,data):return reject("发帽登记或依赖不符。")
  if not data.get("frames") is Array or data.frames.size()!=4 or not parent.get("frames") is Array or parent.frames.size()!=4 or not data.get("idle") is Dictionary or not parent.get("idle") is Dictionary:return reject("发帽必须有四姿态及同配方站姿。")
  var textures:Dictionary={};var idle_textures:Dictionary={};var poses:Array=[];var durations:Array=[]
  for state in STATES:textures[state]=[]
  for index in range(4):
   var frame=data.frames[index];var original=parent.frames[index]
   if not frame is Dictionary or not original is Dictionary or not frame.get("pose_id") is String or frame.pose_id in poses or frame.pose_id!=original.get("pose_id") or not number(frame.get("duration_ms")) or frame.duration_ms<=0 or frame.duration_ms!=floor(frame.duration_ms) or frame.duration_ms!=original.get("duration_ms"):return reject("发帽姿态/时序不符。")
   var views:=state_textures(base,frame,data.inputs,Vector2i(int(data.canvas_px[0]),int(data.canvas_px[1])))
   if views.is_empty():return reject("发帽状态/纹理不完整。")
   if frame.states.bare.sha256!=original.get("sha256"):return reject("裸头状态必须保持原衣装纹理。")
   for state in STATES:textures[state].append(views[state])
   poses.append(frame.pose_id);durations.append(frame.duration_ms)
  if data.idle.get("pose_id")!="idle_"+str(data.direction)+"_0" or data.idle.get("pose_id")!=parent.idle.get("pose_id") or not same_geometry(data.idle,parent.idle):return reject("站姿登记不符。")
  idle_textures=state_textures(base,data.idle,data.inputs,Vector2i(int(data.idle.canvas_px[0]),int(data.idle.canvas_px[1])))
  if idle_textures.is_empty() or data.idle.states.bare.sha256!=parent.idle.get("sha256"):return reject("站姿发帽状态不符。")
  pending.append({"id":entry.id,"data":data,"sample_sha256":entry.sha256,"sample_path":source,"textures_by_state":textures,"idle_by_state":idle_textures,"pose_ids":poses,"durations_ms":durations,"canvas_px":Vector2(data.canvas_px[0],data.canvas_px[1]),"root_anchor_px":Vector2(data.root_anchor_px[0],data.root_anchor_px[1]),"display_scale":float(data.display_scale)})
  seen.append(entry.id)
 samples=pending;catalog_sha256=FileAccess.get_sha256(path);return true
