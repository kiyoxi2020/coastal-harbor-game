extends "res://tests/test_life_farming_native.gd"
var trial
var candidate_root := ""
func run() -> void:
	evidence = "/private/tmp/coastal-run-directions-native"
	DirAccess.make_dir_recursive_absolute(evidence)
	candidate_root = ProjectSettings.globalize_path("res://../art/characters/builds/run-r001")
	trial = load("res://dev/characters/character_walk_trial.tscn").instantiate()
	trial.art_root = ProjectSettings.globalize_path("res://../art/characters/builds/locomotion-r001")
	root.add_child(trial)
	for i in range(4): await process_frame
	check("native_renderer", DisplayServer.get_name() != "headless")
	check("candidate_loads", trial.load_run_candidate(candidate_root))
	if not trial.clips.has("run"):
		printerr(trial.motion_error)
		finish()
		return
	root.grab_focus()
	for i in range(4): await process_frame
	var directions: Array = trial.clips.run.keys()
	var codes := {"west": KEY_A, "east": KEY_D, "north": KEY_W, "south": KEY_S}
	for direction in directions:
		trial.reset_position()
		# Use the already verified unobstructed paths, not the market frontage.
		if direction == "north": trial.actor.position = Vector2(600, 244)
		elif direction == "south": trial.actor.position = Vector2(296, 244)
		var before: Vector2 = trial.actor.position
		await key(codes[direction], true)
		await key(KEY_SHIFT, true)
		await create_timer(0.14).timeout
		check(direction + "_actual_run", trial.current_action == "run" and trial.facing == direction and is_equal_approx(trial.actor.velocity.length(), 81.0))
		check(direction + "_actual_displacement", trial.actor.position.distance_to(before) > 4.0)
		await capture(direction + "-running-harbor")
		await key(KEY_2, true)
		await key(KEY_2, false)
		if trial.has_motion_garment("run", direction, "B"):
			check(direction + "_keyboard_long_sleeve", trial.garment == "B" and trial.current_action == "run")
		else:
			check(direction + "_missing_long_sleeve_rejected", trial.garment == "A" and trial.motion_error != "")
		await key(KEY_1, true)
		await key(KEY_1, false)
		check(direction + "_keyboard_short_sleeve", trial.garment == "A")
		await key(KEY_SHIFT, false)
		await create_timer(0.07).timeout
		if trial.current_action != "walk":
			print("RUN_NATIVE_DIAGNOSTIC ", direction, " position=", trial.actor.position, " velocity=", trial.actor.velocity, " focused=", trial.focused, " collisions=", trial.actor.get_slide_collision_count())
		check(direction + "_return_walk", trial.current_action == "walk")
		await key(codes[direction], false)
		for i in range(3): await physics_frame
		check(direction + "_stop_idle", trial.current_action == "idle" and trial.facing == direction)
	trial.set_physics_process(false)
	for direction in directions:
		for garment in ["A", "B"]:
			if not trial.has_motion_garment("run", direction, garment): continue
			trial.current_action = "walk"
			trial.set_garment("A")
			trial.set_motion_direction(direction)
			trial.set_garment(garment)
			check(direction + garment + "_select", trial.set_locomotion_action("run"))
			await record_clip(direction, garment)
	trial.queue_free()
	finish()
func record_clip(direction: String, garment: String) -> void:
	var label := direction + "-" + garment
	var samples: Array = []
	var captures: Array = []
	var folder := "sequence-" + label
	DirAccess.make_dir_recursive_absolute(evidence.path_join(folder))
	var start := Time.get_ticks_msec()
	var last_capture := -100
	var cycle: float = trial.clip_duration("run", direction)
	var target_ms := int(ceil(cycle / trial.speed_factor * 10.0))
	while Time.get_ticks_msec() - start <= target_ms + 34:
		var elapsed := Time.get_ticks_msec() - start
		trial.phase_ms = fposmod(elapsed * trial.speed_factor, cycle)
		trial.refresh_pose()
		await create_timer(1.0 / 60.0).timeout
		RenderingServer.force_draw()
		samples.append({"wall_ms": elapsed, "phase_ms": trial.phase_ms, "pose_id": trial.frame_metadata[trial.current_frame()].pose_id})
		if elapsed - last_capture >= 33:
			var picture := root.get_texture().get_image()
			picture.resize(1280, 720, Image.INTERPOLATE_NEAREST)
			var filename := folder.path_join("%06d.png" % samples.size())
			captures.append({"file": filename, "image": picture})
			samples[-1].capture_file = filename
			last_capture = elapsed
	check(label + "_ten_cycles", samples.size() > 100 and samples[-1].wall_ms >= target_ms)
	for item in captures: item.image.save_png(evidence.path_join(item.file))
	var file := FileAccess.open(evidence.path_join("metadata-" + label + ".json"), FileAccess.WRITE)
	file.store_string(JSON.stringify({"candidate_manifest_sha256": trial.run_candidate_digest, "run_garments_sha256": trial.run_garments_digest, "trial_script_sha256": FileAccess.get_sha256("res://dev/characters/character_walk_trial.gd"), "test_script_sha256": FileAccess.get_sha256("res://tests/characters/test_character_run_directions_native.gd"), "direction": direction, "garment": garment, "samples": samples, "scope": "native playback and controls; not user acceptance or approved contact trajectories"}, "  "))
	file.close()
