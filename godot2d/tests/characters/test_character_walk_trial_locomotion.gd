extends SceneTree
const Support = preload("res://tests/life_test_support.gd")
var s := Support.new()
var fixture_root := "/private/tmp/coastal-locomotion-fixture"
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var trial = load("res://dev/characters/character_walk_trial.tscn").instantiate()
	if not trial.has_method("set_motion_direction"):
		printerr("FAIL: trial must support schema2 direction changes and same-facing idle")
		trial.free()
		quit(1)
		return
	preload("res://tests/characters/character_fixture_library.gd").locomotion(fixture_root)
	trial.art_root = fixture_root
	root.add_child(trial)
	await process_frame
	if trial.load_error != "":
		printerr("FAIL fixture load: ", trial.load_error)
		quit(1)
		return
	s.check("schema2_twenty_frames", trial.frames.A.size() == 20 and trial.schema_version == 2)
	s.check("default_idle", trial.current_action == "idle" and trial.facing == "south")
	s.check("default_accepted_speed", is_equal_approx(trial.walk_speed(), 54.0))
	s.check("production_entry_preserved", ProjectSettings.get_setting("application/run/main_scene") == "res://scenes/harbor.tscn")
	trial.phase_ms = 177.0
	trial.current_action = "walk"
	trial.refresh_pose()
	var phase: float = trial.phase_ms
	trial.set_motion_direction("east")
	s.check("turn_keeps_walk_phase", trial.phase_ms == phase and trial.current_frame() == 14)
	trial.set_garment("B")
	s.check("clothes_keep_phase_and_direction", trial.phase_ms == phase and trial.facing == "east" and trial.pose.texture == trial.frames.B[14])
	s.check("no_mirroring", not trial.pose.flip_h and not trial.pose.flip_v)
	var original_metadata: Array = trial.frame_metadata.duplicate(true)
	for i in range(4): trial.frame_metadata[12 + i]["duration_ms"] = [60, 90, 120, 180][i]
	trial.set_motion_direction("west")
	trial.phase_ms = 176.0
	trial.set_motion_direction("east")
	s.check("unequal_cycles_keep_normalized_phase", is_equal_approx(trial.phase_ms, 247.5))
	trial.phase_ms = 4500.0 + 200.0
	s.check("uneven_low_rate_jump", trial.current_frame() == 14)
	trial.frame_metadata = original_metadata
	trial.reset_position()
	var start: Vector2 = trial.actor.position
	Input.action_press("trial_walk_east")
	Input.action_press("trial_walk_south")
	var direction: Vector2 = trial.movement_input()
	s.check("diagonal_normalized", is_equal_approx(direction.length(), 1.0) and direction.x > 0 and direction.y > 0)
	for i in range(12): await physics_frame
	Input.action_release("trial_walk_east")
	Input.action_release("trial_walk_south")
	for i in range(2): await physics_frame
	var travel: Vector2 = trial.actor.position - start
	s.check("diagonal_moves_both_axes", travel.x > 2 and travel.y > 2)
	s.check("released_same_facing_idle", trial.current_action == "idle" and trial.facing == "south" and trial.current_frame() == 0)
	var stopped: float = trial.phase_ms
	for i in range(4): await physics_frame
	s.check("idle_does_not_advance_walk", trial.phase_ms == stopped)
	for direction_name in ["west", "east", "north", "south"]:
		trial.reset_position()
		Input.action_press("trial_walk_" + direction_name)
		for i in range(6): await physics_frame
		Input.action_release("trial_walk_" + direction_name)
		for i in range(2): await physics_frame
		s.check("idle_faces_" + direction_name, trial.current_action == "idle" and trial.facing == direction_name)
	trial.actor.position = Vector2(30, 244)
	Input.action_press("trial_walk_west")
	for i in range(60): await physics_frame
	var blocked_point: Vector2 = trial.actor.position
	var blocked_phase: float = trial.phase_ms
	for i in range(5): await physics_frame
	Input.action_release("trial_walk_west")
	s.check("collision_preserved", blocked_point.x > 20 and trial.actor.position.is_equal_approx(blocked_point))
	s.check("blocked_does_not_advance_walk", trial.phase_ms == blocked_phase and trial.current_action == "idle")
	trial.reset_position()
	s.check("reset_zero_phase", trial.phase_ms == 0.0)
	var original: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(fixture_root.path_join("baked/export-manifest.json")))
	var bad_root := "/private/tmp/coastal-locomotion-invalid"
	DirAccess.make_dir_recursive_absolute(bad_root.path_join("baked"))
	original.actions.walk.directions.erase("north")
	var file := FileAccess.open(bad_root.path_join("baked/export-manifest.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(original)); file.close()
	s.check("missing_direction_rejected_no_fallback", not trial.load_art(bad_root) and trial.load_error != "" and not trial.pose.visible)
	s.check("recover_fixture", trial.load_art(fixture_root))
	var fixture_manifest := fixture_root.path_join("baked/export-manifest.json")
	var original_text := FileAccess.get_file_as_string(fixture_manifest)
	for case_name in ["mapped_duration", "texture_hash", "actual_dependency_hash"]:
		var damaged: Dictionary = JSON.parse_string(original_text)
		if case_name == "mapped_duration": damaged.recipes.B.frames[0].duration_ms = 0
		elif case_name == "texture_hash": damaged.recipes.A.frames[0].sha256 = "0".repeat(64)
		else:
			damaged.source_contract["source-contract.json"] = "0".repeat(64)
			damaged.inputs["source-contract.json"].sha256 = "0".repeat(64)
		file = FileAccess.open(fixture_manifest, FileAccess.WRITE)
		file.store_string(JSON.stringify(damaged)); file.close()
		s.check("reject_" + case_name, not trial.load_art(fixture_root) and trial.load_error != "" and not trial.pose.visible)
		file = FileAccess.open(fixture_manifest, FileAccess.WRITE)
		file.store_string(original_text); file.close()
		s.check("restore_after_" + case_name, trial.load_art(fixture_root))
	trial.queue_free()
	await process_frame
	print("LOCOMOTION_TRIAL checks=", s.checks.size(), " passed=", s.passed())
	quit(0 if s.passed() else 1)
