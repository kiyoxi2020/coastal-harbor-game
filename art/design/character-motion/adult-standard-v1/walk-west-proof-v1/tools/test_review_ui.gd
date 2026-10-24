extends SceneTree

func _initialize() -> void:
	call_deferred("exercise")

func exercise() -> void:
	var scene = load("res://review.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	if not scene.loaded:
		printerr("FAIL UI manifest load")
		quit(1)
		return
	scene.paused = true
	scene.elapsed_ms = 0
	scene.step(-1)
	if scene.timeline.frame_at(scene.elapsed_ms) != 3 or not scene.paused:
		printerr("FAIL reverse single-step wraps and pauses")
		quit(1)
		return
	scene.step(1)
	if scene.elapsed_ms != 0:
		printerr("FAIL forward single-step wraps")
		quit(1)
		return
	scene.toggle_pause()
	if scene.paused:
		printerr("FAIL resume")
		quit(1)
		return
	scene.paused = true
	var before: float = scene.elapsed_ms
	scene._process(0.5)
	if scene.elapsed_ms != before:
		printerr("FAIL pause clock")
		quit(1)
		return
	scene.toggle_background()
	if not scene.dark:
		printerr("FAIL backdrop toggle")
		quit(1)
		return
	var font: Color = scene.status.get_theme_color("font_color")
	if font.get_luminance() < 0.75:
		printerr("FAIL dark backdrop requires readable light labels")
		quit(1)
		return
	scene.source_mode = 1
	scene.update_view()
	if scene.source_sprite.texture != scene.data.mask_textures["A"][0][0]:
		printerr("FAIL target mask inspection")
		quit(1)
		return
	if scene.sprites[0].scale != scene.sprites[1].scale or scene.sprites[2].scale != scene.sprites[0].scale * 2:
		printerr("FAIL unified display scales")
		quit(1)
		return
	print("PASS UI: pause/resume, wrapping single-step, background, target mask and A/B scales")
	quit(0)
