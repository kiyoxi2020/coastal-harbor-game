extends SceneTree
## Reproducible native diagnostic board. Never registers visual approval.
var candidate := ""
var idle := ""
var evidence := ""
var checks := {}
func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--candidate="): candidate = argument.trim_prefix("--candidate=")
		elif argument.begins_with("--evidence="): evidence = argument.trim_prefix("--evidence=")
	call_deferred("run")
func label_at(parent: Node, message: String, at: Vector2) -> void:
	var label := Label.new()
	label.position = at
	label.text = message
	label.add_theme_font_override("font",load("res://assets/NotoSansCJKsc-Regular.otf"))
	label.add_theme_font_size_override("font_size",22)
	label.add_theme_color_override("font_color", Color(0.1,0.25,0.3) if at.y < 700 else Color(0.9,0.95,1))
	parent.add_child(label)
func add_pose(parent: Node, texture: Texture2D, anchor: Vector2, scale: float, column: int) -> void:
	for row in range(2):
		for multiplier in [1,2]:
			var sprite := Sprite2D.new()
			sprite.centered = false
			sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			sprite.texture = texture
			sprite.offset = -anchor
			sprite.scale = Vector2.ONE*scale*multiplier
			sprite.position = Vector2(110+column*820+(multiplier-1)*360,590+row*700)
			parent.add_child(sprite)
func run() -> void:
	if not evidence.begins_with("/private/tmp/coastal-") or not FileAccess.file_exists(candidate):
		printerr("candidate/idle or isolated evidence path invalid");quit(1);return
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(candidate))
	var manifest_path := ProjectSettings.globalize_path("res://../art/design/character-motion/adult-standard-v1/locomotion-v1/baked/export-manifest.json")
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
	var recipe: String = data.get("garment","A")
	var idle_entry: Dictionary = {}
	for entry in manifest.recipes[recipe].frames:
		if entry.pose_id == "idle_%s_0" % data.direction: idle_entry = entry
	if idle_entry.is_empty(): printerr("matching idle reference missing");quit(1);return
	idle = manifest_path.get_base_dir().path_join(idle_entry.file)
	checks.same_direction_recipe_idle = idle_entry.pose_id == "idle_%s_0" % data.direction and FileAccess.get_sha256(idle)==idle_entry.sha256
	checks.native_renderer = DisplayServer.get_name() != "headless"
	var node := Node2D.new()
	root.add_child(node)
	for row in range(2):
		var bg := ColorRect.new()
		bg.color = Color(0.88,0.92,0.9) if row == 0 else Color(0.06,0.12,0.17)
		bg.position = Vector2(0,row*700)
		bg.size = Vector2(2560,700)
		node.add_child(bg)
		label_at(node,"候选诊断：%s / %s / %s · 1x与2x源密度显示；不代表用户认可" % [data.action_id,data.direction,data.get("garment","A")],Vector2(25,20+row*700))
	var idle_image := Image.load_from_file(idle)
	add_pose(node,ImageTexture.create_from_image(idle_image),Vector2(256,708),138.0/582.0,0)
	for row in range(2): label_at(node,"认可idle参照 1x / 2x",Vector2(25,70+row*700))
	for i in range(data.frames.size()):
		var entry: Dictionary = data.frames[i]
		var path := candidate.get_base_dir().path_join(entry.file)
		var picture := Image.load_from_file(path)
		checks[entry.pose_id+"_texture_hash"] = FileAccess.get_sha256(path)==entry.sha256
		checks[entry.pose_id+"_canvas"] = picture.get_size()==Vector2i(int(data.canvas_px[0]),int(data.canvas_px[1]))
		add_pose(node,ImageTexture.create_from_image(picture),Vector2(data.root_anchor_px[0],data.root_anchor_px[1]),float(data.display_scale),i+1)
		for row in range(2): label_at(node,entry.pose_id+" 1x / 2x",Vector2(845+i*820,70+row*700))
	root.grab_focus()
	for i in range(5): await process_frame
	await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute(evidence)
	var image := root.get_texture().get_image()
	checks.capture_native_resolution = image.get_size()==Vector2i(2560,1440)
	checks.capture_saved = image.save_png(evidence.path_join("native-board.png"))==OK
	var inputs := {"idle_manifest_sha256":FileAccess.get_sha256(manifest_path),"idle_pose_id":idle_entry.pose_id,"idle_recipe":recipe,"candidate_sha256":FileAccess.get_sha256(candidate),"idle_sha256":FileAccess.get_sha256(idle),"capture_script_sha256":FileAccess.get_sha256("res://tests/capture_character_farming_candidate.gd"),"candidate_path":candidate,"idle_path":idle,"checks":checks,"scope":"Native static density/transparency board only. No continuous contact, modular compatibility, or user acceptance."}
	var file := FileAccess.open(evidence.path_join("report.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(inputs,"  "));file.close()
	print("CANDIDATE_NATIVE checks=",checks.size()," passed=",not checks.values().has(false))
	quit(1 if checks.values().has(false) else 0)
