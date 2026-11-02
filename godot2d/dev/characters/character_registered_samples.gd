extends RefCounted
## Bound runtime artifacts only. Python preflight reconstructs raw source pixels.
const Paths = preload("res://dev/characters/character_resource_paths.gd")
const Construction = preload("res://dev/characters/character_construction_samples.gd")
const KIND = "coastal-registered-character-review-v1"
var helper = Construction.new()
var error := ""
var frames: Dictionary = {}
var frame_metadata: Array = []
var clips: Dictionary = {}
var geometry: Dictionary = {}
var runtime: Dictionary = {}
var artifact_digest := ""
var prepared_frames: Dictionary = {}

func reject(message: String) -> bool:
	frames.clear(); frame_metadata.clear(); clips.clear(); geometry.clear(); runtime.clear()
	prepared_frames.clear(); artifact_digest = ""; error = message
	return false

func runtime_valid(value: Variant) -> bool:
	if not helper.exact(value, "world_scale walk_world_speed speed_factor"): return false
	for name in value:
		if not helper.number(value[name]): return false
	return value.world_scale > 0 and value.world_scale <= 1 and value.walk_world_speed > 0 and value.walk_world_speed <= 1000 and value.speed_factor >= .5 and value.speed_factor <= 1

func png(path: String, size: Variant, mode: String = "RGBA") -> Image:
	if path == "" or not size is Array or size.size() != 2: return null
	for value in size:
		if not helper.integer(value, 1) or value > 8192: return null
	var bytes = FileAccess.get_file_as_bytes(path)
	if bytes.size() < 24 or bytes.slice(0, 8) != PackedByteArray([137,80,78,71,13,10,26,10]): return null
	var result = Image.new()
	if result.load_png_from_buffer(bytes) != OK or result.get_size() != Vector2i(int(size[0]), int(size[1])): return null
	if result.get_format() != (Image.FORMAT_RGBA8 if mode == "RGBA" else Image.FORMAT_L8): return null
	return result

func checked_png(library: String, ref: Variant, inputs: Dictionary, size: Array) -> Image:
	if not helper.ref_valid(library, ref, inputs): return null
	return png(helper.safe_file(library, ref.file), size)

func preparation_engine_valid(project: String, identity: Variant) -> bool:
	if not helper.exact(identity, "pillow code") or not identity.pillow is String or identity.pillow.is_empty(): return false
	if not helper.exact(identity.code, "tools/characters/prepare_registered_source.py"): return false
	for name in identity.code:
		var path = helper.safe_file(project, name, "tools/characters")
		if path == "" or not helper.digest(identity.code[name]) or FileAccess.get_sha256(path) != identity.code[name]: return false
	return true

