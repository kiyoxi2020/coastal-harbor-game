extends SceneTree
const Support = preload("res://tests/life_test_support.gd")
var s := Support.new()
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var trial = load("res://dev/character_walk_trial.tscn").instantiate()
	trial.art_root = ProjectSettings.globalize_path("res://../art/design/character-motion/adult-standard-v1/locomotion-v1")
	root.add_child(trial)
	await process_frame
	trial.set_physics_process(false)
	var review = trial.get_node_or_null("TrialUI/MotionReview")
	s.check("comparison_panel_exists", review != null)
	if review == null:
		trial.queue_free()
		quit(1)
		return
	s.check("real_run_loads", trial.load_run_candidate(ProjectSettings.globalize_path("res://../art/design/character-motion/adult-standard-v1/run-four-directions-v1")))
	review.bind_trial(trial)
	review.show()
	review.set_process(false)
	s.check("default_south_run", review.review_direction == "south" and review.review_action == "run")
	var position_before: Vector2 = trial.actor.position
	var phase_before: float = trial.phase_ms
	for direction in ["south", "west", "east", "north"]:
		for action in ["idle", "walk", "run"]:
			review.select_clip(direction, action)
			var frame: int = trial.clips[action][direction][0]
			s.check(direction + action + "_uses_actual_texture", review.motion_view.texture == trial.frames.A[frame])
			s.check(direction + action + "_same_garment_idle", review.reference_view.texture == trial.frames.A[trial.clips.idle[direction][0]])
	review.select_clip("south", "run")
	review.advance_preview(0.12)
	s.check("timed_preview_advances", review.current_pose_index() == 1)
	review.set_playing(false)
	var frozen: float = review.preview_phase_ms
	review.advance_preview(1.0)
	s.check("pause_freezes_preview", review.preview_phase_ms == frozen)
	review.step_frame()
	s.check("step_advances_while_paused", review.current_pose_index() == 2 and not review.playing)
	review.step_frame(); review.step_frame()
	s.check("step_wraps", review.current_pose_index() == 0)
	trial.set_garment("B")
	review.refresh_preview()
	s.check("missing_north_south_B_has_explicit_message", review.motion_view.texture == null and review.message.text.contains("未提供"))
	s.check("approved_B_reference_remains", review.reference_view.texture == trial.frames.B[trial.clips.idle.south[0]])
	review.select_clip("east", "run")
	s.check("east_B_available", review.motion_view.texture == trial.frames.B[trial.clips.run.east[0]])
	s.check("same_display_dimensions", review.reference_view.scale == review.motion_view.scale and is_equal_approx(review.motion_view.scale.x, 138.0 / 582.0))
	s.check("preview_does_not_move_or_rephase_actor", trial.actor.position == position_before and trial.phase_ms == phase_before and trial.current_action == "idle" and trial.facing == "south")
	var selectors: Array = review.direction_buttons + review.action_buttons
	s.check("selectors_do_not_capture_world_arrow_keys", selectors.all(func(button): return button.focus_mode == Control.FOCUS_NONE))
	trial.queue_free()
	await process_frame
	print("MOTION_REVIEW checks=", s.checks.size(), " passed=", s.passed())
	quit(0 if s.passed() else 1)
