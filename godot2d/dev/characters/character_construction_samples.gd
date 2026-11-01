extends RefCounted
## Strict, bounded consumer for four offline construction builds. Python verify
## remains responsible for reconstructing source pixels; this consumer binds all
## current inputs and validates every displayed output independently.
const Paths=preload("res://dev/characters/character_resource_paths.gd")
const STATES=["bare","hair","hat","hair_hat"]
const KIND="coastal-character-construction-review-v1"
const CANDIDATE_KIND="coastal-character-construction-candidate-v1"
var samples:Array=[]
var error:=""
var catalog_sha256:=""
var suite_kind:=""
var manifest_bindings:Dictionary={}
var full_package:=false
var candidate_package:=false
var full_clips:Dictionary={}
var canonical_idle:Dictionary={}
var runtime:Dictionary={}
func uniform_pair(value:Variant,expected:float) -> bool:
 return value is Array and value.size()==2 and number(value[0]) and number(value[1]) and float(value[0])==expected and float(value[1])==expected
func reject(message:String) -> bool:
 samples.clear();catalog_sha256="";suite_kind="";manifest_bindings.clear();full_package=false;candidate_package=false;full_clips.clear();canonical_idle.clear();runtime.clear();error=message;return false
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
func output_geometry(canonical:Dictionary,head:Dictionary) -> Dictionary:
 if not head.has("output_padding_px"):return canonical
 var pad=head.output_padding_px
 if not pad is Array or pad.size()!=4:return {}
 for value in pad:
  if not integer(value,0) or value>512:return {}
 var result=canonical.duplicate(false)
 result.canvas_px=[canonical.canvas_px[0]+pad[0]+pad[2],canonical.canvas_px[1]+pad[1]+pad[3]]
 result.root_anchor_px=[canonical.root_anchor_px[0]+pad[0],canonical.root_anchor_px[1]+pad[1]]
 return result
func ref_valid(library:String,value:Variant,inputs:Dictionary,prefix:String="") -> bool:
 if not exact(value,"file sha256") or not digest(value.sha256):return false
 var path=safe_file(library,value.file,prefix)
 return path!="" and inputs.get(value.file)==value.sha256 and FileAccess.get_sha256(path)==value.sha256
func references_bound(library:String,value:Variant,inputs:Dictionary) -> bool:
 return reference_tree_bound(library,value,inputs,{})
func reference_tree_bound(library:String,value:Variant,inputs:Dictionary,visited:Dictionary) -> bool:
 if value is Dictionary:
  if exact(value,"document record"):
   if not ref_valid(library,value.document,inputs) or not value.record is String:return false
   var document=read_json(safe_file(library,value.document.file))
   if not document is Dictionary:return false
   # Legacy schema2 registration documents have their own bounded validator.
   if document.get("kind")!="coastal-pose-annotations-v1":return true
   if not document.get("records") is Array:return false
   var selected:Array=[]
   for row in document.records:
    if row is Dictionary and row.get("record_id")==value.record:selected.append(row)
   return selected.size()==1 and reference_tree_bound(library,selected[0],inputs,visited)
  if exact(value,"file sha256"):
   if not ref_valid(library,value,inputs):return false
   if value.file.ends_with(".json") and not visited.has(value.file):
    visited[value.file]=true
    var record=read_json(safe_file(library,value.file))
    # Recurse into typed construction records that the mapper consumes.
    # Opaque source bundles may list unused historical assets.
    if record is Dictionary and record.get("kind")=="coastal-character-construction-v1":
     return reference_tree_bound(library,record,inputs,visited)
   return true
  for v in value.values():
   if not reference_tree_bound(library,v,inputs,visited):return false
 elif value is Array:
  for v in value:
   if not reference_tree_bound(library,v,inputs,visited):return false
 return true
