extends "res://dev/characters/character_construction_samples.gd"
## Body-only adapter for the existing registered review clock and observer.
## Python preflight reconstructs source packs; native loading independently binds
## the input closure, canonical poses, registered atlas pixels and build outputs.
const BODY_KIND="coastal-body-character-review-v1"
const ACTIONS=["idle","walk","run","hoe","water","harvest"]
const DIRECTIONS=["north","west","south","east"]
func rgba_image(path:String,size:Variant=null,rgba_sha:String="") -> Image:
 if path=="":return null
 var raw=FileAccess.get_file_as_bytes(path)
 if raw.size()<24 or raw.slice(0,8)!=PackedByteArray([137,80,78,71,13,10,26,10]):return null
 var image=Image.new()
 if image.load_png_from_buffer(raw)!=OK or image.get_format()!=Image.FORMAT_RGBA8:return null
 if size!=null:
  if not size is Array or size.size()!=2 or not integer(size[0],1) or not integer(size[1],1) or image.get_size()!=Vector2i(int(size[0]),int(size[1])):return null
 if rgba_sha!="" and (not digest(rgba_sha) or bytes_hash(image.get_data())!=rgba_sha):return null
 return image
func pack_index(project:String,library:String,refs:Variant,inputs:Dictionary) -> Dictionary:
 if not refs is Array or refs.is_empty() or refs.size()>32:return {}
 var seen:Dictionary={};var index:Dictionary={}
 for ref in refs:
  if not ref_valid(library,ref,inputs) or not ref.file.begins_with("sources/") and not ref.file.begins_with("parts/") or ref.file.get_file()!="manifest.json" or seen.has(ref.file):return {}
  seen[ref.file]=true
  var path=safe_file(library,ref.file);var pack=read_json(path)
  if not exact(pack,"kind schema_version status release_eligible complete_body_archive plan inputs engine artifact_digest outputs") or pack.kind!="coastal-character-source-atlas-v1" or not integer(pack.schema_version,1) or pack.schema_version!=1 or pack.status!="review-only" or not pack.release_eligible is bool or pack.release_eligible or not pack.complete_body_archive is bool or pack.complete_body_archive or not pack.inputs is Dictionary or pack.inputs.is_empty() or not pack.outputs is Array or pack.outputs.size()<2:return {}
  if not exact(pack.engine,"pillow code") or not pack.engine.pillow is String or pack.engine.pillow.is_empty() or not exact(pack.engine.code,"pack_sources.py build_contract.py"):return {}
  for file in pack.engine.code:
   var code_path=safe_file(project.path_join("tools/characters"),file)
   if code_path=="" or not digest(pack.engine.code[file]) or FileAccess.get_sha256(code_path)!=pack.engine.code[file]:return {}
  if not digest(pack.artifact_digest) or bytes_hash(JSON.stringify({"inputs":pack.inputs,"engine":pack.engine},"",true).to_utf8_buffer())!=pack.artifact_digest:return {}
  for file in pack.inputs:
   if not ref_valid(library,{"file":file,"sha256":pack.inputs[file]},inputs):return {}
  if not pack.plan is String or not pack.inputs.has(pack.plan):return {}
  var atlases:Dictionary={};var layout:Variant=null
  for output in pack.outputs:
   if not output is Dictionary or not output.get("file") is String:return {}
   var relative=ref.file.get_base_dir().path_join(output.file)
   if not ref_valid(library,{"file":relative,"sha256":output.get("sha256")},inputs):return {}
   if output.file=="layout.json":
    if not exact(output,"file sha256") or layout!=null:return {}
    layout=read_json(safe_file(path.get_base_dir(),output.file))
   else:
    if not exact(output,"file sha256 size_px rgba_sha256") or not output.file.begins_with("atlases/") or atlases.has(output.file):return {}
    var image=rgba_image(safe_file(path.get_base_dir(),output.file,"atlases"),output.size_px,output.rgba_sha256)
    if image==null:return {}
    atlases[output.file]={"image":image,"sha256":output.sha256}
  if not exact(layout,"kind schema_version status cell_px root_px rows display_scale clips") or layout.kind!="coastal-character-source-layout-v1" or not integer(layout.schema_version,1) or layout.schema_version!=1 or layout.status!="review-only" or layout.rows!=DIRECTIONS or not layout.clips is Array:return {}
  for clip in layout.clips:
   if not clip is Dictionary or not clip.get("action") is String or not clip.get("direction") is String or not clip.get("frames") is Array:return {}
   if clip.get("representation")!="body" and not (clip.action in ["hoe","water","harvest"] and clip.get("representation")==clip.action+"-visible"):return {}
   for frame in clip.frames:
    if not frame is Dictionary or not frame.get("pose_id") is String or not atlases.has(frame.get("atlas")) or not integer(frame.get("duration_ms"),1) or not frame.get("region_px") is Array or frame.region_px.size()!=4:return {}
    var region=frame.region_px
    for value in region:
     if not integer(value):return {}
    var atlas:Dictionary=atlases[frame.atlas]
    if region[2]<=0 or region[3]<=0 or region[0]+region[2]>atlas.image.get_width() or region[1]+region[3]>atlas.image.get_height():return {}
    var key=clip.action+"/"+clip.direction+"/"+frame.pose_id
    if not index.has(key):index[key]=[]
    index[key].append({"pack":ref.file,"atlas_sha256":atlas.sha256,"image":atlas.image,"region":Rect2i(region[0],region[1],region[2],region[3]),"duration_ms":frame.duration_ms,"canvas_px":layout.cell_px,"root_anchor_px":layout.root_px,"display_scale":layout.display_scale})
 return {"frames":index,"packs":seen}
