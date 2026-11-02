extends SceneTree
const Support = preload("res://tests/life_test_support.gd")
var s = Support.new()
func _initialize() -> void:
	call_deferred("run")
func save(path: String, value: Variant) -> void:
	var file = FileAccess.open(path, FileAccess.WRITE)
	file.store_string(JSON.stringify(value)); file.close()
func publish(project: String, suite_path: String, recipe: Dictionary, manifest: Dictionary, suite: Dictionary) -> void:
	var library = project.path_join("art/characters")
	var recipe_path = library.path_join(manifest.recipe)
	save(recipe_path, recipe)
	manifest.inputs[manifest.recipe] = FileAccess.get_sha256(recipe_path)
	var helper = load("res://dev/characters/character_construction_samples.gd").new()
	manifest.artifact_digest = helper.bytes_hash(JSON.stringify({"inputs": manifest.inputs, "engine": manifest.engine}, "", true).to_utf8_buffer())
	var manifest_path = library.path_join(suite.manifest.file)
	save(manifest_path, manifest)
	suite.manifest.sha256 = FileAccess.get_sha256(manifest_path)
	save(suite_path, suite)

func rejection_checks(project: String, suite_path: String, loader) -> void:
	var library = project.path_join("art/characters")
	var suite = JSON.parse_string(FileAccess.get_file_as_string(suite_path))
	var manifest = JSON.parse_string(FileAccess.get_file_as_string(library.path_join(suite.manifest.file)))
	var recipe = JSON.parse_string(FileAccess.get_file_as_string(library.path_join(manifest.recipe)))
	var original_manifest = FileAccess.get_file_as_bytes(library.path_join(suite.manifest.file))
	var original_recipe = FileAccess.get_file_as_bytes(library.path_join(manifest.recipe))
	for defect in ["run", "duplicate", "time", "malformed_action", "malformed_frame", "malformed_clips", "source_pose", "source_annotation", "source_closure", "output_rgba"]:
		var changed_recipe = recipe.duplicate(true)
		var changed_manifest = manifest.duplicate(true)
		var changed_suite = suite.duplicate(true)
		var image_path = ""; var image_bytes = PackedByteArray()
		var annotation_path = ""; var annotation_bytes = PackedByteArray()
		if defect == "run": changed_recipe.required_capabilities[1].action_id = "run"
		if defect == "duplicate": changed_recipe.clips.append(changed_recipe.clips[1].duplicate(true)); changed_recipe.required_capabilities.append(changed_recipe.required_capabilities[1].duplicate(true))
		if defect == "time": changed_recipe.clips[1].frames[0].duration_ms += 1
		if defect == "malformed_action": changed_recipe.clips[1].action = 4
		if defect == "malformed_frame": changed_recipe.clips[1].frames[0] = 4
		if defect == "malformed_clips": changed_recipe.clips = null
		if defect == "source_pose": changed_recipe.clips[1].frames[0].layers[1].source = changed_recipe.clips[0].frames[0].layers[1].source
		if defect == "source_annotation":
			var adaptation_ref = changed_recipe.adaptations.top
			annotation_path = library.path_join(adaptation_ref.file)
			annotation_bytes = FileAccess.get_file_as_bytes(annotation_path)
			var adaptation = JSON.parse_string(FileAccess.get_file_as_string(annotation_path))
			adaptation.views[1].source_pose.record = "idle_east_0"
			save(annotation_path, adaptation)
			adaptation_ref.sha256 = FileAccess.get_sha256(annotation_path)
			changed_manifest.inputs[adaptation_ref.file] = adaptation_ref.sha256
		if defect == "source_closure": changed_manifest.inputs.erase("sources/prepared/textures/walk_east_1.png"); changed_recipe.authoring_inputs = changed_recipe.authoring_inputs.filter(func(ref): return ref.file != "sources/prepared/textures/walk_east_1.png")
		if defect == "output_rgba":
			image_path = library.path_join(suite.manifest.file.get_base_dir()).path_join(changed_manifest.outputs[0].file)
			image_bytes = FileAccess.get_file_as_bytes(image_path)
			var image = Image.create(2, 2, false, Image.FORMAT_RGBA8); image.fill(Color.GREEN); image.save_png(image_path)
			changed_manifest.outputs[0].sha256 = FileAccess.get_sha256(image_path)
		publish(project, suite_path, changed_recipe, changed_manifest, changed_suite)
		s.check(defect + "_rejected", not loader.load_samples(project, suite_path) and loader.error != "")
		s.check(defect + "_no_stale_state", loader.frames.is_empty() and loader.clips.is_empty() and loader.frame_metadata.is_empty() and loader.geometry.is_empty() and loader.runtime.is_empty() and loader.prepared_frames.is_empty() and loader.artifact_digest == "")
		if annotation_path != "":
			var file = FileAccess.open(annotation_path, FileAccess.WRITE); file.store_buffer(annotation_bytes); file.close()
		if image_path != "":
			var file = FileAccess.open(image_path, FileAccess.WRITE); file.store_buffer(image_bytes); file.close()
		publish(project, suite_path, recipe.duplicate(true), manifest.duplicate(true), suite.duplicate(true))
		s.check(defect + "_reload", loader.load_samples(project, suite_path))
	for defect in ["no_prepared", "duplicate_prepared", "scope", "unknown_key", "manifest_sha"]:
		var bad = suite.duplicate(true)
		if defect == "no_prepared": bad.prepared_sources = []
		if defect == "duplicate_prepared": bad.prepared_sources.append(bad.prepared_sources[0].duplicate(true))
		if defect == "scope": bad.scope = "production"
		if defect == "unknown_key": bad.extra = true
		if defect == "manifest_sha": bad.manifest.sha256 = "0".repeat(64)
		save(suite_path, bad)
		s.check(defect + "_rejected", not loader.load_samples(project, suite_path) and loader.error != "")
	var restore = FileAccess.open(library.path_join(manifest.recipe), FileAccess.WRITE); restore.store_buffer(original_recipe); restore.close()
	restore = FileAccess.open(library.path_join(suite.manifest.file), FileAccess.WRITE); restore.store_buffer(original_manifest); restore.close()
	save(suite_path, suite)
	s.check("rejection_suite_restored", loader.load_samples(project, suite_path))