func registered_inputs_bound(library:String,recipe:Dictionary,inputs:Dictionary) -> bool:
 if not recipe.get("adaptations") is Dictionary:return false
 var catalogs:Dictionary={};var visited:Dictionary={}
 for slot in recipe.adaptations:
  var ref=recipe.adaptations[slot]
  if not ref_valid(library,ref,inputs,"parts"):return false
  var data=read_json(safe_file(library,ref.file))
  if not data is Dictionary or data.get("kind")!="coastal-registered-adaptations-v1" or not data.get("views") is Array or not data.get("mappings") is Array:return false
  var views:Dictionary={};var mappings:Dictionary={}
  for view in data.views:
   if not view is Dictionary or not view.get("view_id") is String or views.has(view.view_id):return false
   views[view.view_id]=view
  for mapping in data.mappings:
   if not mapping is Dictionary or not mapping.get("mapping_id") is String or mappings.has(mapping.mapping_id):return false
   mappings[mapping.mapping_id]=mapping
  catalogs[slot]={"views":views,"mappings":mappings}
 for clip in recipe.clips:
  if not clip is Dictionary or not clip.get("frames") is Array:return false
  for frame in clip.frames:
   if not frame is Dictionary or not frame.get("layers") is Array:return false
   for layer in frame.layers:
    if not layer is Dictionary or not layer.get("slot") is String:return false
    if layer.slot=="body":continue
    if not catalogs.has(layer.slot) or not exact(layer.get("view_binding"),"view_id mapping_id"):return false
    var binding=layer.view_binding;var catalog:Dictionary=catalogs[layer.slot]
    if not binding.view_id is String or not binding.mapping_id is String or not catalog.views.has(binding.view_id) or not catalog.mappings.has(binding.mapping_id):return false
    var view:Dictionary=catalog.views[binding.view_id];var mapping:Dictionary=catalog.mappings[binding.mapping_id]
    for selector in [view.get("source_pose"),mapping.get("target_pose")]:
     if not exact(selector,"document record") or not ref_valid(library,selector.document,inputs):return false
     var annotation=read_json(safe_file(library,selector.document.file))
     if not annotation is Dictionary or annotation.get("kind")!="coastal-pose-annotations-v1":return false
    if mapping.get("view_id")!=binding.view_id or not reference_tree_bound(library,view,inputs,visited) or not reference_tree_bound(library,mapping,inputs,visited):return false
 return true
func fixed_identity_valid(library:String,base:Dictionary,head:Dictionary) -> bool:
 if not exact(base.get("slots"),"body top pants shoes") or not exact(head.get("slots"),"hair hat"):return false
 var template=read_json(safe_file(library,base.template.file,"templates"))
 var motion=read_json(safe_file(library,base.motion_set.file,"templates"))
 if not template is Dictionary or template.get("template_id")!="adult-standard-v1" or not motion is Dictionary or motion.get("motion_set_id")!="review-motion-v1":return false
 var designs={"top":"top03","pants":"original-pants","shoes":"original-shoes","hair":"hair-chestnut-short-v1","hat":"hat-straw-navy-band-v1"}
 for slot in designs:
  var slots:Dictionary=base.slots if slot in ["top","pants","shoes"] else head.slots
  var design=read_json(safe_file(library,slots[slot].file,"parts"))
  if not design is Dictionary or design.get("design_id")!=designs[slot] or design.get("category")!=slot:return false
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
  if not exact(base.slots[slot],"file sha256") or base.slots[slot].file!="parts/"+slot+"/"+design+"/design.json":return false
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
func template_clip_valid(library:String,clip:Dictionary,inputs:Dictionary,expected_template:String="adult-standard-v1") -> bool:
 if not ref_valid(library,clip.action,inputs,"templates") or not ref_valid(library,clip.poses,inputs,"templates") or not clip.variant is String:return false
 var action=read_json(safe_file(library,clip.action.file,"templates"))
 var poses=read_json(safe_file(library,clip.poses.file,"templates"))
 if not action is Dictionary or action.get("action_id")!=clip.action_id or not action.get("directions") is Dictionary or action.directions.get(clip.direction)!=clip.poses.file:return false
 if not poses is Dictionary or poses.get("template_id")!=expected_template or poses.get("action_id")!=clip.action_id or poses.get("direction")!=clip.direction or not poses.get("variants") is Dictionary or not poses.variants.has(clip.variant):return false
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
  if not ref_valid(library,slots[slot],inputs,"parts") or slots[slot].file!="parts/"+slot+"/"+design+"/design.json":return false
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
 if suite is Dictionary and suite.get("kind")==CANDIDATE_KIND:
  return load_full_suite(project,library,suite_path,suite,true)
 if suite is Dictionary and integer(suite.get("schema_version"),1) and suite.schema_version==2:
  return load_full_suite(project,library,suite_path,suite)
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

