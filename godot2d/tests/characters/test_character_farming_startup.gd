extends SceneTree
const Support = preload("res://tests/life_test_support.gd")
var s := Support.new()
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var trial = load("res://dev/characters/character_walk_trial.tscn").instantiate()
	s.check("initial_farming_action_can_be_selected", trial.has_method("set_initial_farming_action"))
	if not trial.has_method("set_initial_farming_action"):
		trial.free();quit(1);return
	s.check("original_default_water", trial.farming_review_action == "water")
	s.check("hoe_default_selected", trial.set_initial_farming_action("hoe"))
	s.check("unknown_default_rejected", not trial.set_initial_farming_action("unknown") and trial.farming_review_action == "hoe")
	trial.art_root = ProjectSettings.globalize_path("res://../art/characters/builds/locomotion-r001")
	trial.run_candidate_root = ProjectSettings.globalize_path("res://../art/characters/builds/run-r001")
	trial.run_diagnostics_enabled = true
	trial.farming_review_enabled = true
	trial.review_enabled = true
	root.add_child(trial)
	await process_frame
	trial.set_physics_process(false)
	s.check("startup_actually_shows_hoe", trial.review_panel.visible and trial.review_panel.review_action == "hoe" and trial.review_panel.review_direction == "west" and trial.garment == "A" and trial.review_panel.motion_view.texture != null)
	s.check("world_stays_idle", trial.current_action == "idle" and trial.facing == "south")
	trial.queue_free();await process_frame
	print("FARMING_STARTUP checks=",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
