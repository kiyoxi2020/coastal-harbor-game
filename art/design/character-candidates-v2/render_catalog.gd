extends SceneTree
## Standalone native inventory viewer. Never loads project scenes or user:// saves.
const CATEGORIES = ["body", "hair", "top", "pants", "shoes", "hat"]
const DIRECTIONS = ["south", "west", "east", "north"]
const VIEW_SIZE = Vector2i(1600, 1200)
const CARD_SIZE = Vector2(780, 218)
var project_root := ""
var output_dir := ""
var catalog_path := ""
var only_category := ""
var catalog: Dictionary = {}
var textures: Dictionary = {}
var loaded_hashes: Dictionary = {}
var manifest: Dictionary = {"kind": "native_catalog_render", "pages": [], "scope": "Native loading and inventory overview only; aesthetic/swap/user acceptance remain separate."}
var requested_scale := 0.0
var page_size := 10
var canvas: Control

func _initialize() -> void:
	call_deferred("render")

func fail(message: String) -> void:
	push_error(message)
	quit(1)

func absolute_file(relative: String) -> String:
	if relative.is_empty() or relative.is_absolute_path() or ".." in relative.split("/"):
		return ""
	var path := project_root.path_join(relative).simplify_path()
	if not FileAccess.file_exists(path):
		return ""
	return path

func get_texture(relative: String) -> Texture2D:
	if textures.has(relative):
		return textures[relative]
	var path := absolute_file(relative)
	if path.is_empty():
		push_warning("Missing image: " + relative)
		return null
	var image := Image.load_from_file(path)
	if image == null or image.is_empty():
		push_warning("Unreadable image: " + relative)
		return null
	var texture := ImageTexture.create_from_image(image)
	# ImageTexture uses original bytes and dimensions. Scaling happens only on Sprite2D.
	assert(texture.get_size() == Vector2(image.get_size()))
	textures[relative] = texture
	loaded_hashes[relative] = FileAccess.get_sha256(path)
	return texture

func metadata_for(item: Dictionary) -> Dictionary:
	var result: Dictionary = {}
	var value: Variant = item.get("metadata", {})
	if value is String:
		var path := absolute_file(value)
		if not path.is_empty():
			var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
			if parsed is Dictionary:
				result = parsed
				loaded_hashes[value] = FileAccess.get_sha256(path)
	elif value is Dictionary:
		result = value
	return result

func text_at(value: String, at: Vector2, color: Color, size: int = 15) -> void:
	var label := Label.new()
	label.text = value
	label.position = at
	label.add_theme_color_override("font_color", color)
	label.add_theme_font_size_override("font_size", size)
	canvas.add_child(label)

func frame_paths(item: Dictionary, mode: String, direction: String) -> Array:
	var frames: Variant = item.get(mode, {})
	if not frames is Dictionary:
		return []
	var value: Variant = frames.get(direction, "")
	if value is String:
		return [value] if not value.is_empty() else []
	if value is Array:
		return value
	return []

func page_frame_scale(items: Array, mode: String) -> float:
	if requested_scale > 0.0:
		return requested_scale
	var largest := Vector2.ONE
	for item in items:
		for direction in DIRECTIONS:
			for path in frame_paths(item, mode, direction):
				var texture := get_texture(str(path))
				if texture != null:
					largest = largest.max(texture.get_size())
	# One uniform fit for the entire page, never independent width/height stretching.
	return minf(178.0 / largest.x, 180.0 / largest.y)

