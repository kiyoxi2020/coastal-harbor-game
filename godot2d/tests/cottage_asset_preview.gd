extends SceneTree

func _initialize() -> void:
	call_deferred("capture")

func capture() -> void:
	var args := OS.get_cmdline_user_args()
	var output := "/private/tmp/cottage-asset-preview.png"
	if args.size() >= 2 and args[0] == "--output":
		output = args[1]
	root.size = Vector2i(800, 500)
	var background := ColorRect.new()
	background.color = Color("#283b45")
	background.size = Vector2(800, 500)
	root.add_child(background)
	var atlas_script = load("res://scripts/atlas.gd")
	var player := AnimatedSprite2D.new()
	player.sprite_frames = atlas_script.player_frames()
	player.animation = "south"
	player.frame = 0
	player.position = Vector2(95, 410)
	player.scale = Vector2(2, 2)
	player.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	root.add_child(player)
	var positions := [Vector2(235, 275), Vector2(410, 290), Vector2(555, 290), Vector2(700, 290)]
	var names := ["bed", "door-closed", "door-half", "door-open"]
	for index in names.size():
		var sprite := Sprite2D.new()
		sprite.texture = load("res://assets/house-interior/" + names[index] + ".png")
		sprite.position = positions[index]
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
