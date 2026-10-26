extends RefCounted
## Read-only key-pose catalog. No actor, gameplay events, save service, or art edits.
const ACTIONS := ["water", "hoe", "harvest"]
const DISPLAY_SCALE := 138.0 / 1164.0
var clips: Dictionary = {}
var error: String = ""
var catalog_sha256: String = ""

func _reject(message: String) -> bool:
	clips.clear()
	catalog_sha256 = ""
	error = message
	return false

func _relative_file(value: Variant) -> bool:
	if not value is String or value.is_empty() or value.is_absolute_path() or ":" in value or "\\" in value:
		return false
	for part in value.split("/", true):
		if part in ["", ".", ".."]: return false
	return true

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

func load_catalog(project_root: String, catalog_path: String = "res://dev/farming_review_catalog.json") -> bool:
	clips.clear()
	error = ""
	catalog_sha256 = ""
	if not project_root.is_absolute_path() or not DirAccess.dir_exists_absolute(project_root):
		return _reject("农事评审项目根目录无效。")
	var catalog: Variant = _json(catalog_path)
	if not catalog is Dictionary or catalog.get("schema_version") != 1 or catalog.get("template_id") != "adult-standard-v1":
		return _reject("农事评审目录合同无效。")
	var records: Variant = catalog.get("clips")
	if not records is Array or records.size() != ACTIONS.size():
		return _reject("农事评审目录缺少三个已登记小样。")
	var pending := {}
	for record in records:
		if not record is Dictionary: return _reject("农事评审条目无效。")
		var action: Variant = record.get("action_id")
		if action not in ACTIONS or pending.has(action): return _reject("农事评审动作重复或未知。")
		if not _relative_file(record.get("candidate")) or not _sha(record.get("sha256")):
			return _reject("农事评审候选路径或哈希无效。")
		var note: Variant = record.get("note")
		if not note is String or note.is_empty(): return _reject("农事评审缺少关键姿态说明。")
		var candidate_path := project_root.path_join(str(record.candidate))
		if not FileAccess.file_exists(candidate_path) or FileAccess.get_sha256(candidate_path) != record.sha256:
			return _reject("农事评审候选缺失或哈希不匹配。")
		var data: Variant = _json(candidate_path)
		if not data is Dictionary or data.get("schema_version") != 1 or data.get("template_id") != "adult-standard-v1" or data.get("action_id") != action or data.get("direction") != "west":
			return _reject("农事评审体型、动作或方向不匹配。")
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
		var directory := candidate_path.get_base_dir()
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
			textures.append(ImageTexture.create_from_image(image))
			durations.append(int(entry.duration_ms))
			poses.append(str(entry.pose_id))
		pending[action] = {
			"action_id": str(action), "direction": "west", "garment": "A",
			"textures": textures, "durations_ms": durations, "pose_ids": poses,
			"canvas_px": Vector2(float(canvas[0]), float(canvas[1])),
			"root_anchor_px": Vector2(float(anchor[0]), float(anchor[1])),
			"display_scale": DISPLAY_SCALE, "candidate_sha256": str(record.sha256),
			"note": str(note), "source_status": str(status)
		}
	clips = pending
	catalog_sha256 = FileAccess.get_sha256(catalog_path)
	return true

func get_clip(action: String, direction: String, garment: String) -> Dictionary:
	if action not in ACTIONS or direction != "west" or garment != "A": return {}
	return clips.get(action, {})
