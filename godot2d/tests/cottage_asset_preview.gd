extends SceneTree

static func player_preview_scale(frame_width: float) -> float:
	return 2.0 * 48.0 / frame_width

func _initialize() -> void:
	call_deferred("capture")

func capture() -> void:
	var args := OS.get_cmdline_user_args()
	var output := "/private/tmp/cottage-asset-preview.png"
	if args.size() >= 2 and args[0] == "--output":
		output = args[1]
	root.size = Vector2i(1280, 720)
	var background := ColorRect.new()
	background.color = Color("#283b45")
	background.size = Vector2(root.size)
	root.add_child(background)
	var baseline := 520.0
	var atlas_script = load("res://scripts/atlas.gd")
	var player := AnimatedSprite2D.new()
	player.sprite_frames = atlas_script.player_frames()
	player.animation = "south"
	player.frame = 0
	var frame_width: float = player.sprite_frames.get_frame_texture("south", 0).get_width()
	player.scale = Vector2.ONE * player_preview_scale(frame_width)
	player.position = Vector2(145, baseline - 48.0)
	player.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	root.add_child(player)
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/house-interior/pilot.json"))
	var positions := [Vector2(365, 0), Vector2(595, 0), Vector2(795, 0), Vector2(995, 0)]
	var names := ["bed", "door-closed", "door-half", "door-open"]
	for index in names.size():
		var sprite := Sprite2D.new()
		sprite.texture = load("res://assets/house-interior/" + names[index] + ".png")
		var entry: Dictionary = manifest[names[index].replace("-", "_")]
		var anchor: Array = entry["pivot"] if index == 0 else entry["floor_anchor"]
		var logical_height: float = float(entry["logical_size"][1])
		var anchor_y: float = float(anchor[1])
		sprite.position = Vector2(positions[index].x, baseline - (anchor_y - logical_height / 2.0) * 2.0)
		sprite.scale = Vector2(2, 2)
		sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		root.add_child(sprite)
	await process_frame
	await process_frame
	var image := root.get_texture().get_image()
	var error := image.save_png(output)
	if error != OK:
		printerr("FAIL preview save: ", error)
		quit(1)
		return
	print("PASS preview: ", output)
	quit(0)