func head_frame_shape_valid(frame:Variant,pose_id:String) -> bool:
 if not frame is Dictionary:return false
 var foreground=frame.has("base_foreground")
 if not exact(frame,"pose_id operation layers layer_order compatibility"+(" base_foreground" if foreground else "")) or frame.pose_id!=pose_id or frame.operation!="supported-alpha-stack" or not frame.layers is Array:return false
 var near=["base","under_hat_hair","near_hat"];var far=["far_hat","base","under_hat_hair","near_hat"]
 if foreground:near.append("base_foreground");far.append("base_foreground")
 if not frame.layer_order in [near,far] or frame.layers.size()!=frame.layer_order.size()-(2 if foreground else 1):return false
 if not exact(frame.compatibility,"hat_source hat_ownership hat_identity_sha256") or not digest(frame.compatibility.hat_identity_sha256):return false
 var seen:Array=[]
 for layer in frame.layers:
  if not layer is Dictionary or not layer.get("id") in ["far_hat","under_hat_hair","near_hat"] or not layer.id in frame.layer_order or layer.id in seen:return false
  seen.append(layer.id)
 return true

func foreground_targets_valid(library:String,binding:Dictionary,frame:Dictionary,adaptations:Dictionary,inputs:Dictionary) -> bool:
 if not exact(binding.get("target_pose"),"document record"):return false
 for layer in frame.layers:
  if not layer is Dictionary or not layer.get("slot") is String or not exact(layer.get("view_binding"),"view_id mapping_id") or not layer.view_binding.mapping_id is String:return false
  if not adaptations.has(layer.slot) or not ref_valid(library,adaptations[layer.slot],inputs,"parts"):return false
  var catalog=read_json(safe_file(library,adaptations[layer.slot].file,"parts"))
  if not catalog is Dictionary or not catalog.get("mappings") is Array:return false
  var selected:Array=[]
  for mapping in catalog.mappings:
   if mapping is Dictionary and mapping.get("mapping_id")==layer.view_binding.mapping_id:selected.append(mapping)
  if selected.size()!=1 or selected[0].get("target_pose")!=binding.target_pose:return false
 return true

func foreground_binding_valid(library:String,binding:Variant,clip:Dictionary,pose_id:String,inputs:Dictionary) -> bool:
 if not exact(binding,"mode target_pose surface_id ownership") or binding.mode!="canonical-rgba-ownership-split" or binding.surface_id!="hands-tools-foreground":return false
 if not exact(binding.ownership,"role mask") or binding.ownership.role!="canonical-foreground-ownership" or not ref_valid(library,binding.ownership.mask,inputs):return false
 var selector=binding.target_pose
 if not exact(selector,"document record") or not selector.record is String or not ref_valid(library,selector.document,inputs,"templates"):return false
 var document=read_json(safe_file(library,selector.document.file,"templates"))
 if not document is Dictionary or document.get("kind")!="coastal-pose-annotations-v1" or document.get("schema_version")!=1 or not document.get("records") is Array:return false
 var selected:Array=[]
 for record in document.records:
  if record is Dictionary and record.get("record_id")==selector.record:selected.append(record)
 if selected.size()!=1:return false
 var row:Dictionary=selected[0]
 if row.get("pose_id")!=pose_id or row.get("poses")!=clip.poses or row.get("variant")!=clip.variant or row.get("canvas_px")!=clip.canvas_px or row.get("root_anchor_px")!=clip.root_anchor_px or row.get("display_scale")!=clip.display_scale:return false
 if not row.get("surfaces") is Dictionary or not exact(row.surfaces.get("hands-tools-foreground"),"layer_id mask") or row.surfaces["hands-tools-foreground"].layer_id!="base" or row.surfaces["hands-tools-foreground"].mask!=binding.ownership.mask:return false
 if not exact(row.surfaces.get("head"),"layer_id mask") or row.surfaces.head.layer_id!="base" or not ref_valid(library,row.surfaces.head.mask,inputs):return false
 # Python reconstructs the RGBA split. The native consumer binds its selected
 # canonical pose and two distinct binary surfaces independently.
 var owner=Image.load_from_file(safe_file(library,binding.ownership.mask.file));var head=Image.load_from_file(safe_file(library,row.surfaces.head.mask.file))
 if owner==null or head==null or owner.get_format()!=Image.FORMAT_L8 or head.get_format()!=Image.FORMAT_L8 or owner.get_size()!=Vector2i(clip.canvas_px[0],clip.canvas_px[1]) or head.get_size()!=owner.get_size():return false
 var owner_bytes=owner.get_data();var head_bytes=head.get_data();var has_owner=false;var has_head=false
 for i in range(owner_bytes.size()):
  if not owner_bytes[i] in [0,255] or not head_bytes[i] in [0,255] or (owner_bytes[i]!=0 and head_bytes[i]!=0):return false
  has_owner=has_owner or owner_bytes[i]!=0;has_head=has_head or head_bytes[i]!=0
 return has_owner and has_head

