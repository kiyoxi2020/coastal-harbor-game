extends "res://tests/test_character_farming_catalog_v2.gd"
func run() -> void:
	make_fixture()
	var trial = load("res://dev/character_walk_trial.tscn").instantiate()
	s.check("catalog_selection_property_exists", "farming_catalog_path" in trial)
	if not s.passed():trial.free();quit(1);return
	trial.art_root = ProjectSettings.globalize_path("res://../art/design/character-motion/adult-standard-v1/locomotion-v1")
	trial.run_candidate_root = ProjectSettings.globalize_path("res://../art/design/character-motion/adult-standard-v1/run-four-directions-v1")
	trial.farming_review_enabled=true;trial.farming_transitions_enabled=true
	trial.farming_catalog_path=ROOT.path_join("catalog.json")
	# Fixture catalog paths are relative to fixture root; explicit loading tests the UI adapter.
	root.add_child(trial);await process_frame;trial.set_physics_process(false)
	s.check("panel_explicit_catalog_load",trial.review_panel.load_farming_samples(ROOT,ROOT.path_join("catalog.json")))
	for record in catalog.clips:
		trial.set_motion_direction(record.direction);trial.set_garment(record.garment)
		var clip: Dictionary = trial.review_panel.farming_library.get_clip(record.action_id,record.direction,record.garment)
		trial.review_panel.select_clip(record.direction,record.action_id)
		var id: String = record.action_id+record.direction+record.garment
		s.check(id+"_panel_real_texture",trial.review_panel.motion_view.texture==clip.textures[0])
		s.check(id+"_world_start",trial.start_farming_sample(record.action_id))
		trial._physics_process(0.201)
		s.check(id+"_world_second_pose",trial.pose.texture==clip.textures[1] and trial.facing==record.direction and trial.garment==record.garment)
		s.check(id+"_status_actual_direction",trial.status.text.contains(record.direction))
		trial._physics_process(2.0)
		s.check(id+"_idle_restored",trial.current_action=="idle" and trial.farming_clip.is_empty())
	trial.queue_free();await process_frame
	print("FARMING_TRIAL_V2 checks=",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
