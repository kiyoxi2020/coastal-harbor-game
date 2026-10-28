extends "res://tests/test_life_farming_native.gd"
var trial
var review
func focus_window() -> void:
	root.grab_focus()
	for i in range(4): await process_frame
func choose(button: Button) -> void:
	var before: Vector2 = trial.actor.position
	var phase: float = trial.phase_ms
	var facing: String = trial.facing
	await click(button)
	check("selector_keeps_world_state_" + button.name, trial.actor.position == before and trial.phase_ms == phase and trial.facing == facing)
func fits(control: Control) -> bool:
	var transform := control.get_global_transform_with_canvas()
	var start: Vector2 = transform * Vector2.ZERO
	var end: Vector2 = transform * control.size
	return start.x >= 0 and start.y >= 0 and end.x <= 2560 and end.y <= 1440
func run() -> void:
	evidence = "/private/tmp/coastal-motion-review-native"
	DirAccess.make_dir_recursive_absolute(evidence)
	trial = load("res://dev/characters/character_walk_trial.tscn").instantiate()
	trial.art_root = ProjectSettings.globalize_path("res://../art/characters/builds/locomotion-r001")
	trial.run_candidate_root = ProjectSettings.globalize_path("res://../art/characters/builds/run-r001")
	trial.review_enabled = true
	root.add_child(trial)
	for i in range(4): await process_frame
	review = trial.review_panel
	check("native_renderer", DisplayServer.get_name() != "headless")
	check("all_motion_loaded", trial.load_error == "" and trial.clips.get("run", {}).size() == 4)
	check("review_opens_by_default", review.visible and review.review_action == "run" and review.review_direction == "south")
	check("comparison_fits_screen", fits(review))
	check("top_controls_fit_screen", fits(trial.get_node("TrialUI/Panel")))
	var scale: float = review.motion_view.get_global_transform_with_canvas().get_scale().x
	check("actual_equal_2x_scale", is_equal_approx(scale, (138.0/582.0)*2.0) and review.motion_view.scale == review.reference_view.scale)
	await focus_window()
	await capture("01-south-run-comparison")
	await click(review.play_button)
	var phase: float = review.preview_phase_ms
	await create_timer(0.15).timeout
	check("mouse_pause", not review.playing and review.preview_phase_ms == phase)
	var pose: int = review.current_pose_index()
	await click(review.get_node("Margin/Rows/Playback/Next"))
	check("mouse_step", review.current_pose_index() == (pose + 1) % 4 and not review.playing)
	await capture("02-paused-frame")
	for index in range(4):
		await choose(review.direction_buttons[index])
		check("mouse_direction_" + str(index), review.review_direction == ["south", "west", "east", "north"][index])
	check("choose_north", review.review_direction == "north")
	await capture("03-north-run-comparison")
	await choose(review.action_buttons[1])
	check("choose_walk", review.review_action == "walk")
	await capture("04-north-walk-comparison")
	await choose(review.action_buttons[2])
	await key(KEY_2, true); await key(KEY_2, false)
	check("missing_B_is_explicit", trial.garment == "B" and review.motion_view.texture == null and review.message.text.contains("未提供"))
	await capture("05-unavailable-long-sleeve")
	await key(KEY_1, true); await key(KEY_1, false)
	var position_before: Vector2 = trial.actor.position
	await key(KEY_C, true); await key(KEY_C, false)
	check("C_hides_panel_without_reset", not review.visible and trial.actor.position == position_before)
	await key(KEY_C, true); await key(KEY_C, false)
	check("C_restores_panel", review.visible)
	await click(trial.get_node("TrialUI/Panel/Margin/Rows/Controls/Review"))
	check("mouse_toggle_panel", not review.visible)
	await focus_window()
	trial.reset_position()
	await key(KEY_D, true)
	await key(KEY_SHIFT, true)
	await create_timer(0.12).timeout
	check("world_run_still_works", trial.current_action == "run" and trial.facing == "east" and trial.actor.position.x > position_before.x + 4)
	await key(KEY_2, true); await key(KEY_2, false)
	check("world_running_wardrobe", trial.current_action == "run" and trial.garment == "B")
	await capture("06-east-long-sleeve-world")
	await key(KEY_SHIFT, false)
	await create_timer(0.04).timeout
	check("world_return_to_walk", trial.current_action == "walk")
	await key(KEY_D, false)
	await key(KEY_C, true); await key(KEY_C, false)
	check("panel_remains_available_after_movement", review.visible)
	var report := {"scope":"native review controls/layout and shared-world locomotion; user acceptance pending", "candidate_sha256":trial.run_candidate_digest, "run_garments_sha256":trial.run_garments_digest, "walk_artifact":trial.artifact_digest, "inputs":{}}
	for path in ["res://dev/characters/character_walk_trial.gd", "res://dev/characters/character_walk_trial.tscn", "res://dev/characters/character_motion_review.gd", "res://dev/characters/character_motion_review.tscn", "res://tests/characters/test_character_motion_review_native.gd"]:
		report.inputs[path] = FileAccess.get_sha256(path)
	var file := FileAccess.open(evidence.path_join("metadata.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"  ")); file.close()
	trial.queue_free()
	finish()
