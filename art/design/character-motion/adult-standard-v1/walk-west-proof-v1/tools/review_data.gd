extends RefCounted
## Fail closed on malformed/changed baked inputs. PNGs load directly without imports.
var error: String = ""
var manifest: Dictionary = {}
var textures: Dictionary = {}
var layer_textures: Dictionary = {}
var mask_textures: Dictionary = {}
var manifest_path: String
var source_root: String

func reject(message: String) -> bool:
	error = message
	return false

func read_texture(path: String, expected_hash: String = "") -> Texture2D:
	if not FileAccess.file_exists(path):
		error = "Missing image: " + path
		return null
	if expected_hash != "" and FileAccess.get_sha256(path) != expected_hash:
		error = "Changed image: " + path
		return null
	var image := Image.new()
	if image.load(path) != OK:
		error = "Cannot load PNG: " + path
		return null
	return ImageTexture.create_from_image(image)

func safe_relative(value: Variant) -> bool:
	return value is String and not value.is_empty() and not value.is_absolute_path() and not ".." in value.split("/")

func open_manifest(path: String) -> bool:
	error = ""
	textures.clear()
	layer_textures.clear()
	mask_textures.clear()
	manifest_path = path
	if not path.is_absolute_path() or not FileAccess.file_exists(path):
		return reject("Absolute existing manifest required")
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not parsed is Dictionary:
		return reject("Invalid manifest JSON")
	manifest = parsed
	if manifest.get("schema_version") != 1 or manifest.get("canvas_px") != [512.0, 768.0]:
		return reject("Unsupported schema/canvas")
	if manifest.get("root_anchor_px") != [256.0, 708.0]:
		return reject("This review requires root [256,708]")
	var display_scale: Variant = manifest.get("display_scale")
	if not (display_scale is float or display_scale is int) or not is_finite(float(display_scale)) or display_scale <= 0 or display_scale > 1:
		return reject("Invalid display_scale")
	var frames: Variant = manifest.get("frames")
	if not frames is Array or frames.size() != 4:
		return reject("Four timeline frames required")
	for i in range(4):
		if not frames[i] is Dictionary or frames[i].get("pose_id") != "walk_w_%d" % i or not (frames[i].get("duration_ms") is float or frames[i].get("duration_ms") is int) or not is_finite(float(frames[i].get("duration_ms", 0))) or float(frames[i].get("duration_ms", 0)) <= 0 or float(frames[i]["duration_ms"]) != floor(float(frames[i]["duration_ms"])):
			return reject("Invalid timeline pose/duration")
	var recipes: Variant = manifest.get("recipes")
	if not recipes is Dictionary or recipes.size() != 2 or not recipes.has("A") or not recipes.has("B"):
		return reject("A/B recipes required")
	var base := path.get_base_dir()
	# Older schema-1 manifests used baked/ under the motion root.
	source_root = base.path_join(str(manifest.get("source_root", ".."))).simplify_path()
	var inputs: Dictionary = manifest.get("inputs", {})
	for recipe in ["A", "B"]:
		var mapped: Variant = recipes[recipe].get("frames")
		if not mapped is Array or mapped.size() != 4:
			return reject("Four baked frames required")
		textures[recipe] = []
		layer_textures[recipe] = []
		mask_textures[recipe] = []
		for i in range(4):
			var frame: Dictionary = mapped[i]
			if frame.get("pose_id") != frames[i]["pose_id"] or frame.get("duration_ms") != frames[i]["duration_ms"]:
				return reject("A/B timeline mismatch")
			if not safe_relative(frame.get("file")) or str(frame.get("sha256", "")).length() != 64:
				return reject("Invalid baked file/hash")
			var texture := read_texture(base.path_join(frame["file"]), frame["sha256"])
			if texture == null:
				return false
			if texture.get_size() != Vector2(512, 768):
				return reject("Baked texture dimensions differ")
			textures[recipe].append(texture)
			var sources: Array = []
			var masks: Array = []
			for layer in frame.get("layers", []):
				if not safe_relative(layer.get("source")) or not inputs.has(layer["source"]):
					return reject("Layer source missing from input hashes")
				var source := read_texture(source_root.path_join(layer["source"]), inputs[layer["source"]]["sha256"])
				if source == null:
					return false
				var offset: Array = layer.get("offset_px", [])
				if offset.size() != 2 or float(offset[0]) != floor(float(offset[0])) or float(offset[1]) != floor(float(offset[1])):
					return reject("Invalid source offset")
				var point := Vector2i(int(offset[0]), int(offset[1]))
				if point.x < 0 or point.y < 0 or point.x + source.get_width() > 512 or point.y + source.get_height() > 768:
					return reject("Source outside registered canvas")
				var registered := Image.create(512, 768, false, Image.FORMAT_RGBA8)
				var source_image := source.get_image()
				source_image.convert(Image.FORMAT_RGBA8)
				registered.blit_rect(source_image, Rect2i(Vector2i.ZERO, source_image.get_size()), point)
				sources.append(ImageTexture.create_from_image(registered))
				var mask: Texture2D = null
				if layer.has("hide_mask"):
					if not safe_relative(layer["hide_mask"]) or not inputs.has(layer["hide_mask"]):
						return reject("Mask missing from input hashes")
					mask = read_texture(source_root.path_join(layer["hide_mask"]), inputs[layer["hide_mask"]]["sha256"])
					if mask == null:
						return false
					if mask.get_size() != Vector2(512, 768):
						return reject("Mask canvas mismatch")
				masks.append(mask)
			layer_textures[recipe].append(sources)
			mask_textures[recipe].append(masks)
	return true
