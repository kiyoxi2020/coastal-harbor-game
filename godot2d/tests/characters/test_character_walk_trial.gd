extends SceneTree
const Support = preload("res://tests/life_test_support.gd")
var s := Support.new()
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var path := "res://dev/characters/character_walk_trial.tscn"
	s.check("trial_scene_exists", ResourceLoader.exists(path))
	if not ResourceLoader.exists(path):
		print("WALK_TRIAL checks=", s.checks.size(), " passed=false")
		quit(1)
		return
	var trial = load(path).instantiate()
	trial.art_root = preload("res://tests/characters/character_fixture_library.gd").locomotion("/private/tmp/coastal-layout-west-fixture", true)
	root.add_child(trial)
	await process_frame
	s.check("art_loaded", trial.load_error == "" and trial.frames.size() == 2)
	if trial.load_error != "":
		print("ART_LOAD_FAILURE: ", trial.load_error, " path=", trial.art_root)
		quit(1)
		return
	s.check("real_harbor_scene", trial.get_node("HarborExterior").scene_file_path == "res://scenes/world/harbor_exterior.tscn")
	s.check("production_entry_unchanged", ProjectSettings.get_setting("application/run/main_scene") == "res://scenes/harbor.tscn")
	s.check("foot_collision_preserved", trial.actor.get_node("CollisionShape2D").shape.size == Vector2(10, 6))
	s.check("default_slower_speed", is_equal_approx(trial.walk_speed(), 54.0))
	s.check("default_slower_frame", is_equal_approx(trial.frame_duration_ms(), 80.0 / 0.75))
	s.check("scale_camera_once", trial.pose.scale.is_equal_approx(Vector2.ONE * 138.0 / 582.0 / 4.0))
	s.check("no_fake_direction", not trial.pose.flip_h)
	trial.phase_ms = 177.0
	trial.refresh_pose()
	var phase: float = trial.phase_ms
	trial.set_garment("B")
	s.check("clothes_keep_phase", trial.phase_ms == phase and trial.garment == "B" and trial.pose.texture == trial.frames.B[2])
	trial.set_speed_factor(0.5)
	s.check("speed_and_clock_scale_together", trial.walk_speed() == 36.0 and trial.frame_duration_ms() == 160.0)
	trial.set_speed_factor(1.0)
	s.check("original_speed_available", trial.walk_speed() == 72.0 and trial.frame_duration_ms() == 80.0)
	trial.set_speed_factor(4.0)
	s.check("speed_clamped", trial.speed_factor == 1.0)
	trial.reset_position()
	var start: Vector2 = trial.actor.position
	Input.action_press("trial_walk_west")
	for i in range(12): await physics_frame
	Input.action_release("trial_walk_west")
	for i in range(2): await physics_frame
	s.check("west_moves_in_world", trial.actor.position.x < start.x - 5.0 and is_equal_approx(trial.actor.position.y, start.y))
	var stopped_phase: float = trial.phase_ms
	for i in range(4): await physics_frame
	s.check("stopped_holds_frame", trial.phase_ms == stopped_phase and trial.actor.velocity == Vector2.ZERO)
	trial.actor.position = Vector2(30, 244)
	Input.action_press("trial_walk_west")
	for i in range(60): await physics_frame
	Input.action_release("trial_walk_west")
	s.check("real_boundary_blocks", trial.actor.position.x > 20 and trial.actor.get_slide_collision_count() > 0)
	var blocked_phase: float = trial.phase_ms
	var blocked_point: Vector2 = trial.actor.position
	for i in range(3): await physics_frame
	if trial.phase_ms != blocked_phase: print("BLOCK_DIAGNOSTIC ", blocked_phase, " -> ", trial.phase_ms, " point ", blocked_point, " -> ", trial.actor.position)
	s.check("blocked_animation_stops", trial.phase_ms == blocked_phase)
	trial.reset_position()
	s.check("explicit_reset", trial.actor.position == start and trial.phase_ms == 0.0)
	var good_path: String = trial.art_root
	s.check("missing_art_rejected", not trial.load_art("/private/tmp/coastal-missing-art") and trial.load_error != "")
	var tampered := "/private/tmp/coastal-trial-tampered"
	DirAccess.make_dir_recursive_absolute(tampered.path_join("baked"))
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(good_path.path_join("baked/export-manifest.json")))
	data.recipes.A.frames[0].sha256 = "0000"
	var file := FileAccess.open(tampered.path_join("baked/export-manifest.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(data))
	file.close()
	DirAccess.copy_absolute(good_path.path_join("baked/A_0.png"), tampered.path_join("baked/A_0.png"))
	s.check("altered_hash_rejected", not trial.load_art(tampered) and trial.load_error.contains("哈希") and not trial.pose.visible)
	s.check("recover_valid_art", trial.load_art(good_path))
	trial.queue_free()
	await process_frame
	print("WALK_TRIAL checks=", s.checks.size(), " passed=", s.passed())
	quit(0 if s.passed() else 1)