func load_preparations(project: String, library: String, refs: Variant, inputs: Dictionary) -> Dictionary:
	if not refs is Array or refs.is_empty() or refs.size() > 32: return {}
	var result: Dictionary = {}; var seen: Dictionary = {}
	for ref in refs:
		if not helper.ref_valid(library, ref, inputs, "sources") or ref.file in seen: return {}
		var relative: PackedStringArray = ref.file.split("/")
		if relative.size() != 3 or relative[2] != "manifest.json": return {}
		seen[ref.file] = true
		var path = helper.safe_file(library, ref.file, "sources")
		var manifest = helper.read_json(path)
		if not helper.exact(manifest, "kind schema_version status release_eligible plan inputs engine artifact_digest frames outputs"): return {}
		if manifest.kind != "coastal-registered-source-preparation-v1" or not helper.integer(manifest.schema_version, 1) or manifest.schema_version != 1 or manifest.status != "review-only" or not manifest.release_eligible is bool or manifest.release_eligible or not manifest.inputs is Dictionary or not preparation_engine_valid(project, manifest.engine): return {}
		if not helper.ref_valid(library, manifest.plan, inputs, "sources") or not helper.digest(manifest.artifact_digest): return {}
		for name in manifest.inputs:
			if not helper.ref_valid(library, {"file": name, "sha256": manifest.inputs[name]}, inputs): return {}
		if not manifest.frames is Array or manifest.frames.is_empty() or manifest.frames.size() > 256 or not manifest.outputs is Array or manifest.outputs.size() != manifest.frames.size() * 3 + 1: return {}
		# Python recomputes this typed source artifact. Godot binds its exact file
		# SHA through strict inputs; JSON parsing loses integer/float distinctions.
		var output_refs: Dictionary = {}; var output_images: Dictionary = {}; var bundle: Dictionary = {}
		var prefix: String = ref.file.get_base_dir() + "/"
		for entry in manifest.outputs:
			if not entry is Dictionary or not entry.get("file") is String or output_refs.has(entry.file): return {}
			if entry.file == "source.json":
				if not helper.exact(entry, "file sha256"): return {}
				bundle = {"file": prefix + entry.file, "sha256": entry.sha256}
				if not helper.ref_valid(library, bundle, inputs): return {}
				var source = helper.read_json(helper.safe_file(library, bundle.file))
				if not source is Dictionary or source.get("source_id") != relative[1] or source.get("status") != "prepared-derived-review-only" or source.get("accepted") != false or not source.get("accepted") is bool or source.get("runtime_eligible") != false or not source.get("runtime_eligible") is bool or source.get("complete_hidden_source") != false or not source.get("complete_hidden_source") is bool: return {}
			else:
				if not helper.exact(entry, "file sha256 size_px mode rgba_sha256") or not helper.digest(entry.sha256) or not helper.digest(entry.rgba_sha256): return {}
				var components: PackedStringArray = entry.file.split("/")
				if components.size() != 2 or not components[0] in ["materials", "ownership", "textures"] or not components[1].ends_with(".png"): return {}
				var expected_mode = "L" if components[0] == "ownership" else "RGBA"
				if entry.mode != expected_mode: return {}
				var file_path = helper.safe_file(path.get_base_dir(), entry.file)
				if file_path == "" or FileAccess.get_sha256(file_path) != entry.sha256: return {}
				var picture = png(file_path, entry.size_px, expected_mode)
				if picture == null: return {}
				if expected_mode == "L":
					for value in picture.get_data():
						if value != 0 and value != 255: return {}
				var rgba = picture.duplicate(); rgba.convert(Image.FORMAT_RGBA8)
				if helper.bytes_hash(rgba.get_data()) != entry.rgba_sha256: return {}
				output_images[entry.file] = picture
			output_refs[entry.file] = {"file": prefix + entry.file, "sha256": entry.sha256}
		if bundle.is_empty(): return {}
		for row in manifest.frames:
			if not helper.exact(row, "pose_id action direction frame_index duration_ms source ownership box_px canonical_poses variant canonical_frame body_source body_source_root_px body_scale density_ratio material_root_px effective_scale inverse_scale canvas_px root_anchor_px display_scale resampling material_fill_rgba ownership_fill"): return {}
			if not row.pose_id is String or not helper.geometry(row) or not row.action in ["idle", "walk"] or not row.direction in ["south", "west", "east", "north"]: return {}
			var material_name = "materials/" + row.pose_id + ".png"
			if not output_refs.has(material_name) or result.has(output_refs[material_name].file): return {}
			var selected: Dictionary = {}; var images: Dictionary = {}
			for folder in ["materials", "ownership", "textures"]:
				var name = folder + "/" + row.pose_id + ".png"
				if not output_refs.has(name) or not output_images.has(name): return {}
				selected[folder] = output_refs[name]; images[folder] = output_images[name]
				if output_images[name].get_size() != Vector2i(int(row.canvas_px[0]), int(row.canvas_px[1])): return {}
			result[selected.materials.file] = {"manifest": ref.file, "frame": row, "refs": selected, "images": images, "bundle": bundle}
	return result