func draw_page(items: Array, category: String, mode: String, layer_index: int, background: String, page: int) -> void:
	for child in canvas.get_children():
		canvas.remove_child(child)
		child.queue_free()
	var bg := ColorRect.new()
	bg.color = Color(background)
	bg.size = Vector2(VIEW_SIZE)
	canvas.add_child(bg)
	var foreground := Color("172127") if background == "e8e0ce" else Color.WHITE
	var scale_factor := page_frame_scale(items, mode)
	text_at(category + " / " + mode + " / S W E N / page " + str(page + 1) + " / layer " + str(layer_index + 1), Vector2(20, 10), foreground, 21)
	text_at("source canvas fit=" + str(scale_factor) + "; missing frame is shown as a blank slot; no appearance approval", Vector2(20, 42), foreground)
	for index in range(items.size()):
		var item: Dictionary = items[index]
		var card := Vector2(20 + (index % 2) * CARD_SIZE.x, 83 + floori(float(index) / 2.0) * CARD_SIZE.y)
		# Candidate labels deliberately use the catalog ID only.
		text_at(str(item.get("id", "missing_id")), card, foreground, 17)
		var metadata := metadata_for(item)
		var display: Variant = item.get("display", metadata.get("display", {}))
		if not display is Dictionary:
			display = {}
		var declared_template: Variant = metadata.get("body_template", item.get("template_id", "UNDECLARED"))
		print("CATALOG_ITEM ", item.get("id", ""), " body_template=", declared_template, " status=", item.get("status", "UNDECLARED"))
		var item_scale := float(display.get("scale", scale_factor))
		if requested_scale > 0.0:
			item_scale = requested_scale
		for col in range(DIRECTIONS.size()):
			var direction: String = DIRECTIONS[col]
			var paths := frame_paths(item, mode, direction)
			if layer_index >= paths.size():
				continue
			var texture := get_texture(str(paths[layer_index]))
			if texture == null:
				continue
			var actor := Sprite2D.new()
			actor.centered = false
			actor.texture = texture
			actor.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			actor.scale = Vector2.ONE * item_scale
			var slot := card + Vector2(col * 193 + 6, 26)
			var anchors: Variant = display.get("root_anchors", {})
			var anchor: Variant = anchors.get(direction, null) if anchors is Dictionary else null
			if anchor is Array and anchor.size() == 2:
				actor.position = slot + Vector2(89, 180) - Vector2(float(anchor[0]), float(anchor[1])) * item_scale
			else:
				actor.position = slot + (Vector2(178, 180) - texture.get_size() * item_scale) * 0.5
			canvas.add_child(actor)
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	var name := category + "-" + mode + "-p" + str(page + 1) + "-layer" + str(layer_index + 1) + "-" + background + ".png"
	var result := root.get_texture().get_image().save_png(output_dir.path_join(name))
	if result != OK:
		fail("Cannot save native screenshot: " + name)
		return
	manifest["pages"].append({"file": name, "category": category, "mode": mode, "layer": layer_index, "page": page, "background": background, "uniform_page_scale": scale_factor, "ids": items.map(func(item: Dictionary): return item.get("id", ""))})

func render() -> void:
	var options: Dictionary = {}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--") and "=" in argument:
			var pair := argument.substr(2).split("=", true, 1)
			options[pair[0]] = pair[1]
	project_root = str(options.get("root", "")).simplify_path()
	output_dir = str(options.get("out", "")).simplify_path()
	catalog_path = str(options.get("catalog", "art/design/character-candidates-v2/catalog.json"))
	only_category = str(options.get("category", ""))
	requested_scale = float(options.get("scale", "0"))
	page_size = int(options.get("per-page", "10"))
	if DisplayServer.get_name() == "headless":
		fail("A native renderer is required; headless loading is not visual validation.")
		return
	if not project_root.is_absolute_path() or not output_dir.begins_with("/private/tmp/coastal-"):
		fail("Required: --root=/absolute/project --out=/private/tmp/coastal-... .")
		return
	if page_size < 1 or page_size > 10 or (not only_category.is_empty() and only_category not in CATEGORIES):
		fail("--per-page must be 1..10; --category must name a catalog category.")
		return
	var resolved_catalog := absolute_file(catalog_path)
	if resolved_catalog.is_empty():
		fail("Missing project-relative catalog.")
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(resolved_catalog))
	if not parsed is Dictionary or parsed.get("schema_version") != 1 or not parsed.get("categories") is Dictionary:
		fail("Expected schema_version=1 and categories object.")
		return
	catalog = parsed
	DirAccess.make_dir_recursive_absolute(output_dir)
	root.size = VIEW_SIZE
	root.content_scale_size = VIEW_SIZE
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	canvas = Control.new()
	root.add_child(canvas)
	manifest["catalog_sha256"] = FileAccess.get_sha256(resolved_catalog)
	manifest["renderer_sha256"] = FileAccess.get_sha256(get_script().resource_path)
	manifest["window"] = [VIEW_SIZE.x, VIEW_SIZE.y]
	manifest["requested_scale"] = requested_scale
	manifest["per_page"] = page_size
	for category in CATEGORIES:
		if not only_category.is_empty() and category != only_category:
			continue
		var entries: Variant = catalog["categories"].get(category, [])
		if not entries is Array:
			fail("Category must be an array: " + category)
			return
		for start in range(0, entries.size(), page_size):
			var items: Array = entries.slice(start, mini(start + page_size, entries.size()))
			for mode in ["previews", "components"]:
				var layer_count := 1
				for item in items:
					for direction in DIRECTIONS:
						layer_count = maxi(layer_count, frame_paths(item, mode, direction).size())
				for layer_index in range(layer_count):
					for background in ["e8e0ce", "172127"]:
						await draw_page(items, category, mode, layer_index, background, floori(float(start) / float(page_size)))
	manifest["loaded_files"] = loaded_hashes
	var file := FileAccess.open(output_dir.path_join("render-manifest.json"), FileAccess.WRITE)
	if file == null:
		fail("Cannot save render-manifest.json.")
		return
	file.store_string(JSON.stringify(manifest, "\t"))
	file.close()
	print("CATALOG_NATIVE_RENDER_FINISHED; pages=", manifest["pages"].size(), "; no aesthetic/swap/user approval granted")
	quit()
