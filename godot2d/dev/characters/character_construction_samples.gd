extends RefCounted
## Strict, bounded consumer for four offline construction builds. Python verify
## remains responsible for reconstructing source pixels; this consumer binds all
## current inputs and validates every displayed output independently.
const Paths=preload("res://dev/characters/character_resource_paths.gd")
const STATES=["bare","hair","hat","hair_hat"]
const KIND="coastal-character-construction-review-v1"
var samples:Array=[]
var error:=""
var catalog_sha256:=""
var suite_kind:=""
var manifest_bindings:Dictionary={}
func reject(message:String) -> bool:
 samples.clear();catalog_sha256="";suite_kind="";manifest_bindings.clear();error=message;return false
func exact(value:Variant,fields:String) -> bool:
 if not value is Dictionary:return false
 var wanted=fields.split(" ",false)
 if value.size()!=wanted.size():return false
 for field in wanted:
  if not value.has(field):return false
 return true
func integer(value:Variant,minimum:int=0) -> bool:
 return (value is int or value is float) and not value is bool and is_finite(float(value)) and value>=minimum and float(value)==floor(float(value))
func number(value:Variant) -> bool:
 return (value is int or value is float) and not value is bool and is_finite(float(value))
func digest(value:Variant) -> bool:
 if not value is String or value.length()!=64:return false
 for c in value:
  if not c in "0123456789abcdef":return false
 return true
func bytes_hash(bytes:PackedByteArray) -> String:
 var h=HashingContext.new();h.start(HashingContext.HASH_SHA256);h.update(bytes);return h.finish().hex_encode()
func no_links(path:String) -> bool:
 if not path.is_absolute_path():return false
 var current="/"
 for component in path.split("/",false):
  var parent=DirAccess.open(current)
  if parent==null or parent.is_link(component):return false
  current=current.path_join(component)
 return true
func safe_file(root_path:String,relative:Variant,prefix:String="") -> String:
 if not Paths.relative_file(relative) or (prefix!="" and not relative.begins_with(prefix+"/")):return ""
 var result=root_path.path_join(relative)
 if not no_links(result) or not FileAccess.file_exists(result):return ""
 return result
func read_json(path:String) -> Variant:
 if path=="":return null
 var parser=JSON.new()
 if parser.parse(FileAccess.get_file_as_string(path))!=OK:return null
 return parser.data
func geometry(data:Variant) -> bool:
 if not data is Dictionary:return false
 for key in ["canvas_px","root_anchor_px"]:
  if not data.get(key) is Array or data[key].size()!=2:return false
 for value in data.canvas_px:
  if not integer(value,1):return false
 for i in range(2):
  if not number(data.root_anchor_px[i]) or data.root_anchor_px[i]<0 or data.root_anchor_px[i]>data.canvas_px[i]:return false
 return number(data.get("display_scale")) and data.display_scale>0
func ref_valid(library:String,value:Variant,inputs:Dictionary,prefix:String="") -> bool:
 if not exact(value,"file sha256") or not digest(value.sha256):return false
 var path=safe_file(library,value.file,prefix)
 return path!="" and inputs.get(value.file)==value.sha256 and FileAccess.get_sha256(path)==value.sha256
func references_bound(library:String,value:Variant,inputs:Dictionary) -> bool:
 if value is Dictionary:
  if exact(value,"file sha256"):return ref_valid(library,value,inputs)
  for v in value.values():
   if not references_bound(library,v,inputs):return false
 elif value is Array:
  for v in value:
   if not references_bound(library,v,inputs):return false
 return true
func engine_valid(project:String,value:Variant) -> bool:
 if not exact(value,"pillow code") or not value.pillow is String or value.pillow.is_empty() or not value.code is Dictionary:return false
 if not exact(value.code,"build.py build_contract.py composition_contract.py"):return false
 for filename in value.code:
  if not filename is String or filename.contains("/") or not filename.ends_with(".py") or not digest(value.code[filename]):return false
  var path=safe_file(project.path_join("tools/characters"),filename)
  if path=="" or FileAccess.get_sha256(path)!=value.code[filename]:return false
 return true
