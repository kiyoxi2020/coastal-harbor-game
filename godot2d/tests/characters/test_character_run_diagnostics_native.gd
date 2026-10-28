extends "res://tests/test_life_farming_native.gd"
var trial
var review
func run() -> void:
	evidence = "/private/tmp/coastal-run-diagnostics-native"
	DirAccess.make_dir_recursive_absolute(evidence)
	trial = load("res://dev/characters/character_walk_trial.tscn").instantiate()
	trial.art_root = ProjectSettings.globalize_path("res://../art/characters/builds/locomotion-r001")
	trial.run_candidate_root = ProjectSettings.globalize_path("res://../art/characters/builds/run-r001")
	trial.review_enabled = true
	trial.run_diagnostics_enabled = true
	root.add_child(trial)
	for i in range(4): await process_frame
	review = trial.review_panel
	check("native_renderer", DisplayServer.get_name() != "headless")
	check("diagnostic_startup_loads_both_directions", trial.run_diagnostics_digest != "" and trial.run_diagnostics.size() == 2)
	check("starts_with_long_sleeve_comparison", trial.garment == "B" and review.visible and review.message.text.contains("诊断稿"))
	trial.set_physics_process(false)
	review.set_playing(false)
	for direction_index in [0,3]:
		var direction: String = ["south","west","east","north"][direction_index]
		await click(review.direction_buttons[direction_index])
		check(direction+"_mouse_selects_diagnostic", review.review_direction == direction and review.motion_view.texture != null and review.message.text.contains("诊断稿"))
		for i in range(4):
			review.preview_phase_ms = i * 80.0
			review.refresh_preview()
			check(direction+"_pose_"+str(i), review.motion_view.texture == trial.frames.B[trial.clips.run[direction][i]])
			await capture("%s-long-sleeve-pose-%d" % [direction,i])
		review.set_playing(true)
		var previous: float = review.preview_phase_ms
		await create_timer(0.15).timeout
		check(direction+"_diagnostic_animates", review.preview_phase_ms != previous)
		review.set_playing(false)
	var end: Vector2 = review.get_global_transform_with_canvas() * review.size
	check("diagnostic_note_fits_screen", end.x <= 2560 and end.y <= 1440)
	trial.set_physics_process(true)
	for direction in ["south","north"]:
		root.grab_focus()
		for i in range(4): await process_frame
		trial.reset_position()
		trial.actor.position = Vector2(296,244) if direction == "south" else Vector2(600,244)
		var code: int = KEY_S if direction == "south" else KEY_W
		await key(code,true);await key(KEY_SHIFT,true)
		await create_timer(0.12).timeout
		check(direction+"_actual_long_sleeve_running", trial.current_action == "run" and trial.facing == direction and trial.garment == "B" and trial.status.text.contains("诊断稿"))
		await capture(direction+"-long-sleeve-world")
		await key(KEY_SHIFT,false)
		await key(code,false)
		for i in range(3): await physics_frame
		check(direction+"_returns_to_approved_idle", trial.current_action == "idle" and trial.garment == "B")
	var metadata := {"scope":"User-requested rejected-art inspection, not visual acceptance", "candidate_sha256":trial.run_candidate_digest,"garments_sha256":trial.run_garments_digest,"diagnostics_sha256":trial.run_diagnostics_digest,"inputs":{}}
	for path in ["res://dev/characters/character_walk_trial.gd","res://dev/characters/character_walk_trial.tscn","res://dev/characters/character_motion_review.gd","res://dev/characters/character_motion_review.tscn","res://tests/characters/test_character_run_diagnostics_native.gd"]:
		metadata.inputs[path] = FileAccess.get_sha256(path)
	var file := FileAccess.open(evidence.path_join("metadata.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(metadata,"  "));file.close()
	trial.queue_free()
	finish()
