extends "res://tests/test_life_farming_native.gd"
var trial
func run() -> void:
	evidence = "/private/tmp/coastal-walk-trial-native"
	DirAccess.make_dir_recursive_absolute(evidence)
	trial = load("res://dev/character_walk_trial.tscn").instantiate()
	root.add_child(trial)
	for i in range(4): await process_frame
	check("native_renderer", DisplayServer.get_name() != "headless")
	check("real_art_ready", trial.load_error == "")
	if trial.load_error != "": finish(); return
	await capture("01-short-75-start")
	await key(KEY_A, true)
	var start: Vector2 = trial.actor.position
	var begin_ms: float = trial.phase_ms
	await create_timer(0.65).timeout
	check("keyboard_moves_at_54", is_equal_approx(trial.actor.velocity.x, -54.0) and trial.actor.position.x < start.x - 25.0)
	await key(KEY_A, false)
	var delta_x: float = start.x - trial.actor.position.x
	check("clock_tracks_actual_travel", is_equal_approx(trial.phase_ms, fposmod(begin_ms + delta_x / 72.0 * 1000.0, 320.0)))
	await capture("02-short-75-walk")
	var phase: float = trial.phase_ms
	await key(KEY_2, true)
	await key(KEY_2, false)
	check("keyboard_long_same_pose", trial.garment == "B" and trial.phase_ms == phase)
	await capture("03-long-same-pose")
	await click(trial.get_node("TrialUI/Panel/Margin/Rows/Controls/Short"))
	check("short_button", trial.garment == "A" and trial.phase_ms == phase)
	await click(trial.get_node("TrialUI/Panel/Margin/Rows/Controls/Long"))
	check("long_button", trial.garment == "B" and trial.phase_ms == phase)
	var slider: HSlider = trial.speed_slider
	var point: Vector2 = slider.get_global_transform_with_canvas() * Vector2(slider.size.x * 0.02, slider.size.y * 0.5)
	for pressed in [true, false]:
		var event := InputEventMouseButton.new()
		event.position = point
		event.button_index = MOUSE_BUTTON_LEFT
		event.pressed = pressed
		root.push_input(event, true)
		await process_frame
	check("mouse_slider_slow", trial.speed_factor <= 0.55 and trial.frame_duration_ms() >= 145.0)
	await capture("04-long-slower")
	await key(KEY_R, true)
	await key(KEY_R, false)
	check("keyboard_reset", trial.actor.position == Vector2(490,244) and trial.phase_ms == 0.0)
	var still: Vector2 = trial.actor.position
	await key(KEY_D, true)
	await key(KEY_SHIFT, true)
	await create_timer(0.15).timeout
	await key(KEY_D, false)
	await key(KEY_SHIFT, false)
	check("missing_direction_not_faked", trial.actor.position == still and not trial.pose.flip_h)
	var panel: Control = trial.get_node("TrialUI/Panel")
	check("ui_inside_native_view", Rect2(Vector2.ZERO,Vector2(2560,1440)).encloses(Rect2(panel.get_global_transform_with_canvas()*Vector2.ZERO,panel.size*2)))
	check("visible_actor_in_world", trial.pose.is_visible_in_tree() and trial.actor.get_parent().y_sort_enabled)
	check("same_world_foot_scale", is_equal_approx(trial.pose.scale.x * trial.get_node("WorldCamera").zoom.x,138.0/582.0))
	trial.set_speed_factor(0.75)
	trial.set_garment("A")
	await capture("05-final-default")
	var metadata := {"artifact_digest":trial.artifact_digest,"default_world_speed":54,"default_frame_ms":80.0/0.75,"camera_zoom":4,"source_canvas":[512,768],"world_scale":trial.pose.scale.x,"render_canvas":[2560,1440],"captured_utc":Time.get_datetime_string_from_system(true),"trial_inputs":{}}
	for path in ["res://dev/character_walk_trial.gd","res://dev/character_walk_trial.tscn","res://scenes/world/harbor_exterior.tscn","res://scripts/world_camera.gd"]:
		metadata.trial_inputs[path] = FileAccess.get_sha256(path)
	var file := FileAccess.open(evidence.path_join("metadata.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(metadata,"  "))
	file.close()
	finish()
