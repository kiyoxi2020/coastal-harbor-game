extends SceneTree
var trial
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var art := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--trial-art-root="): art = arg.trim_prefix("--trial-art-root=")
	if art.is_empty() or DisplayServer.get_name() == "headless": quit(1); return
	var output := "/private/tmp/coastal-locomotion-backgrounds"
	DirAccess.make_dir_recursive_absolute(output)
	trial = load("res://dev/character_walk_trial.tscn").instantiate()
	trial.art_root = art
	root.add_child(trial)
	await process_frame
	if trial.load_error != "": printerr(trial.load_error); quit(1); return
	trial.set_physics_process(false)
	var layer := CanvasLayer.new()
	layer.layer = 100
	root.add_child(layer)
	var background := ColorRect.new()
	background.size = Vector2(root.size)
	layer.add_child(background)
	var sprites: Array = []
	for row in range(2):
		for column in range(4):
			var sprite := Sprite2D.new()
			sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			sprite.centered = false
			sprite.offset = Vector2(-256, -708)
			sprite.scale = Vector2.ONE * 138.0 / 582.0
			sprite.position = Vector2((column + 0.5) * root.size.x / 4.0, (row + 0.62) * root.size.y / 2.0)
			layer.add_child(sprite)
			sprites.append(sprite)
	var captures: Array = []
	for tone in ["light", "dark"]:
		background.color = Color("e5e0d2") if tone == "light" else Color("15202b")
		for frame in range(5):
			var action := "idle" if frame == 0 else "walk"
			for row in range(2):
				var garment := "A" if row == 0 else "B"
				for column in range(4):
					var direction: String = ["south", "west", "east", "north"][column]
					var index: int = trial.clips[action][direction][0 if frame == 0 else frame - 1]
					sprites[row * 4 + column].texture = trial.frames[garment][index]
			await process_frame
			await RenderingServer.frame_post_draw
			var filename := "%s-%d.png" % [tone, frame]
			root.get_texture().get_image().save_png(output.path_join(filename))
			captures.append({"file": filename, "action": action, "frame": 0 if frame == 0 else frame - 1, "sha256": FileAccess.get_sha256(output.path_join(filename))})
	var file := FileAccess.open(output.path_join("backgrounds.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify({"artifact_digest": trial.artifact_digest, "scope": "8sprites A/B rows and south/west/east/north columns, exact game rendering scale on native light/dark grounds", "viewport_px": [root.size.x, root.size.y], "source_canvas_px": [512,768], "display_scale": 138.0/582.0, "captures": captures, "script_sha256": FileAccess.get_sha256("res://tests/capture_character_locomotion_backgrounds.gd")}, "  "))
	file.close()
	print("BACKGROUNDS_OK 10 sheets / 80 pose views")
	quit(0)
