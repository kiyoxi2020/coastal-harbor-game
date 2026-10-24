extends "res://tests/test_life_farming_native.gd"
var trial
var samples: Array = []
func run() -> void:
	evidence = "/private/tmp/coastal-locomotion-trial-native"
	var source_root := "/private/tmp/coastal-locomotion-fixture"
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--trial-art-root="): source_root = argument.trim_prefix("--trial-art-root=")
		elif argument.begins_with("--trial-evidence="): evidence = argument.trim_prefix("--trial-evidence=")
	if not evidence.begins_with("/private/tmp/coastal-"):
		printerr("Native test evidence must use /private/tmp/coastal-*")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(evidence)
	trial = load("res://dev/character_walk_trial.tscn").instantiate()
	trial.art_root = source_root
	root.add_child(trial)
	for i in range(4): await process_frame
	check("native_renderer", DisplayServer.get_name() != "headless")
	check("complete_schema2_loaded", trial.load_error == "" and trial.schema_version == 2)
	if trial.load_error != "": finish(); return
	check("default_accepted_75_percent", is_equal_approx(trial.walk_speed(), 54.0))
	check("camera_scale_once", is_equal_approx(trial.pose.scale.x * trial.get_node("WorldCamera").zoom.x, 138.0 / 582.0))
	await capture("00-idle-start")
	var code_map := {"west": KEY_A, "east": KEY_D, "north": KEY_W, "south": KEY_S}
	for direction in ["west", "east", "north", "south"]:
		trial.reset_position()
		# Market/crate blockers border the original north/south route at x490.
		# Use the verified eastern path for unobstructed clock measurement.
		if direction == "north": trial.actor.position = Vector2(600, 244)
		# WaterEast starts at y272 across the eastern shore: the stairs gap
		# at x296 is the unobstructed southern route.
		elif direction == "south": trial.actor.position = Vector2(296, 244)
		var start: Vector2 = trial.actor.position
		var begin_phase: float = trial.phase_ms
		await key(code_map[direction], true)
		for sample in range(3):
			await create_timer(0.08).timeout
			await capture("walk-%s-%d" % [direction, sample])
			samples.append({"direction": direction, "position": [trial.actor.position.x, trial.actor.position.y], "phase_ms": trial.phase_ms, "frame": trial.current_frame(), "pose_id": trial.frame_metadata[trial.current_frame()]["pose_id"], "wall_usec": Time.get_ticks_usec()})
		await key(code_map[direction], false)
		for i in range(2): await physics_frame
		var displacement: Vector2 = trial.actor.position - start
		check("keyboard_move_" + direction, displacement.length() > 5 and trial.facing == direction)
		var expected_clock: float = fposmod(begin_phase + displacement.length() / 72.0 * 1000.0, trial.clip_duration("walk", direction))
		if not is_equal_approx(trial.phase_ms, expected_clock):
			print("NATIVE_CLOCK_DIAGNOSTIC ", direction, " displacement=", displacement, " actual=", trial.phase_ms, " expected=", expected_clock, " collisions=", trial.actor.get_slide_collision_count())
		check("actual_motion_clock_" + direction, is_equal_approx(trial.phase_ms, expected_clock))
		check("release_idle_" + direction, trial.current_action == "idle" and trial.facing == direction)
		await capture("idle-" + direction)
	# Freeze physics only while checking an atomic direction/garment change.
	trial.set_physics_process(false)
	trial.current_action = "walk"
	trial.set_motion_direction("west")
	trial.phase_ms = trial.clip_duration("walk", "west") * 0.55
	var fraction: float = trial.phase_ms / trial.clip_duration("walk", "west")
	trial.set_motion_direction("east")
	check("turn_preserves_normalized_phase", is_equal_approx(trial.phase_ms / trial.clip_duration("walk", "east"), fraction))
	var phase: float = trial.phase_ms
	await key(KEY_2, true)
	await key(KEY_2, false)
	check("keyboard_garment_same_phase", trial.garment == "B" and trial.phase_ms == phase and trial.facing == "east")
	await capture("long-east-same-phase")
	await click(trial.get_node("TrialUI/Panel/Margin/Rows/Controls/Short"))
	check("mouse_garment_same_phase", trial.garment == "A" and trial.phase_ms == phase)
	check("never_mirrors", not trial.pose.flip_h and not trial.pose.flip_v)
	trial.set_physics_process(true)
	trial.reset_position()
	# Native input is intentionally ignored when the OS window loses focus.
	# Restore real focus after mouse/capture work; never override trial.focused.
	root.grab_focus()
	for i in range(8): await process_frame
	check("diagonal_window_focused", trial.focused)
	await key(KEY_D, true)
	await key(KEY_S, true)
	await create_timer(0.12).timeout
	if not is_equal_approx(trial.actor.velocity.length(), 54.0):
		print("DIAGONAL_DIAGNOSTIC position=", trial.actor.position, " velocity=", trial.actor.velocity, " focused=", trial.focused, " input=", trial.movement_input(), " collisions=", trial.actor.get_slide_collision_count())
	check("diagonal_speed_normalized", is_equal_approx(trial.actor.velocity.length(), 54.0))
	await key(KEY_D, false)
	await key(KEY_S, false)
	await key(KEY_R, true)
	await key(KEY_R, false)
	check("keyboard_reset", trial.actor.position == trial.get_node("Start").position and trial.phase_ms == 0)
	trial.actor.position = Vector2(30, 244)
	await key(KEY_A, true)
	await create_timer(0.5).timeout
	var blocked: float = trial.phase_ms
	await create_timer(0.12).timeout
	check("native_collision_clock_stops", trial.actor.position.x > 20 and trial.phase_ms == blocked and trial.current_action == "idle")
	await key(KEY_A, false)
	await capture("collision-idle")
	var metadata := {"scope": "fixture_controls_or_real_artifact_only_not_art_acceptance", "artifact_digest": trial.artifact_digest, "art_root": trial.art_root, "schema_version": trial.schema_version, "world_speed": trial.walk_speed(), "samples": samples, "trial_inputs": {}}
	for path in ["res://dev/character_walk_trial.gd", "res://dev/character_walk_trial.tscn", "res://scenes/world/harbor_exterior.tscn", "res://scripts/world_camera.gd"]:
		metadata.trial_inputs[path] = FileAccess.get_sha256(path)
	var file := FileAccess.open(evidence.path_join("metadata.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(metadata, "  ")); file.close()
	finish()
