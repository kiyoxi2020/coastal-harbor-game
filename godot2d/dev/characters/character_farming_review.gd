extends RefCounted
const ResourcePaths = preload("res://dev/characters/character_resource_paths.gd")
## Read-only key-pose catalog. No actor, gameplay events, save service, or art edits.
const ACTIONS := ["water", "hoe", "harvest"]
const DIRECTIONS := ["south", "west", "east", "north"]
const GARMENTS := ["A", "B"]
const PHASES := {"hoe":["ready","lift","contact","recovery"],"water":["ready","raise","pour","recovery"],"harvest":["ready","reach","pluck","recovery"]}
const DISPLAY_SCALE := 138.0 / 1164.0
var clips: Dictionary = {}
var error: String = ""
var catalog_sha256: String = ""
var catalog_version := 0

func _reject(message: String) -> bool:
	clips.clear()
	catalog_sha256 = ""
	catalog_version = 0
	error = message
	return false

func _relative_file(value: Variant) -> bool:
	return ResourcePaths.relative_file(value)

func _sha(value: Variant) -> bool:
	if not value is String or value.length() != 64: return false
	for character in value:
		if character not in "0123456789abcdef": return false
	return true

func _number(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value))

func _positive_integer(value: Variant) -> bool:
	return _number(value) and value > 0 and value <= 2147483647 and float(value) == floor(float(value))

func _pair(value: Variant) -> bool:
	return value is Array and value.size() == 2 and _number(value[0]) and _number(value[1])

func _json(path: String) -> Variant:
	if not FileAccess.file_exists(path): return null
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null: return null
	return JSON.parse_string(file.get_as_text())