func base_valid(base:Variant) -> bool:
 if not exact(base,"kind schema_version resource_root character_model_id recipe_id revision template motion_set slots required_capabilities clips authoring_inputs"):return false
 if base.kind!="coastal-character-construction-v1" or not integer(base.schema_version,1) or base.schema_version!=1 or base.resource_root!="art/characters" or base.character_model_id!="unified-composable-character-v1":return false
 if not base.recipe_id is String or not base.revision is String or not base.clips is Array or base.clips.size()!=2:return false
 if not exact(base.template,"file sha256") or base.template.file!="templates/adult-standard-v1/template.json" or not exact(base.motion_set,"file sha256") or base.motion_set.file!="templates/adult-standard-v1/motions/review-motion-v1/motion-set.json":return false
 if not exact(base.slots,"body top pants shoes") or base.slots.body!=null:return false
 for slot in ["top","pants","shoes"]:
  var design="top03" if slot=="top" else "original-"+slot
  if not exact(base.slots[slot],"file sha256") or base.slots[slot].file!="parts/"+design+"/design.json":return false
 if not base.required_capabilities is Array or base.required_capabilities!=[{"action_id":"hoe","direction":"west"},{"action_id":"idle","direction":"west"}] or not base.authoring_inputs is Array or base.authoring_inputs.is_empty():return false
 var actions:Array=[]
 for clip in base.clips:
  if not exact(clip,"action_id direction canvas_px root_anchor_px display_scale action poses variant frames") or not geometry(clip):return false
  if not clip.action_id in ["hoe","idle"] or clip.action_id in actions or clip.direction!="west" or not clip.frames is Array:return false
  actions.append(clip.action_id)
  if clip.frames.size()!=(4 if clip.action_id=="hoe" else 1):return false
  for i in range(clip.frames.size()):
   var frame=clip.frames[i]
   if not exact(frame,"pose_id duration_ms layers layer_order registration composition"):return false
   var pose="hoe_west_key_"+str(i) if clip.action_id=="hoe" else "idle_west_0"
   if frame.pose_id!=pose or not integer(frame.duration_ms,1):return false
 return actions==["hoe","idle"]
func template_clip_valid(library:String,clip:Dictionary,inputs:Dictionary) -> bool:
 if not ref_valid(library,clip.action,inputs,"templates") or not ref_valid(library,clip.poses,inputs,"templates") or not clip.variant is String:return false
 var action=read_json(safe_file(library,clip.action.file,"templates"))
 var poses=read_json(safe_file(library,clip.poses.file,"templates"))
 if not action is Dictionary or action.get("action_id")!=clip.action_id or not action.get("directions") is Dictionary or action.directions.get(clip.direction)!=clip.poses.file:return false
 if not poses is Dictionary or poses.get("template_id")!="adult-standard-v1" or poses.get("action_id")!=clip.action_id or poses.get("direction")!=clip.direction or not poses.get("variants") is Dictionary or not poses.variants.has(clip.variant):return false
 var variant=poses.variants[clip.variant]
 if not geometry(variant) or not variant.get("frames") is Array or variant.frames.size()!=clip.frames.size():return false
 for field in ["canvas_px","root_anchor_px","display_scale"]:
  if variant[field]!=clip[field]:return false
 for i in range(clip.frames.size()):
  var original=variant.frames[i]
  if not original is Dictionary or original.get("pose_id")!=clip.frames[i].pose_id or not integer(original.get("duration_ms"),1) or original.duration_ms!=clip.frames[i].duration_ms:return false
 return true
func head_slots_valid(library:String,slots:Variant,state:String,inputs:Dictionary) -> bool:
 var fields="" if state=="bare" else "hair" if state=="hair" else "hat" if state=="hat" else "hair hat"
 if not exact(slots,fields):return false
 for slot in slots:
  var design="hair-chestnut-short-v1" if slot=="hair" else "hat-straw-navy-band-v1"
  if not ref_valid(library,slots[slot],inputs,"parts") or slots[slot].file!="parts/"+design+"/design.json":return false
 return true
func matching_head_clips(library:String,head:Variant,base_clips:Array,state:String,inputs:Dictionary) -> bool:
 if not head is Array or head.size()!=base_clips.size():return false
 for i in range(head.size()):
  var clip=head[i];var original:Dictionary=base_clips[i]
  if not exact(clip,"action_id direction frames") or clip.action_id!=original.action_id or clip.direction!=original.direction or not clip.frames is Array or clip.frames.size()!=original.frames.size():return false
  for j in range(clip.frames.size()):
   var frame=clip.frames[j]
   if not exact(frame,"pose_id operation layers layer_order") or frame.pose_id!=original.frames[j].pose_id:return false
   var expected="none" if state=="bare" else "binary-rgba-replace" if state=="hair" else "supported-alpha-stack"
   var order=["base"] if state=="bare" else ["base","hair"] if state=="hair" else ["far_hat","base","near_hat"] if state=="hat" else ["far_hat","base","under_hat_hair","near_hat"]
   if frame.operation!=expected or not frame.layers is Array or frame.layers.size()!=order.size()-1 or frame.layer_order!=order:return false
   var seen:Array=[]
   for layer in frame.layers:
    if not exact(layer,"id slot texture registration provenance") or not layer.id is String or layer.id=="base" or not layer.id in order or layer.id in seen:return false
    var slot="hat" if layer.id in ["far_hat","near_hat"] else "hair"
    if layer.slot!=slot or not ref_valid(library,layer.texture,inputs) or not layer.registration is Dictionary or not layer.provenance is Dictionary:return false
    seen.append(layer.id)
 return true
