extends SceneTree
const Support = preload("res://tests/life_test_support.gd")
var s = Support.new()
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var project := ProjectSettings.globalize_path("res://..")
	var base := project.path_join("art/characters")
	var trial = load("res://dev/characters/character_walk_trial.tscn").instantiate()
	root.add_child(trial)
	trial.set_physics_process(false)
	s.check("new_locomotion_40_textures", trial.load_error == "" and trial.schema_version == 2 and trial.frames.get("A", []).size() == 20 and trial.frames.get("B", []).size() == 20)
	if trial.load_error != "": printerr("LOCOMOTION_ERROR ", trial.load_error)
	var run_loaded: bool = trial.load_run_candidate(base.path_join("builds/run-r001"))
	s.check("new_run_four_directions", run_loaded and trial.clips.get("run", {}).size() == 4)
	if not run_loaded: printerr("RUN_ERROR ", trial.motion_error)
	if run_loaded:
		s.check("new_diagnostics_load", trial.load_run_diagnostics(base.path_join("builds/run-r001")))
		if trial.motion_error != "": printerr("DIAGNOSTIC_ERROR ", trial.motion_error)
	var manifest_path := base.path_join("builds/locomotion-r001/manifest.json")
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
	var fixture := "/private/tmp/coastal-layout-actual-mutated"
	DirAccess.make_dir_recursive_absolute(fixture)
	for defect in ["root", "input_path", "frame_path", "source_hash", "frame_hash"]:
		var damaged: Dictionary = manifest.duplicate(true)
		match defect:
			"root": damaged.resource_root = "../art/characters"
			"input_path": damaged.inputs["../outside.json"] = "0".repeat(64)
			"frame_path": damaged.recipes.A.frames[0].file = "../outside.png"
			"source_hash": damaged.source_contract[damaged.source_contract.keys()[0]] = "0".repeat(64)
			"frame_hash": damaged.recipes.A.frames[0].sha256 = "0".repeat(64)
		preload("res://tests/characters/character_fixture_library.gd").save_json(fixture.path_join("manifest.json"), damaged)
		s.check("rooted_walk_reject_" + defect, not trial.load_art(fixture) and not trial.pose.visible)
	s.check("rooted_walk_recovers", trial.load_art(base.path_join("builds/locomotion-r001")))
	var farming = load("res://dev/characters/character_farming_review.gd").new()
	s.check("new_farming_24", farming.load_catalog(project, base.path_join("reviews/farming/catalog.json")) and farming.clips.size() == 24)
	if farming.error != "": printerr("FARMING_ERROR ", farming.error)
	var wardrobe = load("res://dev/characters/character_wardrobe_samples.gd").new()
	s.check("new_wardrobe_five", wardrobe.load_samples(project, base.path_join("reviews/wardrobe/catalog.json")) and wardrobe.samples.size() == 5)
	if wardrobe.error != "": printerr("WARDROBE_ERROR ", wardrobe.error)
	var headwear = load("res://dev/characters/character_headwear_samples.gd").new()
	s.check("new_headwear_four", headwear.load_samples(project, base.path_join("reviews/headwear/catalog.json")) and headwear.samples.size() == 4)
	if headwear.error != "": printerr("HEADWEAR_ERROR ", headwear.error)
	s.check("production_entry_preserved", ProjectSettings.get_setting("application/run/main_scene") == "res://scenes/harbor.tscn")
	trial.queue_free(); await process_frame
	print("CHARACTER_LAYOUT_ACTUAL checks=", s.checks.size(), " passed=", s.passed())
	quit(0 if s.passed() else 1)