func load_catalog(project_root: String, catalog_path: String = "") -> bool:
	if catalog_path.is_empty(): catalog_path = project_root.path_join("art/characters/reviews/farming/catalog.json")
	clips.clear()
	error = ""
	catalog_sha256 = ""
	catalog_version = 0
	if not project_root.is_absolute_path() or not DirAccess.dir_exists_absolute(project_root):
		return _reject("农事评审项目根目录无效。")
	var catalog: Variant = _json(catalog_path)
	if not catalog is Dictionary or (not _number(catalog.get("schema_version")) or float(catalog.schema_version) not in [1.0, 2.0]) or catalog.get("template_id") != "adult-standard-v1":
		return _reject("农事评审目录合同无效。")
	if ResourcePaths.base(project_root, catalog_path, catalog).is_empty(): return _reject("农事目录资源根无效。")
	var version := int(catalog.schema_version)
	var records: Variant = catalog.get("clips")
	var required_count := ACTIONS.size() if version == 1 else ACTIONS.size()*DIRECTIONS.size()*GARMENTS.size()
	if not records is Array or records.size() != required_count:
		return _reject("农事评审目录缺少完整动作、方向或上衣组合。")
	var pending := {}
	for record in records:
		if not record is Dictionary: return _reject("农事评审条目无效。")
		var action: Variant = record.get("action_id")
		var direction: Variant = record.get("direction", "west") if version == 1 else record.get("direction")
		var garment: Variant = record.get("garment", "A") if version == 1 else record.get("garment")
		if version == 1 and (direction != "west" or garment != "A"):
			return _reject("旧版农事目录只支持西向短袖。")
		if action not in ACTIONS or direction not in DIRECTIONS or garment not in GARMENTS:
			return _reject("农事评审动作、方向或上衣未知。")
		var key: String = str(action) if version == 1 else "%s/%s/%s" % [action,direction,garment]
		if pending.has(key): return _reject("农事评审组合重复。")
		if not _relative_file(record.get("candidate")) or not _sha(record.get("sha256")):
			return _reject("农事评审候选路径或哈希无效。")
		var note: Variant = record.get("note")
		if not note is String or note.is_empty(): return _reject("农事评审缺少关键姿态说明。")
		var candidate_path := project_root.path_join(str(record.candidate))
		if not FileAccess.file_exists(candidate_path) or FileAccess.get_sha256(candidate_path) != record.sha256:
			return _reject("农事评审候选缺失或哈希不匹配。")
		var data: Variant = _json(candidate_path)
		if not data is Dictionary or data.get("schema_version") != 1 or data.get("template_id") != "adult-standard-v1" or data.get("action_id") != action or data.get("direction") != direction or (version == 2 and data.get("garment") != garment):
			return _reject("农事评审体型、动作或方向不匹配。")
		if catalog.has("resource_root") and not data.has("resource_root"): return _reject("农事候选资源根缺失。")
		var status: Variant = data.get("status")
		if not status is String or status.is_empty(): return _reject("农事评审缺少源状态。")
		var scale: Variant = data.get("display_scale")
		if data.get("source_density_scale_vs_idle") != 2 or not _number(scale) or not is_equal_approx(float(scale), DISPLAY_SCALE):
			return _reject("农事评审必须使用母版两倍源密度及固定显示比例。")
		var canvas: Variant = data.get("canvas_px")
		var anchor: Variant = data.get("root_anchor_px")
		if not _pair(canvas) or not _positive_integer(canvas[0]) or not _positive_integer(canvas[1]):
			return _reject("农事评审画布无效。")
		if not _pair(anchor) or anchor[0] < 0 or anchor[1] < 0 or anchor[0] >= canvas[0] or anchor[1] >= canvas[1]:
			return _reject("农事评审根点超出画布。")
		var directory := ResourcePaths.base(project_root, candidate_path, data)
		if directory.is_empty(): return _reject("农事资源根无效。")
		var inputs: Variant = data.get("inputs")
		if not inputs is Dictionary or inputs.is_empty(): return _reject("农事评审源依赖缺失。")
		for reference in inputs:
			if not _relative_file(reference) or not _sha(inputs[reference]):
				return _reject("农事评审源依赖路径或哈希无效。")
			var dependency := directory.path_join(str(reference))
			if not FileAccess.file_exists(dependency) or FileAccess.get_sha256(dependency) != inputs[reference]:
				return _reject("农事评审源依赖缺失或哈希不匹配。")
		var entries: Variant = data.get("frames")
		if not entries is Array or entries.is_empty(): return _reject("农事评审关键姿态缺失。")
		var textures: Array[Texture2D] = []
		var durations: Array[int] = []
		var poses: Array[String] = []
		var phases_seen := {}
		var texture_hashes := {}
		var previous_phase := -1
		if version == 2 and entries.size() < 4: return _reject("完整农事序列少于四个真实姿态。")
		for entry in entries:
			if not entry is Dictionary or not entry.get("pose_id") is String or entry.pose_id.is_empty() or poses.has(entry.pose_id):
				return _reject("农事评审姿态ID缺失或重复。")
			if not _positive_integer(entry.get("duration_ms")) or not _relative_file(entry.get("file")) or not _sha(entry.get("sha256")):
				return _reject("农事评审纹理路径、时长或哈希无效。")
			if not _relative_file(entry.get("source")) or not _sha(entry.get("source_sha256")) or inputs.get(entry.source) != entry.source_sha256:
				return _reject("农事评审姿态源依赖不匹配。")
			var path := directory.path_join(str(entry.file))
			if not FileAccess.file_exists(path) or FileAccess.get_sha256(path) != entry.sha256:
				return _reject("农事评审纹理缺失或哈希不匹配。")
			var image := Image.load_from_file(path)
			if image == null or image.get_size() != Vector2i(int(canvas[0]), int(canvas[1])):
				return _reject("农事评审实际纹理尺寸与画布不匹配。")
			if version == 2:
				var phase: Variant = entry.get("phase")
				if phase not in PHASES[action]: return _reject("完整农事序列缺少合法动作阶段。")
				var phase_index: int = PHASES[action].find(phase)
				if phase_index < previous_phase: return _reject("农事动作阶段顺序无效。")
				previous_phase = phase_index
				phases_seen[phase] = true
				texture_hashes[entry.sha256] = true
			textures.append(ImageTexture.create_from_image(image))
			durations.append(int(entry.duration_ms))
			poses.append(str(entry.pose_id))
		if version == 2 and (phases_seen.size() != 4 or texture_hashes.size() < 4):
			return _reject("完整农事序列未覆盖预备、使用、收回或真实姿态重复。")
		pending[key] = {
			"action_id": str(action), "direction": str(direction), "garment": str(garment),
			"textures": textures, "durations_ms": durations, "pose_ids": poses,
			"canvas_px": Vector2(float(canvas[0]), float(canvas[1])),
			"root_anchor_px": Vector2(float(anchor[0]), float(anchor[1])),
			"display_scale": DISPLAY_SCALE, "candidate_sha256": str(record.sha256),
			"note": str(note), "source_status": str(status)
		}
	clips = pending
	catalog_version = version
	catalog_sha256 = FileAccess.get_sha256(catalog_path)
	return true

func get_clip(action: String, direction: String, garment: String) -> Dictionary:
	if action not in ACTIONS or direction not in DIRECTIONS or garment not in GARMENTS: return {}
	if catalog_version == 1:
		if direction != "west" or garment != "A": return {}
		return clips.get(action, {})
	return clips.get("%s/%s/%s" % [action,direction,garment], {})
