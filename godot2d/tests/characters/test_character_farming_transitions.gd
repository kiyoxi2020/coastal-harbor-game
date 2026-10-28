extends SceneTree
const Support = preload("res://tests/life_test_support.gd")
var s := Support.new()
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var fixture := preload("res://tests/characters/character_fixture_library.gd").farming_schema1("/private/tmp/coastal-layout-schema1-adapter")
	var trial = load("res://dev/characters/character_walk_trial.tscn").instantiate()
	trial.art_root = ProjectSettings.globalize_path("res://../art/characters/builds/locomotion-r001")
	trial.run_candidate_root = ProjectSettings.globalize_path("res://../art/characters/builds/run-r001")
	root.add_child(trial)
	await process_frame
	trial.set_physics_process(false)
	s.check("world_farming_entry_exists", trial.has_method("start_farming_sample"))
	if not trial.has_method("start_farming_sample"):
		trial.queue_free(); quit(1); return
	trial.review_panel.load_farming_samples(fixture,fixture.path_join("catalog.json"))
	trial.set_motion_direction("west")
	s.check("explicit_opt_in_required", not trial.start_farming_sample("hoe"))
	trial.farming_transitions_enabled = true
	var scale_before: Vector2 = trial.pose.scale
	var offset_before: Vector2 = trial.pose.offset
	for action in ["water", "hoe", "harvest"]:
		trial.set_garment("A")
		trial.set_motion_direction("west")
		trial.current_action = "run"
		var position_before: Vector2 = trial.actor.position
		var clip: Dictionary = trial.review_panel.farming_library.get_clip(action,"west","A")
		s.check(action+"_enters_from_run", trial.start_farming_sample(action) and trial.current_action == action)
		s.check(action+"_real_texture_and_density", trial.pose.texture == clip.textures[0] and trial.pose.scale.is_equal_approx(scale_before/2.0) and trial.pose.offset == -clip.root_anchor_px)
		s.check(action+"_no_reentry", not trial.start_farming_sample("hoe"))
		s.check(action+"_locomotion_locked", not trial.set_locomotion_action("walk") and trial.current_action == action)
		s.check(action+"_direction_locked", not trial.set_motion_direction("east") and trial.facing == "west")
		trial.set_garment("B")
		s.check(action+"_wardrobe_deferred", trial.garment == "A")
		Input.action_press("trial_walk_east")
		trial._physics_process(float(clip.durations_ms[0]-1)/1000.0)
		s.check(action+"_movement_locked", trial.actor.position == position_before and trial.actor.velocity == Vector2.ZERO)
		s.check(action+"_first_boundary", trial.pose.texture == clip.textures[0])
		trial._physics_process(0.002)
		s.check(action+"_second_pose", trial.pose.texture == clip.textures[1])
		var elapsed: float = trial.farming_elapsed_ms
		trial.focused = false
		trial._physics_process(1.0)
		s.check(action+"_focus_pause", trial.farming_elapsed_ms == elapsed)
		trial.focused = true
		trial._physics_process(10.0)
		s.check(action+"_complete_idle", trial.current_action == "idle" and trial.facing == "west" and trial.actor.position == position_before)
		s.check(action+"_wardrobe_atomic_after_end", trial.garment == "B" and trial.pose.texture == trial.frames.B[trial.clips.idle.west[0]])
		s.check(action+"_geometry_restored", trial.pose.scale == scale_before and trial.pose.offset == offset_before)
		trial._physics_process(0.02)
		s.check(action+"_movement_resumes_next_tick", trial.actor.position.x > position_before.x and trial.facing == "east")
		Input.action_release("trial_walk_east")
	trial.set_garment("A"); trial.set_motion_direction("north")
	s.check("missing_direction_rejected", not trial.start_farming_sample("hoe") and trial.current_action in ["walk","idle"])
	trial.set_motion_direction("west");trial.set_garment("B")
	s.check("missing_garment_rejected", not trial.start_farming_sample("hoe"))
	trial.set_garment("A")
	s.check("unknown_action_rejected", not trial.start_farming_sample("dig"))
	trial.start_farming_sample("hoe");trial.set_garment("B");trial.reset_position()
	s.check("reset_cancels_and_restores", trial.farming_clip.is_empty() and trial.current_action == "idle" and trial.pose.scale == scale_before and trial.garment == "A")
	trial.queue_free();await process_frame
	print("FARMING_TRANSITIONS checks=",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