func output_texture(build_dir:String,entry:Variant,clip:Dictionary,frame:Dictionary) -> Texture2D:
 if not exact(entry,"file sha256 rgba_sha256 size") or not digest(entry.sha256) or not digest(entry.rgba_sha256):return null
 var expected="frames/"+clip.action_id+"/"+clip.direction+"/"+frame.pose_id+".png"
 if entry.file!=expected or entry.size!=clip.canvas_px:return null
 var path=safe_file(build_dir,entry.file,"frames")
 if path=="" or FileAccess.get_sha256(path)!=entry.sha256:return null
 var raw=FileAccess.get_file_as_bytes(path)
 if raw.size()<24 or raw.slice(0,8)!=PackedByteArray([137,80,78,71,13,10,26,10]):return null
 var picture=Image.new()
 if picture.load_png_from_buffer(raw)!=OK or picture.get_size()!=Vector2i(int(clip.canvas_px[0]),int(clip.canvas_px[1])) or picture.get_format()!=Image.FORMAT_RGBA8:return null
 if bytes_hash(picture.get_data())!=entry.rgba_sha256:return null
 return ImageTexture.create_from_image(picture)
func load_samples(project:String,path:String) -> bool:
 reject("")
 if ".." in project.split("/") or "." in project.split("/") or "\\" in project or ":" in project:return reject("构建项目路径不允许父级跳转。")
 project=project.simplify_path()
 if not no_links(project):return reject("构建项目路径包含链接或无效。")
 var library=project.path_join("art/characters")
 if not path.begins_with(project+"/"):return reject("构建评审目录越界。")
 var suite_path=safe_file(project,path.trim_prefix(project+"/"),"art/characters/reviews")
 var suite=read_json(suite_path)
 if not exact(suite,"kind schema_version resource_root scope sample_id states") or suite.kind!=KIND or not integer(suite.schema_version,1) or suite.schema_version!=1 or suite.resource_root!="art/characters" or suite.scope!="review-only" or suite.sample_id!="hoe-west" or not exact(suite.states,"bare hair hat hair_hat"):return reject("构建评审范围或四状态不完整。")
 var textures:Dictionary={};var idle_textures:Dictionary={};var bindings:Dictionary={};var frozen_base:Dictionary={};var frozen_ref:Dictionary={}
 for state in STATES:
  var binding=suite.states[state]
  if not exact(binding,"manifest sha256") or not digest(binding.sha256):return reject("构建manifest绑定无效。")
  var manifest_path=safe_file(project,binding.manifest,"art/characters/builds")
  if manifest_path=="" or manifest_path.get_file()!="manifest.json" or manifest_path.get_base_dir().get_base_dir()!=library.path_join("builds") or FileAccess.get_sha256(manifest_path)!=binding.sha256:return reject("构建manifest路径或哈希失效。")
  var manifest=read_json(manifest_path)
  if not exact(manifest,"kind schema_version status release_eligible recipe artifact_digest inputs engine outputs") or manifest.kind!="coastal-character-review-build-v1" or not integer(manifest.schema_version,1) or manifest.schema_version!=1 or manifest.status!="review-only" or not manifest.release_eligible is bool or manifest.release_eligible!=false:return reject("构建只能是严格review-only manifest。")
  if not manifest.inputs is Dictionary or manifest.inputs.is_empty() or not engine_valid(project,manifest.engine):return reject("构建来源或当前engine代码失效。")
  for file in manifest.inputs:
   var input_path=safe_file(library,file)
   if input_path=="" or not digest(manifest.inputs[file]) or FileAccess.get_sha256(input_path)!=manifest.inputs[file]:return reject("构建来源输入失效。")
  if not digest(manifest.artifact_digest) or bytes_hash(JSON.stringify({"inputs":manifest.inputs,"engine":manifest.engine},"",true).to_utf8_buffer())!=manifest.artifact_digest:return reject("构建artifact digest失效。")
  var recipe_path=safe_file(library,manifest.recipe,"recipes");var recipe=read_json(recipe_path)
  if not exact(recipe,"kind schema_version resource_root character_model_id recipe_id revision base_recipe head_state slots clips authoring_inputs") or recipe.kind!="coastal-character-construction-v1" or not integer(recipe.schema_version,1) or recipe.schema_version!=2 or recipe.resource_root!="art/characters" or recipe.character_model_id!="unified-composable-character-v1" or recipe.head_state!=state:return reject("构建配方schema或头部状态不符。")
  if not head_slots_valid(library,recipe.slots,state,manifest.inputs):return reject("构建头部槽位或设计绑定不符。")
  if not recipe.slots is Dictionary or not recipe.authoring_inputs is Array:return reject("构建配方槽位或authoring输入类型无效。")
  if not recipe.recipe_id is String or not recipe.revision is String or manifest.recipe!="recipes/"+recipe.recipe_id+"/"+recipe.revision+".json" or manifest.inputs.get(manifest.recipe)!=FileAccess.get_sha256(recipe_path):return reject("构建配方身份或输入绑定不符。")
  for authoring in recipe.authoring_inputs:
   if not ref_valid(library,authoring,manifest.inputs):return reject("构建authoring输入绑定无效。")
  if not ref_valid(library,recipe.base_recipe,manifest.inputs,"recipes") or not references_bound(library,recipe,manifest.inputs):return reject("构建base或部件输入绑定失效。")
  var base=read_json(safe_file(library,recipe.base_recipe.file,"recipes"))
  if not base_valid(base) or not references_bound(library,base,manifest.inputs) or not matching_head_clips(library,recipe.clips,base.clips,state,manifest.inputs):return reject("构建base姿态/时序/几何不符。")
  for clip in base.clips:
   if not template_clip_valid(library,clip,manifest.inputs):return reject("构建base与真实模板variant不符。")
  if frozen_base.is_empty():frozen_base=base;frozen_ref=recipe.base_recipe
  elif frozen_base!=base or frozen_ref!=recipe.base_recipe:return reject("四状态必须引用同一base。")
  if not manifest.outputs is Array or manifest.outputs.size()!=5:return reject("构建必须包含四姿态与idle。")
  textures[state]=[];var output_index=0
  for clip in base.clips:
   for frame in clip.frames:
    var texture=output_texture(manifest_path.get_base_dir(),manifest.outputs[output_index],clip,frame)
    if texture==null:return reject("构建PNG/尺寸/RGBA/输出姿态不符。")
    if clip.action_id=="idle":idle_textures[state]=texture
    else:textures[state].append(texture)
    output_index+=1
  bindings[state]={"manifest":binding.manifest,"sha256":binding.sha256,"recipe":manifest.recipe,"recipe_sha256":manifest.inputs[manifest.recipe],"artifact_digest":manifest.artifact_digest}
 var motion:Dictionary=frozen_base.clips[0];var idle:Dictionary=frozen_base.clips[1];var poses:Array=[];var durations:Array=[]
 for frame in motion.frames:poses.append(frame.pose_id);durations.append(frame.duration_ms)
 var data={"template_id":"adult-standard-v1","action_id":"hoe","direction":"west","recipe":{"slots":{"top":"top03","pants":"original-pants","shoes":"original-shoes"}},"idle":{"pose_id":"idle_west_0","canvas_px":idle.canvas_px,"root_anchor_px":idle.root_anchor_px,"display_scale":idle.display_scale},"canvas_px":motion.canvas_px,"root_anchor_px":motion.root_anchor_px,"display_scale":motion.display_scale}
 catalog_sha256=FileAccess.get_sha256(suite_path);suite_kind=KIND;manifest_bindings=bindings
 samples=[{"id":"hoe-west","data":data,"sample_sha256":catalog_sha256,"sample_path":suite_path,"textures_by_state":textures,"idle_by_state":idle_textures,"pose_ids":poses,"durations_ms":durations,"canvas_px":Vector2(motion.canvas_px[0],motion.canvas_px[1]),"root_anchor_px":Vector2(motion.root_anchor_px[0],motion.root_anchor_px[1]),"display_scale":float(motion.display_scale),"manifest_bindings":bindings}]
 error="";return true