func annotation_valid(library: String, selector: Variant, clip: Dictionary, frame: Dictionary, canonical: Dictionary, inputs: Dictionary) -> bool:
	if not helper.exact(selector, "document record") or not selector.record is String or not helper.ref_valid(library, selector.document, inputs): return false
	var data = helper.read_json(helper.safe_file(library, selector.document.file))
	if not data is Dictionary or data.get("kind") != "coastal-pose-annotations-v1" or not data.get("records") is Array: return false
	var matches: Array = []
	for record in data.records:
		if record is Dictionary and record.get("record_id") == selector.record: matches.append(record)
	if matches.size() != 1: return false
	var record = matches[0]
	if not helper.exact(record, "record_id poses variant pose_id reference_frame canvas_px root_anchor_px display_scale landmarks_px surfaces"): return false
	if record.poses != clip.poses or record.variant != clip.variant or record.pose_id != frame.pose_id or record.reference_frame != canonical: return false
	for field in ["canvas_px", "root_anchor_px", "display_scale"]:
		if record[field] != clip[field]: return false
	return true

func top_valid(library: String, layer: Dictionary, clip: Dictionary, frame: Dictionary, canonical: Dictionary, catalog: Dictionary, inputs: Dictionary, prepared: Dictionary) -> String:
	if not helper.exact(layer, "id slot pose_id texture source source_bundle ownership coverage occlusion interface_scope placement_mode offset_px local_scale view_binding"): return ""
	if layer.slot != "top" or layer.pose_id != frame.pose_id or layer.interface_scope != "registered-component" or layer.placement_mode != "full_frame" or not helper.uniform_pair(layer.offset_px, 0) or not helper.uniform_pair(layer.local_scale, 1) or layer.coverage != null or layer.occlusion != null: return ""
	if not helper.exact(layer.view_binding, "view_id mapping_id"): return ""
	var binding = layer.view_binding
	if not binding.view_id is String or not binding.mapping_id is String or not catalog.views.has(binding.view_id) or not catalog.mappings.has(binding.mapping_id): return ""
	var view = catalog.views[binding.view_id]; var mapping = catalog.mappings[binding.mapping_id]
	if not helper.exact(view, "view_id role source_pose source source_bundle canvas_px root_anchor_px source_ownership extraction") or not helper.exact(mapping, "mapping_id view_id texture target_pose target_surface interface_scope role anchors coverage occlusion"): return ""
	if view.role != "full-source-component" or not helper.exact(view.source_ownership, "role mask") or view.source_ownership.role != "source-ownership" or not helper.exact(view.extraction, "kind density_normalization") or view.extraction.kind != "binary-rgba-extract-v1" or view.extraction.density_normalization != null: return ""
	if mapping.view_id != binding.view_id or mapping.role != "component-surface" or mapping.interface_scope != "same-cut-surface" or mapping.coverage != null or mapping.occlusion != null: return ""
	if layer.source != view.source or layer.source_bundle != view.source_bundle or layer.ownership != view.source_ownership.mask or layer.texture != mapping.texture or not helper.exact(layer.source, "file sha256") or not prepared.has(layer.source.file): return ""
	var source = prepared[layer.source.file]; var row = source.frame
	if layer.source != source.refs.materials or layer.source_bundle != source.bundle or layer.ownership != source.refs.ownership or view.canvas_px != clip.canvas_px or view.root_anchor_px != clip.root_anchor_px: return ""
	if row.pose_id != frame.pose_id or row.action != clip.action_id or row.direction != clip.direction or row.canonical_poses != clip.poses or row.variant != clip.variant or row.canonical_frame != canonical: return ""
	for field in ["canvas_px", "root_anchor_px", "display_scale"]:
		if row[field] != clip[field]: return ""
	for ref in source.refs.values():
		if not helper.ref_valid(library, ref, inputs): return ""
	if not annotation_valid(library, view.source_pose, clip, frame, canonical, inputs) or not annotation_valid(library, mapping.target_pose, clip, frame, canonical, inputs): return ""
	if not helper.exact(mapping.anchors, "name source_px target_px") or mapping.anchors.source_px != clip.root_anchor_px or mapping.anchors.target_px != clip.root_anchor_px: return ""
	var texture = checked_png(library, mapping.texture, inputs, clip.canvas_px)
	if texture == null or texture.get_data() != source.images.textures.get_data(): return ""
	return source.manifest