func actual_checks() -> void:
	var project = ProjectSettings.globalize_path("res://..").simplify_path()
	var suite_path = project.path_join("art/characters/reviews/registered/review.json")
	if not FileAccess.file_exists(suite_path): return
	var loader = load("res://dev/characters/character_registered_samples.gd").new()
	s.check("actual_registered_suite_loads", loader.load_samples(project, suite_path))
	if loader.error != "": print("ACTUAL_REGISTERED_ERROR ", loader.error); return
	s.check("actual_six_walk_plus_real_idle", loader.frames.A.size() == 7 and loader.clips.walk.west.size() == 6 and loader.clips.idle.west.size() == 1)
	var library = project.path_join("art/characters")
	var suite = loader.helper.read_json(suite_path)
	var manifest = loader.helper.read_json(library.path_join(suite.manifest.file))
	var recipe = loader.helper.read_json(library.path_join(manifest.recipe))
	var index = 0
	for clip in recipe.clips:
		for frame in clip.frames:
			var body = Image.new(); body.load(library.path_join(frame.layers[0].texture.file))
			var output = Image.new(); output.load(library.path_join(suite.manifest.file.get_base_dir()).path_join(manifest.outputs[index].file))
			s.check("actual_" + frame.pose_id + "_canonical_rgba", loader.frames.A[index].get_image().get_data() == body.get_data())
			s.check("actual_" + frame.pose_id + "_strict_rgba_and_clock", loader.frames.B[index].get_image().get_data() == output.get_data() and loader.frame_metadata[index].duration_ms == frame.duration_ms)
			index += 1

