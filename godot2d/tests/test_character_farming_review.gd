extends SceneTree
const Support = preload("res://tests/life_test_support.gd")
var s := Support.new()
const LOADER := "res://dev/character_farming_review.gd"
const CATALOG := "res://dev/farming_review_catalog.json"
const FIXTURE := "/private/tmp/coastal-farming-loader-fixture"
var project_root := ""
var original_catalog: Dictionary
var originals := {}

func _initialize() -> void: call_deferred("run")

func write_json(path: String, value: Variant) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	file.store_string(JSON.stringify(value))
	file.close()

func reset_fixture() -> Dictionary:
	var catalog: Dictionary = original_catalog.duplicate(true)
	for record in catalog.clips:
		var path := FIXTURE.path_join(record.candidate)
		write_json(path, originals[record.action_id])
		record.sha256 = FileAccess.get_sha256(path)
	write_json(FIXTURE.path_join("catalog.json"), catalog)
	return catalog

func candidate_path(catalog: Dictionary, index: int) -> String:
	return FIXTURE.path_join(catalog.clips[index].candidate)

func save_mutation(catalog: Dictionary, data: Dictionary, index: int = 0) -> void:
	var path := candidate_path(catalog, index)
	write_json(path, data)
	catalog.clips[index].sha256 = FileAccess.get_sha256(path)
	write_json(FIXTURE.path_join("catalog.json"), catalog)

func rejected(loader, name: String) -> void:
	var ok: bool = loader.load_catalog(FIXTURE, FIXTURE.path_join("catalog.json"))
	s.check(name, not ok and loader.clips.is_empty() and not loader.error.is_empty() and loader.catalog_sha256.is_empty())