func load_full_suite(project:String,library:String,suite_path:String,suite:Dictionary,candidate:bool=false) -> bool:
 # Python preflight reconstructs sources. This consumer independently checks
 # the complete input closure, current engine, clip contract and every PNG.
 var fields="kind schema_version resource_root scope head_state manifest samples canonical_idle runtime"+(" capabilities" if candidate else "")
 var expected_kind:=CANDIDATE_KIND if candidate else KIND
 var expected_scope:="internal-review-only" if candidate else "review-only"
 var expected_schema:=1 if candidate else 2
 if not exact(suite,fields) or suite.kind!=expected_kind or not integer(suite.schema_version,1) or suite.schema_version!=expected_schema or suite.resource_root!="art/characters" or suite.scope!=expected_scope or suite.head_state!="hair_hat":return reject("注册动作范围或固定hair_hat无效。")
 var required_count:=24;var claimed:Dictionary={}
 if candidate:
  if not suite.capabilities is Array or suite.capabilities.is_empty() or suite.capabilities.size()>24:return reject("内部验收能力范围缺失。")
  for cap in suite.capabilities:
   if not exact(cap,"action_id direction") or not cap.action_id is String or not cap.direction is String or not cap.action_id in ["idle","walk","run","hoe","water","harvest"] or not cap.direction in ["south","west","east","north"]:return reject("内部验收能力无效。")
   var id=cap.action_id+"-"+cap.direction
   if claimed.has(id):return reject("内部验收能力重复。")
   claimed[id]=true
  required_count=claimed.size()
 var binding=suite.manifest
 if not exact(binding,"manifest sha256") or not digest(binding.sha256):return reject("全动作manifest绑定无效。")
 var manifest_path=safe_file(project,binding.manifest,"art/characters/builds")
 if manifest_path=="" or manifest_path.get_file()!="manifest.json" or manifest_path.get_base_dir().get_base_dir()!=library.path_join("builds") or FileAccess.get_sha256(manifest_path)!=binding.sha256:return reject("全动作manifest路径或SHA失效。")
 var manifest=read_json(manifest_path)
 if not exact(manifest,"kind schema_version status release_eligible recipe artifact_digest inputs engine outputs") or manifest.kind!="coastal-character-review-build-v1" or not integer(manifest.schema_version,1) or manifest.schema_version!=1 or manifest.status!="review-only" or manifest.release_eligible!=false or not manifest.release_eligible is bool or not manifest.inputs is Dictionary or manifest.inputs.is_empty() or not engine_valid(project,manifest.engine):return reject("全动作构建状态或当前engine无效。")
 for file in manifest.inputs:
  var input_path=safe_file(library,file)
  if input_path=="" or not digest(manifest.inputs[file]) or FileAccess.get_sha256(input_path)!=manifest.inputs[file]:return reject("全动作真实输入SHA失效。")
 if not digest(manifest.artifact_digest) or bytes_hash(JSON.stringify({"inputs":manifest.inputs,"engine":manifest.engine},"",true).to_utf8_buffer())!=manifest.artifact_digest:return reject("全动作artifact digest失效。")
 var recipe_path=safe_file(library,manifest.recipe,"recipes");var recipe=read_json(recipe_path)
 if not exact(recipe,"kind schema_version resource_root character_model_id recipe_id revision base_recipe head_state slots clips authoring_inputs adaptations") or recipe.kind!="coastal-character-construction-v1" or recipe.schema_version!=2 or recipe.resource_root!="art/characters" or recipe.character_model_id!="unified-composable-character-v1" or recipe.head_state!="hair_hat" or not exact(recipe.slots,"hair hat") or not exact(recipe.adaptations,"hair hat"):return reject("全动作头部注册合同无效。")
 if not recipe.recipe_id is String or not recipe.revision is String or manifest.recipe!="recipes/"+recipe.recipe_id+"/"+recipe.revision+".json" or manifest.inputs.get(manifest.recipe)!=FileAccess.get_sha256(recipe_path) or not references_bound(library,recipe,manifest.inputs) or not recipe.clips is Array:return reject("全动作配方身份/引用失效。")
 if not ref_valid(library,recipe.base_recipe,manifest.inputs,"recipes"):return reject("全动作base引用失效。")
 var base_path=safe_file(library,recipe.base_recipe.file,"recipes");var base=read_json(base_path)
 if not exact(base,"kind schema_version resource_root character_model_id recipe_id revision template motion_set slots required_capabilities clips authoring_inputs adaptations") or base.kind!=recipe.kind or base.schema_version!=3 or base.resource_root!="art/characters" or base.character_model_id!=recipe.character_model_id or not base.clips is Array or base.clips.size()!=required_count or not base.required_capabilities is Array or base.required_capabilities.size()!=required_count or not references_bound(library,base,manifest.inputs):return reject("全动作必须使用完整schema3基础配方。")
 if not ref_valid(library,base.template,manifest.inputs,"templates") or not ref_valid(library,base.motion_set,manifest.inputs,"templates"):return reject("全动作母版/动作集引用失效。")
 var template=read_json(safe_file(library,base.template.file,"templates"))
 if not template is Dictionary or not template.get("template_id") is String or template.get("motion_set")!=base.motion_set.file:return reject("全动作母版身份不符。")
 var template_id:String=template.template_id
 if not fixed_identity_valid(library,base,recipe):return reject("全动作固定母版/衣装/发帽身份不符。")
 if not registered_inputs_bound(library,base,manifest.inputs) or not registered_inputs_bound(library,recipe,manifest.inputs):return reject("全动作实际映射的传递输入闭包缺失。")
 if not base.slots is Dictionary or base.slots.get("body","missing")!=null or not base.adaptations is Dictionary or not recipe.authoring_inputs is Array or not base.authoring_inputs is Array:return reject("全动作槽位/来源类型无效。")
 var slots:Dictionary={}
 for slot in base.slots:
  if slot=="body":continue
  if not ref_valid(library,base.slots[slot],manifest.inputs,"parts"):return reject("全动作衣装定义引用失效。")
  var design=read_json(safe_file(library,base.slots[slot].file,"parts"))
  if not design is Dictionary or design.get("category")!=slot or not design.get("design_id") is String:return reject("全动作衣装身份无效。")
  slots[slot]=design.design_id
 var required:Dictionary={}
 for cap in base.required_capabilities:
  if not exact(cap,"action_id direction") or not cap.action_id is String or not cap.direction is String:return reject("全动作能力声明无效。")
  var id=cap.action_id+"-"+cap.direction
  if required.has(id):return reject("全动作能力重复。")
  required[id]=true
 if candidate:
  for id in claimed:
   if not required.has(id):return reject("内部验收能力与实际配方不符。")
 if not manifest.outputs is Array or recipe.clips.size()!=required_count:return reject("全动作输出/头部clip缺失。")
 var pending:Dictionary={};var output_index=0
 for index in range(base.clips.size()):
  var clip=base.clips[index];var head=recipe.clips[index]
  if not exact(clip,"action_id direction canvas_px root_anchor_px display_scale action poses variant frames") or not geometry(clip) or not clip.action_id in ["idle","walk","run","hoe","water","harvest"] or not clip.direction in ["south","west","east","north"] or not clip.frames is Array or clip.frames.is_empty() or not template_clip_valid(library,clip,manifest.inputs,template_id):return reject("全动作clip与真实模板不符。")
  var id:String=clip.action_id+"-"+clip.direction
  if pending.has(id) or not required.has(id):return reject("全动作clip缺失或重复。")
  if not head is Dictionary or not exact(head,"action_id direction frames"+(" output_padding_px" if head.has("output_padding_px") else "")) or head.action_id!=clip.action_id or head.direction!=clip.direction or not head.frames is Array or head.frames.size()!=clip.frames.size():return reject("全动作发帽能力/顺序不符。")
  var output_clip=output_geometry(clip,head)
  if output_clip.is_empty() or not geometry(output_clip):return reject("全帧透明留边无效。")
  var textures:Array=[];var poses:Array=[];var durations:Array=[]
  for pose_index in range(clip.frames.size()):
   var frame=clip.frames[pose_index];var head_frame=head.frames[pose_index]
   if not exact(frame,"pose_id duration_ms layers layer_order registration composition") or not frame.pose_id is String or frame.pose_id in poses or not integer(frame.duration_ms,1) or frame.registration!=null:return reject("全动作姿态/时长/注册无效。")
   if not head_frame_shape_valid(head_frame,frame.pose_id):return reject("全动作发帽层序/兼容声明无效。")
   if head_frame.has("base_foreground"):
    if not foreground_binding_valid(library,head_frame.base_foreground,clip,frame.pose_id,manifest.inputs) or not foreground_targets_valid(library,head_frame.base_foreground,head_frame,recipe.adaptations,manifest.inputs):return reject("同母版手/工具前景绑定失效。")
   var seen:Array=[]
   for layer in head_frame.layers:
    if not exact(layer,"id slot pose_id texture source source_bundle ownership coverage occlusion interface_scope placement_mode offset_px local_scale view_binding"):return reject("全动作头部字段不完整。")
    if not layer.id is String or not layer.id in head_frame.layer_order or layer.id=="base" or layer.id in seen or layer.pose_id!=frame.pose_id or layer.slot!=("hair" if layer.id=="under_hat_hair" else "hat"):return reject("全动作头部身份无效："+str(frame.pose_id)+"/"+str(layer.id))
    if layer.placement_mode!="full_frame" or not uniform_pair(layer.offset_px,0.0) or not uniform_pair(layer.local_scale,1.0) or layer.coverage!=null or layer.occlusion!=null:return reject("全动作头部注册无效："+str(frame.pose_id)+"/"+str(layer.id))
    if not ref_valid(library,layer.texture,manifest.inputs,"parts"):return reject("全动作头部纹理绑定无效："+str(layer.texture))
    seen.append(layer.id)
   if output_index>=manifest.outputs.size():return reject("全动作PNG输出缺失。")
   var texture=output_texture(manifest_path.get_base_dir(),manifest.outputs[output_index],output_clip,frame)
   if texture==null:return reject("全动作PNG/尺寸/RGBA失效。")
   output_index+=1;textures.append(texture);poses.append(frame.pose_id);durations.append(frame.duration_ms)
  var action=read_json(safe_file(library,clip.action.file,"templates"))
  pending[id]={"action_id":clip.action_id,"direction":clip.direction,"textures":textures,"pose_ids":poses,"durations_ms":durations,"canvas_px":Vector2(output_clip.canvas_px[0],output_clip.canvas_px[1]),"root_anchor_px":Vector2(output_clip.root_anchor_px[0],output_clip.root_anchor_px[1]),"display_scale":float(output_clip.display_scale),"loop":action.get("loop",false)}
 var directions:Array=[]
 for clip in pending.values():
  if not clip.direction in directions:directions.append(clip.direction)
 if output_index!=manifest.outputs.size() or not suite.canonical_idle is Dictionary or suite.canonical_idle.size()!=directions.size() or not suite.samples is Array or suite.samples.size()!=required_count-directions.size():return reject("注册动作范围或canonical idle缺失。")
 var idle_map:Dictionary={}
 for direction in directions:
  if not suite.canonical_idle.has(direction):return reject("注册动作canonical idle方向缺失。")
  var idle:Dictionary=pending.get("idle-"+direction,{})
  if idle.is_empty() or suite.canonical_idle[direction]!=idle.pose_ids:return reject("全动作canonical idle错配。")
  idle_map[direction]=idle
 var pending_samples:Array=[];var sample_ids:Array=[]
 var bound={"manifest":binding.manifest,"sha256":binding.sha256,"recipe":manifest.recipe,"recipe_sha256":manifest.inputs[manifest.recipe],"artifact_digest":manifest.artifact_digest}
 for entry in suite.samples:
  if not exact(entry,"id action_id direction") or not entry.id is String or not entry.action_id is String or not entry.direction is String or entry.id!=entry.action_id+"-"+entry.direction or entry.action_id=="idle" or not pending.has(entry.id) or entry.id in sample_ids:return reject("全动作评审条目缺失/重复。")
  var clip:Dictionary=pending[entry.id];var idle:Dictionary=idle_map[entry.direction]
  var data={"template_id":template_id,"action_id":entry.action_id,"direction":entry.direction,"recipe":{"slots":slots},"idle":{"pose_id":idle.pose_ids[0],"canvas_px":[idle.canvas_px.x,idle.canvas_px.y],"root_anchor_px":[idle.root_anchor_px.x,idle.root_anchor_px.y],"display_scale":idle.display_scale},"canvas_px":[clip.canvas_px.x,clip.canvas_px.y],"root_anchor_px":[clip.root_anchor_px.x,clip.root_anchor_px.y],"display_scale":clip.display_scale}
  pending_samples.append({"id":entry.id,"data":data,"sample_sha256":FileAccess.get_sha256(suite_path),"sample_path":suite_path,"textures_by_state":{"hair_hat":clip.textures},"idle_by_state":{"hair_hat":idle.textures[0]},"pose_ids":clip.pose_ids,"durations_ms":clip.durations_ms,"canvas_px":clip.canvas_px,"root_anchor_px":clip.root_anchor_px,"display_scale":clip.display_scale,"manifest_bindings":{"hair_hat":bound}})
  sample_ids.append(entry.id)
 if not runtime_valid(suite.runtime,pending):return reject("全动作运行时序/事件合同无效。")
 runtime=suite.runtime
 samples=pending_samples;full_clips=pending;canonical_idle=idle_map;full_package=not candidate;candidate_package=candidate
 catalog_sha256=FileAccess.get_sha256(suite_path);suite_kind=expected_kind;manifest_bindings={"hair_hat":bound};error="";return true