func run() -> void:
	s.check("registered_loader_exists", FileAccess.file_exists("res://dev/characters/character_registered_samples.gd"))
	if not s.passed(): quit(1); return
	var project := ""
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--fixture-project="): project = argument.trim_prefix("--fixture-project=")
	s.check("temporary_fixture_only", project.begins_with("/private/tmp/coastal-"))
	if not s.passed(): quit(1); return
	var suite_path = project.path_join("art/characters/reviews/registered/review.json")
	var loader = load("res://dev/characters/character_registered_samples.gd").new()
	s.check("real_strict_prepared_fixture_loads", loader.load_samples(project, suite_path))
	if not s.passed(): print("REGISTERED_LOAD_ERROR ", loader.error); quit(1); return
	s.check("body_and_strict_comparison", loader.frames.keys() == ["A", "B"] and loader.frames.A.size() == 3 and loader.frames.B.size() == 3)
	s.check("generic_east_two_frame_walk", loader.clips.walk.east.size() == 2 and loader.clips.idle.east.size() == 1)
	s.check("actual_nonuniform_frame_clock", loader.frame_metadata[loader.clips.walk.east[0]].duration_ms == 70 and loader.frame_metadata[loader.clips.walk.east[1]].duration_ms == 90)
	s.check("synthetic_canonical_rgba_exact", loader.frames.A[0].get_image().get_data().slice(0, 4) == PackedByteArray([30, 40, 50, 255]))
	s.check("synthetic_strict_alpha_over_rgba_exact", loader.frames.B[0].get_image().get_data().slice(0, 4) == PackedByteArray([120, 30, 40, 255]))
	var original = JSON.parse_string(FileAccess.get_file_as_string(suite_path))
	var bad = original.duplicate(true); bad.runtime.speed_factor = true; save(suite_path, bad)
	s.check("malformed_runtime_clears_every_state", not loader.load_samples(project, suite_path) and loader.frames.is_empty() and loader.clips.is_empty() and loader.frame_metadata.is_empty() and loader.geometry.is_empty() and loader.runtime.is_empty())
	s.check("failure_has_error", loader.error != "")
	save(suite_path, original)
	s.check("reload_after_failure", loader.load_samples(project, suite_path))
	rejection_checks(project, suite_path, loader)
	if not s.passed(): quit(1); return
	var trial = load("res://dev/characters/character_registered_trial.tscn").instantiate()
	trial.registered_project_override = project
	trial.registered_suite_override = suite_path
	root.add_child(trial); trial.set_physics_process(false)
	s.check("thin_trial_loads", trial.load_error == "" and trial.schema_version == 2 and trial.current_action == "idle" and trial.garment == "B")
	s.check("whole_frame_geometry", trial.pose.scale == Vector2(.25, .25) and trial.pose.offset == Vector2(-1, -1))
	s.check("unsupported_direction_button_disabled", trial.review_panel.direction_buttons[1].disabled and not trial.review_panel.direction_buttons[2].disabled)
	s.check("run_and_farming_disabled", trial.review_panel.action_buttons[2].disabled and trial.review_panel.action_buttons[3].disabled)
	trial.review_panel.select_clip("east", "walk")
	trial.review_panel.set_playing(false)
	s.check("panel_reuses_actual_metadata", trial.review_panel.preview_available() and trial.review_panel.preview_durations() == [70.0, 90.0])
	trial.review_panel.step_frame()
	s.check("panel_existing_step_clock", trial.review_panel.current_pose_index() == 1)
	Input.action_press("trial_walk_west")
	s.check("unsupported_world_direction_filtered", trial.movement_input() == Vector2.ZERO)
	Input.action_release("trial_walk_west")
	await physics_frame
	Input.action_press("trial_walk_east")
	var before = trial.actor.position
	trial._physics_process(.05)
	Input.action_release("trial_walk_east")
	s.check("inherited_world_controller_walks", trial.actor.position.x > before.x and trial.current_action == "walk" and trial.phase_ms > 0)
	trial._physics_process(.05)
	s.check("release_uses_actual_matching_idle", trial.current_action == "idle" and trial.pose.texture == trial.frames.B[trial.clips.idle.east[0]])
	trial.set_garment("A")
	s.check("comparison_is_canonical_body", trial.pose.texture == loader.frames.A[loader.clips.idle.east[0]] or trial.pose.texture.get_image().get_data() == loader.frames.A[loader.clips.idle.east[0]].get_image().get_data())
	trial.review_panel.set_playing(true)
	trial.review_panel.hide()
	s.check("trial_failure_clears_texture", not trial.load_registered(project, "/private/tmp/coastal-missing-review.json") and trial.frames.is_empty() and trial.clips.is_empty() and trial.pose.texture == null)
	s.check("trial_failure_disables_controls", trial.review_panel.direction_buttons.all(func(button): return button.disabled) and trial.review_panel.action_buttons.all(func(button): return button.disabled))
	s.check("hidden_trial_failure_clears_both_previews_immediately", trial.review_panel.reference_view.texture == null and trial.review_panel.motion_view.texture == null)
	s.check("hidden_trial_failure_stops_preview", not trial.review_panel.playing and trial.review_panel.preview_phase_ms == 0)
	await process_frame
	await process_frame
	s.check("hidden_trial_failure_remains_clear", trial.review_panel.reference_view.texture == null and trial.review_panel.motion_view.texture == null)
	trial.queue_free()
	actual_checks()
	print("REGISTERED_REVIEW checks=", s.checks.size(), " passed=", s.passed())
	quit(0 if s.passed() else 1)
