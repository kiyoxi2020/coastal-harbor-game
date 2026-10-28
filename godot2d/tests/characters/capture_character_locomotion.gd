extends SceneTree
## Visual evidence only: frozen world position, monotonic animation clock.
## Real keyboard/displacement is validated separately by the native trial test.
var trial
var output := "/private/tmp/coastal-locomotion-visual"
var samples: Array = []
func _initialize() -> void:
	call_deferred("run")
func run() -> void:
	var art := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--trial-art-root="): art = arg.trim_prefix("--trial-art-root=")
		elif arg.begins_with("--trial-evidence="): output = arg.trim_prefix("--trial-evidence=")
	if art.is_empty() or not output.begins_with("/private/tmp/coastal-") or DisplayServer.get_name() == "headless":
		quit(1); return
	DirAccess.make_dir_recursive_absolute(output)
	trial = load("res://dev/characters/character_walk_trial.tscn").instantiate()
	trial.art_root = art
	root.add_child(trial)
	await process_frame
	if trial.load_error != "": printerr(trial.load_error); quit(1); return
	trial.set_physics_process(false)
	for garment in ["A", "B"]:
		trial.set_garment(garment)
		for direction in ["south", "west", "east", "north"]:
			trial.set_motion_direction(direction)
			trial.current_action = "idle"
			trial.refresh_pose()
			await snap("idle-%s-%s" % [garment, direction], 0)
			trial.current_action = "walk"
			for i in range(4):
				trial.phase_ms = i * 80.0
				trial.refresh_pose()
				await snap("still-%s-%s-%d" % [garment, direction, i], 0)
			var start := Time.get_ticks_usec()
			var index := 0
			var elapsed := 0
			while elapsed < 4400000:
				elapsed = Time.get_ticks_usec() - start
				trial.phase_ms = fposmod(elapsed / 1000.0 * 0.75, 320.0)
				trial.refresh_pose()
				await snap("sequence-%s-%s-%04d" % [garment, direction, index], elapsed)
				index += 1
				await create_timer(0.035).timeout
	var record := {"artifact_digest": trial.artifact_digest, "capture_script_sha256": FileAccess.get_sha256("res://tests/characters/capture_character_locomotion.gd"), "scope": "stationary native animation crops; no foot-lock or movement claim", "playback_rate": 0.75, "samples": samples}
	var file := FileAccess.open(output.path_join("capture.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(record, "  ")); file.close()
	print("CAPTURE_OK ", samples.size())
	quit(0)
func snap(label: String, elapsed: int) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	var screenshot := root.get_texture().get_image()
	var center: Vector2 = trial.actor.get_global_transform_with_canvas().origin
	var region := Rect2i(Vector2i(center) - Vector2i(160, 200), Vector2i(320, 240))
	region = region.intersection(Rect2i(Vector2i.ZERO, screenshot.get_size()))
	var crop := screenshot.get_region(region)
	crop.save_png(output.path_join(label + ".png"))
	samples.append({"file": label + ".png", "elapsed_usec": elapsed, "wall_usec": Time.get_ticks_usec(), "pose_id": trial.frame_metadata[trial.current_frame()]["pose_id"], "garment": trial.garment, "crop_px": [region.position.x, region.position.y, region.size.x, region.size.y], "viewport_px": [screenshot.get_width(), screenshot.get_height()]})