func run() -> void:
	s.check("farming_loader_exists", ResourceLoader.exists(LOADER))
	s.check("pinned_catalog_exists", FileAccess.file_exists(CATALOG))
	if not s.passed():
		print("FARMING_REVIEW RED: loader/catalog feature missing")
		quit(1)
		return
	var loader = load(LOADER).new()
	project_root = ProjectSettings.globalize_path("res://..").simplify_path()
	s.check("real_pinned_candidates_load", loader.load_catalog(project_root))
	if loader.clips.size() != 3:
		printerr(loader.error)
		quit(1)
		return
	s.check("success_digest_and_error", loader.catalog_sha256 == FileAccess.get_sha256(CATALOG) and loader.error.is_empty())
	for action in ["water", "hoe", "harvest"]:
		var clip: Dictionary = loader.get_clip(action, "west", "A")
		var expected_count := 4 if action == "hoe" else 2
		s.check(action + "_only_existing_keyposes", clip.textures.size() == expected_count and clip.pose_ids.size() == expected_count and clip.durations_ms.size() == expected_count)
		s.check(action + "_source_contract", clip.action_id == action and clip.direction == "west" and clip.garment == "A" and clip.canvas_px.x == 1536 and clip.root_anchor_px == (Vector2(768,1544) if action == "hoe" else Vector2(768,1480)) and is_equal_approx(clip.display_scale,138.0/1164.0))
		s.check(action + "_real_textures_and_integer_timing", clip.textures.all(func(texture): return texture is Texture2D and texture.get_size() == clip.canvas_px) and clip.durations_ms.all(func(duration): return duration is int and duration > 0))
		s.check(action + "_proof_disclosure", not clip.note.is_empty() and clip.note.contains("关键姿态") and not clip.source_status.is_empty() and clip.candidate_sha256.length() == 64)
	s.check("unsupported_combinations_have_no_fallback", loader.get_clip("water","north","A").is_empty() and loader.get_clip("water","west","B").is_empty() and loader.get_clip("run","west","A").is_empty())
	original_catalog = JSON.parse_string(FileAccess.get_file_as_string(CATALOG))
	DirAccess.make_dir_recursive_absolute(FIXTURE)
	for record in original_catalog.clips:
		var original_path: String = project_root.path_join(record.candidate)
		var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(original_path))
		originals[record.action_id] = data
		var references: Array = data.inputs.keys()
		for frame in data.frames: references.append(frame.file)
		for reference in references:
			var destination: String = FIXTURE.path_join(record.candidate.get_base_dir()).path_join(reference)
			DirAccess.make_dir_recursive_absolute(destination.get_base_dir())
			DirAccess.copy_absolute(original_path.get_base_dir().path_join(reference), destination)
	var catalog := reset_fixture()
	s.check("isolated_real_fixture_loads", loader.load_catalog(FIXTURE,FIXTURE.path_join("catalog.json")))
	catalog.clips[2].sha256 = "0".repeat(64)
	write_json(FIXTURE.path_join("catalog.json"),catalog)
	rejected(loader,"third_candidate_failure_clears_previous_success_atomically")
	catalog = reset_fixture()
	catalog.clips[0].candidate = "../outside/candidate.json"
	write_json(FIXTURE.path_join("catalog.json"),catalog)
	rejected(loader,"catalog_candidate_traversal_rejected")
	catalog = reset_fixture()
	var data: Dictionary = originals.water.duplicate(true)
	data.inputs["../outside.txt"] = "0".repeat(64)
	save_mutation(catalog,data)
	rejected(loader,"input_traversal_rejected")
	catalog = reset_fixture(); data = originals.water.duplicate(true)
	data.inputs["references\\escape.txt"] = "0".repeat(64)
	save_mutation(catalog,data)
	rejected(loader,"input_backslash_rejected")
	catalog = reset_fixture(); data = originals.water.duplicate(true)
	data.inputs[data.inputs.keys()[0]] = "0".repeat(64)
	save_mutation(catalog,data)
	rejected(loader,"actual_input_hash_mismatch_rejected")
	catalog = reset_fixture(); data = originals.water.duplicate(true)
	data.frames[0].file = "/private/tmp/outside.png"
	save_mutation(catalog,data)
	rejected(loader,"absolute_texture_path_rejected")
	catalog = reset_fixture(); data = originals.water.duplicate(true)
	data.frames[0].sha256 = "0".repeat(64)
	save_mutation(catalog,data)
	rejected(loader,"actual_texture_hash_mismatch_rejected")
	catalog = reset_fixture(); data = originals.water.duplicate(true)
	data.canvas_px[0] = 1535
	save_mutation(catalog,data)
	rejected(loader,"actual_texture_canvas_mismatch_rejected")
	for value in [0, -1, 1.5, "500"]:
		catalog = reset_fixture(); data = originals.water.duplicate(true)
		data.frames[0].duration_ms = value
		save_mutation(catalog,data)
		rejected(loader,"invalid_duration_rejected_" + str(value))
	for field in ["template_id","action_id","direction","source_density_scale_vs_idle","display_scale"]:
		catalog = reset_fixture(); data = originals.water.duplicate(true)
		data[field] = {"template_id":"other","action_id":"hoe","direction":"east","source_density_scale_vs_idle":1,"display_scale":138.0/582.0}[field]
		save_mutation(catalog,data)
		rejected(loader,"contract_field_rejected_" + field)
	catalog = reset_fixture(); data = originals.water.duplicate(true)
	data.root_anchor_px = [768,1664]
	save_mutation(catalog,data)
	rejected(loader,"root_outside_canvas_rejected")
	catalog = reset_fixture(); data = originals.water.duplicate(true)
	data.canvas_px = [-1536,1664]
	save_mutation(catalog,data)
	rejected(loader,"invalid_canvas_rejected")
	catalog = reset_fixture(); data = originals.water.duplicate(true)
	data.frames[1].pose_id = data.frames[0].pose_id
	save_mutation(catalog,data)
	rejected(loader,"duplicate_pose_rejected")
	catalog = reset_fixture()
	catalog.clips[2].action_id = "water"
	write_json(FIXTURE.path_join("catalog.json"),catalog)
	rejected(loader,"duplicate_catalog_action_rejected")
	catalog = reset_fixture(); data = originals.water.duplicate(true)
	data.frames[0].erase("sha256")
	save_mutation(catalog,data)
	rejected(loader,"missing_texture_hash_rejected")
	catalog = reset_fixture(); data = originals.water.duplicate(true)
	data.frames[0].source_sha256 = "0".repeat(64)
	save_mutation(catalog,data)
	rejected(loader,"frame_source_dependency_mismatch_rejected")
	catalog = reset_fixture()
	write_json(FIXTURE.path_join("catalog.json"),[])
	rejected(loader,"non_dictionary_catalog_rejected")
	reset_fixture()
	s.check("valid_reload_recovers_after_failure", loader.load_catalog(FIXTURE,FIXTURE.path_join("catalog.json")) and loader.error.is_empty() and loader.clips.size() == 3)
	print("FARMING_REVIEW checks=",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