func runtime_valid(data:Variant,pending:Dictionary) -> bool:
 if not exact(data,"schema_version movement default_speed_factor locomotion_transition clips") or not integer(data.schema_version,1) or data.schema_version!=1 or not exact(data.movement,"walk run"):return false
 for action in ["walk","run"]:
  if not exact(data.movement[action],"base_world_speed") or not number(data.movement[action].base_world_speed) or data.movement[action].base_world_speed<=0:return false
 if not number(data.default_speed_factor) or data.default_speed_factor<0.5 or data.default_speed_factor>1:return false
 var transition=data.locomotion_transition
 if not exact(transition,"kind duration_ms") or transition.kind!="stable-idle-v1" or not integer(transition.duration_ms,1) or transition.duration_ms>1000:return false
 if not data.clips is Dictionary or data.clips.size()!=pending.size():return false
 for id in pending:
  var clip:Dictionary=pending[id];var row=data.clips.get(id)
  if not exact(row,"playback_rate events") or not number(row.playback_rate) or row.playback_rate<=0 or not row.events is Array:return false
  if clip.action_id in ["walk","run"] and row.playback_rate!=1:return false
  if clip.action_id not in ["hoe","water","harvest"] and not row.events.is_empty():return false
  var seen:Array=[];var previous_time:=-1.0
  for event in row.events:
   if not exact(event,"event_id at_ms pose_id") or not event.event_id is String or event.event_id=="" or event.event_id=="complete" or event.event_id in seen or not integer(event.at_ms,0):return false
   seen.append(event.event_id)
   if float(event.at_ms)<previous_time:return false
   previous_time=float(event.at_ms)
   var elapsed:=0.0;var matched:=false
   for i in range(clip.pose_ids.size()):
    if clip.pose_ids[i]==event.pose_id:matched=event.at_ms>=elapsed and event.at_ms<elapsed+float(clip.durations_ms[i])
    elapsed+=float(clip.durations_ms[i])
   if not matched:return false
 return true