func load_samples(project:String,path:String) -> bool:
 reject("")
 if ".." in project.split("/") or "." in project.split("/") or "\\" in project or ":" in project:return reject("身体评审项目路径不允许跳转。")
 project=project.simplify_path()
 if not no_links(project) or not path.begins_with(project+"/"):return reject("身体评审路径无效。")
 var library=project.path_join("art/characters")
 var suite_path=safe_file(project,path.trim_prefix(project+"/"),"art/characters/reviews")
 var suite=read_json(suite_path)
 if not exact(suite,"kind schema_version resource_root scope manifest packed_sources runtime") or suite.kind!=BODY_KIND or not integer(suite.schema_version,1) or suite.schema_version!=1 or suite.resource_root!="art/characters" or suite.scope!="review-only":return reject("身体评审范围或版本无效。")
 if not exact(suite.manifest,"file sha256") or not digest(suite.manifest.sha256):return reject("身体manifest绑定无效。")
 var manifest_path=safe_file(library,suite.manifest.file,"builds")
 if manifest_path=="" or manifest_path.get_file()!="manifest.json" or manifest_path.get_base_dir().get_base_dir()!=library.path_join("builds") or FileAccess.get_sha256(manifest_path)!=suite.manifest.sha256:return reject("身体manifest路径或SHA失效。")
 var manifest=read_json(manifest_path)
 if not exact(manifest,"kind schema_version status release_eligible recipe artifact_digest inputs engine outputs") or manifest.kind!="coastal-character-review-build-v1" or not integer(manifest.schema_version,1) or manifest.schema_version!=1 or manifest.status!="review-only" or not manifest.release_eligible is bool or manifest.release_eligible or not manifest.inputs is Dictionary or manifest.inputs.is_empty() or not manifest.outputs is Array or not engine_valid(project,manifest.engine):return reject("身体严格构建状态或engine失效。")
 for file in manifest.inputs:
  if not ref_valid(library,{"file":file,"sha256":manifest.inputs[file]},manifest.inputs):return reject("身体实际输入SHA失效。")
 if not digest(manifest.artifact_digest) or bytes_hash(JSON.stringify({"inputs":manifest.inputs,"engine":manifest.engine},"",true).to_utf8_buffer())!=manifest.artifact_digest:return reject("身体artifact digest失效。")
 var recipe_path=safe_file(library,manifest.recipe,"recipes");var recipe=read_json(recipe_path)
 if not exact(recipe,"kind schema_version resource_root character_model_id recipe_id revision template motion_set slots required_capabilities clips authoring_inputs adaptations") or recipe.kind!="coastal-character-construction-v1" or not integer(recipe.schema_version,1) or recipe.schema_version!=3 or recipe.resource_root!="art/characters" or recipe.character_model_id!="unified-composable-character-v1" or not exact(recipe.slots,"body") or recipe.slots.body!=null or not exact(recipe.adaptations,"") or not recipe.authoring_inputs is Array:return reject("身体评审必须为schema3单body配方。")
 if not recipe.recipe_id is String or not recipe.revision is String or manifest.recipe!="recipes/"+recipe.recipe_id+"/"+recipe.revision+".json" or manifest.inputs.get(manifest.recipe)!=FileAccess.get_sha256(recipe_path) or not references_bound(library,recipe,manifest.inputs):return reject("身体配方身份或引用失效。")
 if not ref_valid(library,recipe.template,manifest.inputs,"templates") or not ref_valid(library,recipe.motion_set,manifest.inputs,"templates"):return reject("身体母版或动作集引用失效。")
 var template=read_json(safe_file(library,recipe.template.file,"templates"))
 var motion=read_json(safe_file(library,recipe.motion_set.file,"templates"))
 if not template is Dictionary or not template.get("template_id") is String or template.get("motion_set")!=recipe.motion_set.file or not motion is Dictionary or motion.get("template_id")!=template.template_id or not motion.get("actions") is Dictionary:return reject("身体母版或动作集身份不符。")
 if not recipe.required_capabilities is Array or recipe.required_capabilities.size()!=24 or not recipe.clips is Array or recipe.clips.size()!=24:return reject("身体评审需要完整24能力。")
 var required:Dictionary={}
 for cap in recipe.required_capabilities:
  if not exact(cap,"action_id direction") or not cap.action_id in ACTIONS or not cap.direction in DIRECTIONS:return reject("身体能力声明无效。")
  var id=cap.action_id+"-"+cap.direction
  if required.has(id):return reject("身体能力重复。")
  required[id]=true
 var packed=pack_index(project,library,suite.packed_sources,manifest.inputs)
 if packed.is_empty():return reject("身体packed source闭包或RGBA失效。")
 var pending:Dictionary={};var used_packs:Dictionary={};var output_index=0
 for clip in recipe.clips:
  if not exact(clip,"action_id direction canvas_px root_anchor_px display_scale action poses variant frames") or not geometry(clip) or not clip.action_id in ACTIONS or not clip.direction in DIRECTIONS or not clip.frames is Array or clip.frames.is_empty() or not template_clip_valid(library,clip,manifest.inputs,template.template_id):return reject("身体clip与真实模板时序/几何不符。")
  if motion.actions.get(clip.action_id)!=clip.action.file:return reject("身体action未注册于实际动作集。")
  var id:String=clip.action_id+"-"+clip.direction
  if pending.has(id) or not required.has(id):return reject("身体clip重复或未声明。")
  var pose_document=read_json(safe_file(library,clip.poses.file,"templates"))
  var originals:Array=pose_document.variants[clip.variant].frames
  var textures:Array=[];var poses:Array=[];var durations:Array=[]
  for i in range(clip.frames.size()):
   var frame=clip.frames[i]
   if not exact(frame,"pose_id duration_ms layers layer_order registration composition") or not frame.pose_id is String or frame.pose_id in poses or not integer(frame.duration_ms,1) or frame.registration!=null or frame.layer_order!=["body"] or not frame.layers is Array or frame.layers.size()!=1 or not frame.composition in ["ownership-replace","alpha-over"]:return reject("身体姿态/层序合同无效。")
   var layer=frame.layers[0]
   if not exact(layer,"id slot pose_id texture source source_bundle ownership coverage occlusion interface_scope placement_mode offset_px local_scale") or layer.id!="body" or layer.slot!="body" or layer.pose_id!=frame.pose_id or layer.ownership!=null or layer.coverage!=null or layer.occlusion!=null or layer.interface_scope!="same-pose-reference" or layer.placement_mode!="full_frame" or not uniform_pair(layer.offset_px,0.0) or not uniform_pair(layer.local_scale,1.0):return reject("身体只支持完整同姿态body层及空mask。")
   var original:Dictionary=originals[i]
   if not exact(layer.texture,"file sha256") or layer.texture.file!=original.get("file") or layer.texture.sha256!=original.get("sha256") or not ref_valid(library,layer.texture,manifest.inputs,"templates") or not ref_valid(library,layer.source,manifest.inputs,"sources") or not ref_valid(library,layer.source_bundle,manifest.inputs,"sources"):return reject("身体纹理未绑定实际canonical pose。")
   var image=rgba_image(safe_file(library,layer.texture.file),clip.canvas_px)
   if image==null:return reject("身体canonical RGBA失效。")
   var matches:Array=[]
   for item in packed.frames.get(clip.action_id+"/"+clip.direction+"/"+frame.pose_id,[]):
    if item.atlas_sha256==layer.source.sha256 and item.duration_ms==frame.duration_ms and item.canvas_px==clip.canvas_px and item.root_anchor_px==clip.root_anchor_px and item.display_scale==clip.display_scale and item.image.get_region(item.region).get_data()==image.get_data():matches.append(item)
   if matches.size()!=1:return reject("身体实际来源图集/姿态/几何不唯一匹配。")
   used_packs[matches[0].pack]=true
   if output_index>=manifest.outputs.size():return reject("身体PNG输出缺失。")
   var texture=output_texture(manifest_path.get_base_dir(),manifest.outputs[output_index],clip,frame)
   if texture==null or texture.get_image().get_data()!=image.get_data():return reject("身体输出PNG/RGBA与canonical不符。")
   output_index+=1;textures.append(texture);poses.append(frame.pose_id);durations.append(frame.duration_ms)
  var action=read_json(safe_file(library,clip.action.file,"templates"))
  pending[id]={"action_id":clip.action_id,"direction":clip.direction,"textures":textures,"pose_ids":poses,"durations_ms":durations,"canvas_px":Vector2(clip.canvas_px[0],clip.canvas_px[1]),"root_anchor_px":Vector2(clip.root_anchor_px[0],clip.root_anchor_px[1]),"display_scale":float(clip.display_scale),"loop":action.get("loop",false)}
 if output_index!=manifest.outputs.size() or used_packs.size()!=packed.packs.size() or not runtime_valid(suite.runtime,pending):return reject("身体输出/来源范围或runtime合同无效。")
 var bound={"manifest":"art/characters/"+suite.manifest.file,"sha256":suite.manifest.sha256,"recipe":manifest.recipe,"recipe_sha256":manifest.inputs[manifest.recipe],"artifact_digest":manifest.artifact_digest}
 var idle_map:Dictionary={};var pending_samples:Array=[]
 for direction in DIRECTIONS:idle_map[direction]=pending["idle-"+direction]
 var suite_sha=FileAccess.get_sha256(suite_path)
 for id in pending:
  var clip:Dictionary=pending[id]
  if clip.action_id=="idle":continue
  var idle:Dictionary=idle_map[clip.direction]
  var data={"template_id":template.template_id,"action_id":clip.action_id,"direction":clip.direction,"recipe":{"slots":{}},"idle":{"pose_id":idle.pose_ids[0],"canvas_px":[idle.canvas_px.x,idle.canvas_px.y],"root_anchor_px":[idle.root_anchor_px.x,idle.root_anchor_px.y],"display_scale":idle.display_scale},"canvas_px":[clip.canvas_px.x,clip.canvas_px.y],"root_anchor_px":[clip.root_anchor_px.x,clip.root_anchor_px.y],"display_scale":clip.display_scale}
  pending_samples.append({"id":id,"data":data,"sample_sha256":suite_sha,"sample_path":suite_path,"textures_by_state":{"body":clip.textures},"idle_by_state":{"body":idle.textures[0]},"pose_ids":clip.pose_ids,"durations_ms":clip.durations_ms,"canvas_px":clip.canvas_px,"root_anchor_px":clip.root_anchor_px,"display_scale":clip.display_scale,"manifest_bindings":{"body":bound}})
 samples=pending_samples;full_clips=pending;canonical_idle=idle_map;runtime=suite.runtime
 full_package=true;candidate_package=false;suite_kind=BODY_KIND;catalog_sha256=suite_sha;manifest_bindings={"body":bound};error="";return true
