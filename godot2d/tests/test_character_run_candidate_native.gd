extends "res://tests/test_life_farming_native.gd"
var trial
func run() -> void:
	evidence = "/private/tmp/coastal-run-garments-native"
	DirAccess.make_dir_recursive_absolute(evidence)
	trial = load("res://dev/character_walk_trial.tscn").instantiate()
	trial.art_root = ProjectSettings.globalize_path("res://../art/design/character-motion/adult-standard-v1/locomotion-v1")
	root.add_child(trial)
	for i in range(4): await process_frame
	check("native_renderer", DisplayServer.get_name() != "headless")
	check("approved_walk_loaded", trial.load_error == "")
	check("run_candidate_loaded", trial.load_run_candidate(ProjectSettings.globalize_path("res://../art/design/character-motion/adult-standard-v1/run-west-proof-v1")))
	if not trial.clips.has("run"): finish(); return
	root.grab_focus()
	for i in range(4): await process_frame
	await key(KEY_A, true)
	await create_timer(0.16).timeout
	check("walking_before_shift", trial.current_action == "walk")
	var start: Vector2 = trial.actor.position
	await key(KEY_SHIFT, true)
	await create_timer(0.18).timeout
	check("shift_selects_run", trial.current_action == "run" and is_equal_approx(trial.actor.velocity.length(), 81.0))
	check("real_run_displacement", start.x - trial.actor.position.x > 8)
	await capture("01-running-harbor")
	if trial.run_garments_digest != "":
		await key(KEY_2, true)
		await key(KEY_2, false)
		check("native_running_long_sleeve_switch", trial.garment == "B" and trial.current_action == "run")
		await capture("01b-long-sleeve-running-harbor")
	await key(KEY_SHIFT, false)
	await create_timer(0.08).timeout
	check("shift_release_walk", trial.current_action == "walk" and is_equal_approx(trial.actor.velocity.length(), 54.0))
	await key(KEY_A, false)
	for i in range(3): await physics_frame
	check("stop_idle", trial.current_action == "idle" and trial.facing == "west")
	await capture("02-stop-idle")
	trial.actor.position = Vector2(30, 244)
	await key(KEY_A, true)
	await key(KEY_SHIFT, true)
	await create_timer(0.6).timeout
	var blocked_phase: float = trial.phase_ms
	await create_timer(0.12).timeout
	check("run_collision_stops_clock", trial.current_action == "idle" and trial.phase_ms == blocked_phase and trial.actor.position.x > 20)
	await key(KEY_A, false)
	await key(KEY_SHIFT, false)
	trial.reset_position()
	# Native full-size stop frames and continuous 10 cycles at actual render scale.
	trial.set_physics_process(false)
	trial.set_motion_direction("west")
	trial.set_locomotion_action("run")
	for garment in (["A", "B"] if trial.run_garments_digest != "" else ["A"]):
		trial.set_garment(garment)
		check(garment + "_run_available", trial.garment == garment and trial.has_motion_garment("run", "west", garment))
		await record_cycles(garment)
	trial.queue_free()
	finish()

func record_cycles(garment: String) -> void:
	for i in range(4):
		trial.phase_ms = i * 80.0
		trial.refresh_pose()
		await capture("%s-run-pose-%d" % [garment, i])
	var samples: Array = []
	var captured_images: Array = []
	DirAccess.make_dir_recursive_absolute(evidence.path_join("sequence-" + garment))
	var start_ms := Time.get_ticks_msec()
	var last_capture := -100
	while Time.get_ticks_msec() - start_ms < 4300:
		var elapsed := Time.get_ticks_msec() - start_ms
		trial.phase_ms = fposmod(elapsed * 0.75, 320.0)
		trial.refresh_pose()
		await create_timer(1.0 / 60.0).timeout
		# Explicit draw avoids waiting for a post_draw signal after a static frame
		# when the macOS window is throttled during review tooling.
		RenderingServer.force_draw()
		samples.append({"wall_ms": elapsed, "phase_ms": trial.phase_ms, "pose_id": trial.frame_metadata[trial.current_frame()].pose_id})
		if elapsed - last_capture >= 33:
			var picture := root.get_texture().get_image()
			picture.resize(1280, 720, Image.INTERPOLATE_NEAREST)
			var filename := "sequence-%s/%06d.png" % [garment, samples.size()]
			captured_images.append({"file": filename, "image": picture})
			samples[-1]["capture_file"] = filename
			last_capture = elapsed
	check(garment + "_ten_native_cycles", samples.size() > 100 and samples[-1].wall_ms >= 4266)
	for item in captured_images: item.image.save_png(evidence.path_join(item.file))
	var file := FileAccess.open(evidence.path_join("metadata-" + garment + ".json"), FileAccess.WRITE)
	file.store_string(JSON.stringify({"candidate_manifest_sha256": trial.run_candidate_digest, "run_garments_sha256": trial.run_garments_digest, "garment": garment, "walk_artifact": trial.artifact_digest, "samples": samples, "scope": "native control and timed animation; not approved joint/contact trajectories", "trial_script_sha256": FileAccess.get_sha256("res://dev/character_walk_trial.gd")}, "  "))
	file.close()
