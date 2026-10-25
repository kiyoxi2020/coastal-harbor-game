extends SceneTree
const Support = preload("res://tests/life_test_support.gd")
var s := Support.new()
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var trial = load("res://dev/character_walk_trial.tscn").instantiate()
	if not trial.has_method("load_run_candidate"):
		printerr("FAIL: existing trial needs explicit single-side run candidate loading")
		trial.free()
		quit(1)
		return
	trial.art_root = ProjectSettings.globalize_path("res://../art/design/character-motion/adult-standard-v1/locomotion-v1")
	root.add_child(trial)
	await process_frame
	trial.set_physics_process(false)
	var candidate := ProjectSettings.globalize_path("res://../art/design/character-motion/adult-standard-v1/run-west-proof-v1")
	s.check("approved_walk_loads", trial.load_error == "" and is_equal_approx(trial.walk_speed(), 54.0))
	var fixture := make_fixture(candidate)
	s.check("candidate_loads", trial.load_run_candidate(fixture))
	if not trial.clips.has("run"):
		printerr(trial.motion_error)
		quit(1)
		return
	trial.set_motion_direction("west")
	trial.current_action = "walk"
	for phase in [0.0, 40.0, 80.0, 159.0, 160.0, 240.0, 319.0]:
		trial.phase_ms = phase
		s.check("enter_run_" + str(phase), trial.set_locomotion_action("run"))
		s.check("run_phase_" + str(phase), is_equal_approx(trial.phase_ms / trial.clip_duration("run", "west"), phase / 320.0))
		s.check("run_texture_" + str(phase), trial.pose.texture == trial.frames.A[trial.current_frame()])
		s.check("return_walk_" + str(phase), trial.set_locomotion_action("walk") and is_equal_approx(trial.phase_ms, phase))
	var first_run: int = trial.clips.run.west[0]
	for i in range(4): trial.frame_metadata[first_run + i].duration_ms = [60, 100, 70, 90][i]
	trial.phase_ms = 120.0
	trial.set_locomotion_action("run")
	s.check("unequal_duration_maps_within_pose", is_equal_approx(trial.phase_ms, 110.0))
	trial.set_motion_direction("west")
	s.check("same_direction_preserves_run_phase", is_equal_approx(trial.phase_ms, 110.0))
	trial.set_locomotion_action("walk")
	s.check("unequal_duration_roundtrip", is_equal_approx(trial.phase_ms, 120.0))
	for i in range(4): trial.frame_metadata[first_run + i].duration_ms = 80
	trial.set_locomotion_action("run")
	s.check("run_speed_candidate", is_equal_approx(trial.locomotion_speed(), 81.0))
	var phase: float = trial.phase_ms
	trial.set_garment("B")
	s.check("unsupported_run_garment_rejected", trial.garment == "A" and trial.current_action == "run" and trial.phase_ms == phase and trial.motion_error != "")
	trial.set_locomotion_action("walk")
	trial.set_motion_direction("east")
	s.check("east_run_explicitly_rejected", not trial.set_locomotion_action("run") and trial.current_action == "walk")
	trial.set_motion_direction("west")
	trial.set_garment("B")
	s.check("long_sleeve_run_rejected", not trial.set_locomotion_action("run") and trial.current_action == "walk")
	trial.set_garment("A")
	trial.set_locomotion_action("run")
	trial.reset_position()
	s.check("reset_returns_idle", trial.current_action == "idle" and trial.phase_ms == 0.0)
	var manifest := JSON.parse_string(FileAccess.get_file_as_string(fixture.path_join("candidate.json"))) as Dictionary
	var recipes := {"A": [], "B": []}
	for entry in manifest.frames:
		recipes.A.append(entry.file)
		recipes.B.append(entry.file) # Synthetic duplicate is only a loader fixture.
	var garments := {"candidate_manifest_sha256": FileAccess.get_sha256(fixture.path_join("candidate.json")), "inputs": manifest.inputs, "recipes": recipes}
	write_json(fixture.path_join("run-garments.json"), garments)
	s.check("layered_candidate_loads", trial.load_run_candidate(fixture))
	trial.set_motion_direction("west")
	trial.set_garment("B")
	s.check("long_sleeve_run_supported", trial.set_locomotion_action("run"))
	trial.phase_ms = 159.0
	trial.refresh_pose()
	s.check("long_sleeve_uses_run_texture", trial.pose.texture == trial.frames.B[trial.current_frame()] and trial.frames.B.size() == 24)
	trial.set_garment("A")
	s.check("running_change_preserves_phase", trial.garment == "A" and trial.phase_ms == 159.0 and trial.current_action == "run")
	trial.set_garment("B")
	s.check("long_sleeve_returns_walk", trial.set_locomotion_action("walk") and trial.phase_ms == 159.0 and trial.pose.texture == trial.frames.B[trial.current_frame()])
	garments.recipes.B.pop_back()
	write_json(fixture.path_join("run-garments.json"), garments)
	s.check("partial_garment_rejected", not trial.load_run_candidate(fixture) and not trial.clips.has("run") and trial.frames.B.size() == 20)
	garments.recipes.B.append(manifest.frames[3].file)
	garments.candidate_manifest_sha256 = "stale"
	write_json(fixture.path_join("run-garments.json"), garments)
	s.check("stale_garment_rejected", not trial.load_run_candidate(fixture))
	garments.candidate_manifest_sha256 = FileAccess.get_sha256(fixture.path_join("candidate.json"))
	garments.inputs[manifest.frames[0].file] = "tampered"
	write_json(fixture.path_join("run-garments.json"), garments)
	s.check("changed_garment_dependency_rejected", not trial.load_run_candidate(fixture))
	s.check("invalid_candidate_rejected", not trial.load_run_candidate("/private/tmp/coastal-run-missing"))
	s.check("failed_reload_removes_stale_run", not trial.clips.has("run") and trial.frames.A.size() == 20)
	trial.queue_free()
	await process_frame
	print("RUN_CANDIDATE checks=", s.checks.size(), " passed=", s.passed())
	quit(0 if s.passed() else 1)

func write_json(path: String, data: Dictionary) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	file.store_string(JSON.stringify(data))
	file.close()

func make_fixture(source: String) -> String:
	var target := "/private/tmp/coastal-run-garment-fixture"
	DirAccess.make_dir_recursive_absolute(target)
	DirAccess.remove_absolute(target.path_join("run-garments.json"))
	var data := JSON.parse_string(FileAccess.get_file_as_string(source.path_join("candidate.json"))) as Dictionary
	for reference in data.inputs:
		DirAccess.make_dir_recursive_absolute(target.path_join(reference).get_base_dir())
		DirAccess.copy_absolute(source.path_join(reference), target.path_join(reference))
	DirAccess.copy_absolute(source.path_join("candidate.json"), target.path_join("candidate.json"))
	return target