func load_samples(project: String, suite_path: String) -> bool:
	reject("")
	if not project.is_absolute_path() or ".." in project.split("/") or "." in project.split("/") or "\\" in project or not helper.no_links(project): return reject("审阅项目路径无效。")
	var library = project.path_join(Paths.LIBRARY_ROOT)
	if not suite_path.begins_with(library + "/reviews/") or not Paths.relative_file(suite_path.trim_prefix(library + "/")) or not helper.no_links(suite_path): return reject("审阅清单路径无效。")
	var suite = helper.read_json(suite_path)
	if not helper.exact(suite, "kind schema_version resource_root scope manifest prepared_sources runtime") or suite.kind != KIND or not helper.integer(suite.schema_version, 1) or suite.schema_version != 1 or suite.resource_root != Paths.LIBRARY_ROOT or suite.scope != "review-only" or not runtime_valid(suite.runtime): return reject("审阅范围或运行参数无效。")
	if not helper.exact(suite.manifest, "file sha256") or not helper.digest(suite.manifest.sha256): return reject("构建manifest引用无效。")
	var manifest_path = helper.safe_file(library, suite.manifest.file, "builds")
	if manifest_path == "" or manifest_path.get_file() != "manifest.json" or manifest_path.get_base_dir().get_base_dir() != library.path_join("builds") or FileAccess.get_sha256(manifest_path) != suite.manifest.sha256: return reject("构建manifest路径或SHA失效。")
	var manifest = helper.read_json(manifest_path)
	if not helper.exact(manifest, "kind schema_version status release_eligible recipe artifact_digest inputs engine outputs") or manifest.kind != "coastal-character-review-build-v1" or not helper.integer(manifest.schema_version, 1) or manifest.schema_version != 1 or manifest.status != "review-only" or not manifest.release_eligible is bool or manifest.release_eligible or not manifest.inputs is Dictionary or manifest.inputs.is_empty() or not helper.engine_valid(project, manifest.engine): return reject("严格构建范围或当前工具SHA失效。")
	for name in manifest.inputs:
		if not helper.ref_valid(library, {"file": name, "sha256": manifest.inputs[name]}, manifest.inputs): return reject("严格构建实际输入SHA失效。")
	if not helper.digest(manifest.artifact_digest) or helper.bytes_hash(JSON.stringify({"inputs": manifest.inputs, "engine": manifest.engine}, "", true).to_utf8_buffer()) != manifest.artifact_digest: return reject("严格构建artifact失效。")
	var recipe_path = helper.safe_file(library, manifest.recipe, "recipes")
	var recipe = helper.read_json(recipe_path)
	if not helper.exact(recipe, "kind schema_version resource_root character_model_id recipe_id revision template motion_set slots required_capabilities clips authoring_inputs adaptations") or recipe.kind != "coastal-character-construction-v1" or not helper.integer(recipe.schema_version, 3) or recipe.schema_version != 3 or recipe.resource_root != Paths.LIBRARY_ROOT or recipe.character_model_id != "unified-composable-character-v1" or not recipe.recipe_id is String or not recipe.revision is String or manifest.recipe != "recipes/" + recipe.recipe_id + "/" + recipe.revision + ".json" or manifest.inputs.get(manifest.recipe) != FileAccess.get_sha256(recipe_path): return reject("注册配方身份或schema失效。")
	if not recipe.clips is Array or not recipe.authoring_inputs is Array: return reject("配方动作/来源类型无效。")
	if not helper.exact(recipe.slots, "body top") or recipe.slots.body != null or not helper.exact(recipe.adaptations, "top") or not helper.references_bound(library, recipe, manifest.inputs) or not helper.registered_inputs_bound(library, recipe, manifest.inputs): return reject("注册上衣/身体或来源闭包无效。")
	if not helper.ref_valid(library, recipe.template, manifest.inputs, "templates") or not helper.ref_valid(library, recipe.motion_set, manifest.inputs, "templates") or not helper.ref_valid(library, recipe.slots.top, manifest.inputs, "parts"): return reject("母版/动作/上衣绑定失效。")
	var template = helper.read_json(helper.safe_file(library, recipe.template.file))
	var motion = helper.read_json(helper.safe_file(library, recipe.motion_set.file))
	var design = helper.read_json(helper.safe_file(library, recipe.slots.top.file))
	if not template is Dictionary or not template.get("template_id") is String or template.get("motion_set") != recipe.motion_set.file or not motion is Dictionary or motion.get("template_id") != template.template_id or not motion.get("actions") is Dictionary or not design is Dictionary or design.get("category") != "top": return reject("母版/动作集/款式身份无效。")
	if not recipe.clips is Array or recipe.clips.is_empty() or recipe.clips.size() > 8 or not recipe.required_capabilities is Array or recipe.required_capabilities.size() != recipe.clips.size(): return reject("注册能力范围缺失。")
	var required: Dictionary = {}
	for cap in recipe.required_capabilities:
		if not helper.exact(cap, "action_id direction") or not cap.action_id is String or not cap.direction is String or not cap.action_id in ["idle", "walk"] or not cap.direction in ["south", "west", "east", "north"]: return reject("仅支持已登记站立/行走。")
		var key = cap.action_id + "-" + cap.direction
		if required.has(key): return reject("能力重复。")
		required[key] = true
	var prepared = load_preparations(project, library, suite.prepared_sources, manifest.inputs)
	if prepared.is_empty(): return reject("准备源、工具、输出或直接输入闭包失效。")
	var adaptation = helper.read_json(helper.safe_file(library, recipe.adaptations.top.file))
	if not adaptation is Dictionary or not adaptation.get("views") is Array or not adaptation.get("mappings") is Array: return reject("上衣注册目录无效。")
	var catalog = {"views": {}, "mappings": {}}
	for row in adaptation.views:
		if not row is Dictionary or not row.get("view_id") is String or catalog.views.has(row.view_id): return reject("来源视图重复。")
		catalog.views[row.view_id] = row
	for row in adaptation.mappings:
		if not row is Dictionary or not row.get("mapping_id") is String or catalog.mappings.has(row.mapping_id): return reject("姿态映射重复。")
		catalog.mappings[row.mapping_id] = row
	if not manifest.outputs is Array: return reject("构建输出缺失。")
	var pending_frames = {"A": [], "B": []}; var pending_meta: Array = []; var pending_clips: Dictionary = {}
	var pending_geometry: Dictionary = {}; var used_sources: Dictionary = {}; var seen_clips: Dictionary = {}; var output_index = 0
	for clip in recipe.clips:
		if not helper.exact(clip, "action_id direction action poses variant canvas_px root_anchor_px display_scale frames") or not helper.geometry(clip) or not clip.action_id is String or not clip.direction is String or not clip.frames is Array or clip.frames.is_empty() or clip.frames.size() > 256: return reject("动作几何或帧类型无效。")
		var key = clip.action_id + "-" + clip.direction
		for candidate in clip.frames:
			if not helper.exact(candidate, "pose_id duration_ms layers layer_order registration composition") or not candidate.pose_id is String or not helper.integer(candidate.duration_ms, 1): return reject("动作帧类型无效。")
		if not required.has(key) or seen_clips.has(key) or not helper.template_clip_valid(library, clip, manifest.inputs, template.template_id) or motion.actions.get(clip.action_id) != clip.action.file: return reject("动作/姿态次序或时序不符。")
		seen_clips[key] = true
		var geo = {"canvas_px": clip.canvas_px, "root_anchor_px": clip.root_anchor_px, "display_scale": clip.display_scale}
		if pending_geometry.is_empty(): pending_geometry = geo
		if pending_geometry != geo: return reject("动作整帧几何不一致。")
		var poses = helper.read_json(helper.safe_file(library, clip.poses.file))
		var canonical_frames = poses.variants[clip.variant].frames
		var indices: Array = []; var pose_ids: Dictionary = {}
		for index in range(clip.frames.size()):
			var frame = clip.frames[index]; var original = canonical_frames[index]
			if not helper.exact(frame, "pose_id duration_ms layers layer_order registration composition") or not frame.pose_id is String or pose_ids.has(frame.pose_id) or not helper.integer(frame.duration_ms, 1) or frame.registration != null or frame.composition != "alpha-over" or not frame.layers is Array or frame.layers.size() != 2 or not frame.layer_order is Array or frame.layer_order.size() != 2: return reject("帧身份/组合接口无效。")
			pose_ids[frame.pose_id] = true
			var body: Dictionary = {}; var top: Dictionary = {}
			for layer in frame.layers:
				if not layer is Dictionary or not layer.get("slot") is String: return reject("帧图层无效。")
				if layer.slot == "body" and body.is_empty(): body = layer
				elif layer.slot == "top" and top.is_empty(): top = layer
				else: return reject("图层槽位重复或未知。")
			if not helper.exact(body, "id slot pose_id texture source source_bundle ownership coverage occlusion interface_scope placement_mode offset_px local_scale") or not original.get("file") is String or not helper.digest(original.get("sha256")): return reject("身体canonical引用无效。")
			var canonical = {"file": original.file, "sha256": original.sha256}
			if body.texture != canonical or body.pose_id != frame.pose_id or body.interface_scope != "same-pose-reference" or body.ownership != null or body.coverage != null or body.occlusion != null or body.placement_mode != "full_frame" or not helper.uniform_pair(body.offset_px, 0) or not helper.uniform_pair(body.local_scale, 1): return reject("身体层必须使用真实canonical整帧。")
			if not body.get("id") is String or not top.get("id") is String or frame.layer_order != [body.id, top.id]: return reject("身体/上衣层序无效。")
			var body_image = checked_png(library, canonical, manifest.inputs, clip.canvas_px)
			if body_image == null: return reject("真实身体PNG失效。")
			var used = top_valid(library, top, clip, frame, canonical, catalog, manifest.inputs, prepared)
			if used == "": return reject("上衣未绑定同姿态准备源输出。")
			used_sources[used] = true
			if output_index >= manifest.outputs.size(): return reject("严格输出帧缺失。")
			var texture = helper.output_texture(manifest_path.get_base_dir(), manifest.outputs[output_index], clip, frame)
			if texture == null: return reject("严格输出PNG/SHA/RGBA失效。")
			indices.append(pending_meta.size()); pending_frames.A.append(ImageTexture.create_from_image(body_image)); pending_frames.B.append(texture)
			pending_meta.append({"pose_id": frame.pose_id, "duration_ms": frame.duration_ms, "action_id": clip.action_id, "direction": clip.direction})
			output_index += 1
		if not pending_clips.has(clip.action_id): pending_clips[clip.action_id] = {}
		pending_clips[clip.action_id][clip.direction] = indices
	if output_index != manifest.outputs.size() or not pending_clips.has("walk") or not pending_clips.has("idle") or pending_clips.walk.keys().size() != pending_clips.idle.keys().size(): return reject("站立/行走或输出范围不完整。")
	for direction in pending_clips.walk:
		if not pending_clips.idle.has(direction): return reject("方向缺少匹配站立。")
	if used_sources.size() != suite.prepared_sources.size(): return reject("准备源引用未被实际使用。")
	frames = pending_frames; frame_metadata = pending_meta; clips = pending_clips; geometry = pending_geometry
	runtime = suite.runtime; artifact_digest = manifest.artifact_digest; prepared_frames = prepared; error = ""
	return true
