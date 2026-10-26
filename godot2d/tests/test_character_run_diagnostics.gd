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
	var base := ProjectSettings.globalize_path("res://../art/design/character-motion/adult-standard-v1/run-four-directions-v1")
	s.check("regular_candidate_loads", trial.load_run_candidate(base))
	s.check("regular_loader_keeps_B_diagnostics_disabled", not trial.has_motion_garment("run","south","B") and not trial.has_motion_garment("run","north","B"))
	s.check("diagnostic_loader_exists", trial.has_method("load_run_diagnostics"))
	if not trial.has_method("load_run_diagnostics"):
		trial.queue_free();quit(1);return
	var west = trial.frames.B[trial.clips.run.west[0]]
	s.check("explicit_diagnostics_load", trial.load_run_diagnostics(base))
	trial.review_panel.bind_trial(trial)
	trial.review_panel.set_process(false)
	trial.set_garment("B")
	for direction in ["south","north"]:
		trial.set_locomotion_action("walk")
		trial.set_motion_direction(direction)
		s.check(direction+"_world_run_available", trial.set_locomotion_action("run"))
		s.check(direction+"_world_marked_diagnostic", trial.diagnostic_note("run",direction,"B") != "" and trial.status.text.contains("诊断稿"))
		trial.review_panel.select_clip(direction,"run")
		s.check(direction+"_preview_real_diagnostic", trial.review_panel.motion_view.texture == trial.frames.B[trial.clips.run[direction][0]] and trial.review_panel.message.text.contains("诊断稿"))
		trial.review_panel.step_frame()
		s.check(direction+"_diagnostic_can_step", trial.review_panel.current_pose_index() == 1)
	s.check("accepted_west_not_overwritten", trial.frames.B[trial.clips.run.west[0]] == west and trial.diagnostic_note("run","west","B") == "")
	s.check("walk_not_marked_diagnostic", trial.diagnostic_note("walk","north","B") == "")
	var fixture := "/private/tmp/coastal-run-diagnostic-fixture"
	DirAccess.make_dir_recursive_absolute(fixture)
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(base.path_join("run-diagnostics.json")))
	for reference in data.inputs:
		DirAccess.make_dir_recursive_absolute(fixture.path_join(reference).get_base_dir())
		DirAccess.copy_absolute(base.path_join(reference),fixture.path_join(reference))
	data.inputs[data.records[0].frames[0].file] = "changed"
	var file := FileAccess.open(fixture.path_join("run-diagnostics.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(data));file.close()
	s.check("stale_diagnostics_rejected", not trial.load_run_diagnostics(fixture))
	s.check("failed_reload_revokes_only_diagnostics", not trial.has_motion_garment("run","north","B") and not trial.has_motion_garment("run","south","B") and trial.has_motion_garment("run","west","B") and trial.current_action == "idle")
	s.check("diagnostics_recover", trial.load_run_diagnostics(base))
	s.check("regular_reload_discards_diagnostics", trial.load_run_candidate(base) and not trial.has_motion_garment("run","south","B"))
	trial.queue_free()
	await process_frame
	print("RUN_DIAGNOSTICS checks=",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
