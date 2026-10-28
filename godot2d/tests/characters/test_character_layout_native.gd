extends SceneTree
## Native migration smoke test. Logical controls only; no OS input/user acceptance claim.
const Support = preload("res://tests/life_test_support.gd")
var s = Support.new()
var evidence := "/private/tmp/coastal-character-layout-native"
var trial
var review
var contract_sha256 := ""
var started_utc := ""
var outputs := {}
var subjects := {}
var timing := []
var project := ""

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--evidence="): evidence = argument.trim_prefix("--evidence=")
	call_deferred("run")

func check(id: String, passed: bool) -> void:
	s.check(id, passed)

func json_file(path: String, value: Variant) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	file.store_string(JSON.stringify(value, "  ")); file.close()

func bind_file(path: String) -> void:
	var canonical := path.simplify_path()
	check("subject_exists_" + canonical, FileAccess.file_exists(canonical))
	if FileAccess.file_exists(canonical): subjects[canonical] = FileAccess.get_sha256(canonical)

func sample_subject(sample: Dictionary) -> void:
	bind_file(sample.sample_path)
	check("loaded_sha_" + sample.id, subjects.get(sample.sample_path.simplify_path()) == sample.sample_sha256)

func crop(control: Control) -> Image:
	await process_frame
	await RenderingServer.frame_post_draw
	var transform := control.get_global_transform_with_canvas()
	var rect := Rect2i(Vector2i(transform * Vector2.ZERO), Vector2i(transform.get_scale() * control.size))
	return root.get_texture().get_image().get_region(rect)

func save_image(name: String, image: Image) -> void:
	var relative := "boards/" + name + ".png"
	check("capture_" + name, image.save_png(evidence.path_join(relative)) == OK)
	outputs[relative] = FileAccess.get_sha256(evidence.path_join(relative))

func inspect_clip(id: String, count: int = 4, include_idle: bool = false) -> void:
	review.set_playing(false); review.preview_phase_ms = 0; review.refresh_preview()
	var slot: Control = review.motion_view.get_parent()
	var images: Array[Image] = []
	if include_idle: images.append(await crop(review.reference_view.get_parent()))
	for index in range(count):
		check(id + "_pose_" + str(index), review.current_pose_index() == index and review.motion_view.texture != null)
		images.append(await crop(slot))
		review.step_frame()
	var board := Image.create(images[0].get_width() * images.size(), images[0].get_height(), false, Image.FORMAT_RGBA8)
	for index in range(images.size()): board.blit_rect(images[index], Rect2i(Vector2i.ZERO, images[index].get_size()), Vector2i(index * images[0].get_width(), 0))
	save_image(id, board)
	review.preview_phase_ms = 0; review.set_playing(true)
	var duration: float = review.preview_duration()
	var elapsed := 0.0
	var last := 0.0
	var seen := {}
	var start := Time.get_ticks_msec()
	while elapsed < duration and Time.get_ticks_msec() - start < 12000:
		await process_frame
		trial.focused = true
		var phase: float = review.preview_phase_ms
		elapsed += fposmod(phase - last, duration); last = phase
		seen[review.current_pose_index()] = true
		timing.append({"clip": id, "wall_ms": Time.get_ticks_msec(), "phase_ms": phase, "phase_f64_le": PackedFloat64Array([phase]).to_byte_array().hex_encode(), "unwrapped_ms": elapsed, "unwrapped_f64_le": PackedFloat64Array([elapsed]).to_byte_array().hex_encode(), "pose": review.current_pose_index()})
	review.set_playing(false)
	check(id + "_native_cycle", elapsed >= duration and seen.size() == count)

func inspect_world(sample: Dictionary, state: String) -> void:
	var action: String = sample.data.action_id
	var direction: String = sample.data.direction
	var id: String = "world-" + sample.id + "-" + state
	trial.reset_position(); trial.facing = direction; trial.focused = true
	trial.set_physics_process(true)
	var position_before: Vector2 = trial.actor.position
	var seen := {}
	if action == "run": Input.action_press("trial_walk_" + direction)
	else: check(id + "_starts", trial.start_farming_sample(action))
	var start := Time.get_ticks_msec()
	var limit: int = 1100 if action == "run" else int(review.preview_duration()) + 300
	var switched := false
	while Time.get_ticks_msec() - start < limit:
		await physics_frame
		trial.focused = true
		var index: int = -1
		if action == "run" and trial.current_action == "run": index = trial.clips.run[direction].find(trial.current_frame())
		elif not trial.farming_clip.is_empty(): index = trial.farming_pose_index()
		if index >= 0:
			var observed_phase: float = trial.phase_ms if action == "run" else trial.farming_elapsed_ms
			timing.append({"clip": id, "wall_ms": Time.get_ticks_msec(), "phase_ms": observed_phase, "phase_f64_le": PackedFloat64Array([observed_phase]).to_byte_array().hex_encode(), "pose": index})
			check(id + "_texture_" + str(index), trial.pose.texture == sample.textures_by_state[state][index])
			if not seen.has(index):
				RenderingServer.force_draw()
				var origin: Vector2 = trial.actor.get_global_transform_with_canvas() * Vector2.ZERO
				var screen: Image = root.get_texture().get_image()
				var rect := Rect2i(Vector2i(origin) - Vector2i(150,270), Vector2i(300,320)).intersection(Rect2i(Vector2i.ZERO, screen.get_size()))
				save_image(id + "-pose-" + str(index), screen.get_region(rect))
				seen[index] = true
			if not switched:
				var phase: float = trial.phase_ms
				var tool_phase: float = trial.farming_elapsed_ms
				trial.select_head_state("bare" if state != "bare" else "hair_hat"); trial.select_head_state(state)
				check(id + "_switch_keeps_clock", trial.phase_ms == phase and trial.farming_elapsed_ms == tool_phase)
				switched = true
	if action == "run": Input.action_release("trial_walk_" + direction)
	await physics_frame; await physics_frame
	check(id + "_all_four_poses", seen.size() == 4)
	check(id + "_motion_policy", trial.actor.position.distance_to(position_before) > 10 if action == "run" else trial.actor.position == position_before)
	check(id + "_matching_idle", trial.current_action == "idle" and trial.pose.texture == sample.idle_by_state[state])
	trial.set_physics_process(false)

func run() -> void:
	if not evidence.begins_with("/private/tmp/coastal-") or ".." in evidence.split("/"): quit(2); return
	var contract := evidence.path_join("input-contract.json")
	if not FileAccess.file_exists(contract): printerr("pre-capture input contract required"); quit(2); return
	contract_sha256 = FileAccess.get_sha256(contract)
	started_utc = Time.get_datetime_string_from_system(true)
	project = ProjectSettings.globalize_path("res://..").simplify_path()
	DirAccess.make_dir_recursive_absolute(evidence.path_join("boards"))
	check("real_gpu", DisplayServer.get_name() != "headless")
	if not s.passed(): finish(); return
	for relative in ["builds/locomotion-r001/manifest.json", "builds/run-r001/candidate.json", "builds/run-r001/run-garments.json", "builds/run-r001/run-diagnostics.json", "reviews/farming/catalog.json", "reviews/wardrobe/catalog.json", "reviews/headwear/catalog.json"]:
		bind_file(project.path_join("art/characters").path_join(relative))
	for script in ["res://tests/characters/test_character_layout_native.gd", "res://dev/characters/character_resource_paths.gd", "res://dev/characters/character_walk_trial.gd", "res://dev/characters/character_farming_review.gd", "res://dev/characters/character_wardrobe_samples.gd", "res://dev/characters/character_headwear_samples.gd"]: bind_file(script)
	trial = load("res://dev/characters/character_walk_trial.tscn").instantiate()
	trial.run_candidate_root = project.path_join("art/characters/builds/run-r001")
	trial.run_diagnostics_enabled = true; trial.review_enabled = true; trial.farming_review_enabled = true; trial.farming_transitions_enabled = true
	root.add_child(trial); review = trial.review_panel
	trial.set_physics_process(false); trial.focused = true
	check("locomotion_run_loaded", trial.load_error == "" and trial.motion_error == "" and trial.clips.has("run"))
	check("farming_24_loaded", review.farming_library != null and review.farming_library.clips.size() == 24)
	if not s.passed(): finish(); return
	var farming_catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(trial.farming_catalog_path))
	for record in farming_catalog.clips: bind_file(project.path_join(record.candidate))
	for garment in ["A", "B"]:
		trial.set_garment(garment)
		for action in ["walk", "run", "hoe", "water", "harvest"]:
			for direction in trial.DIRECTIONS:
				review.select_clip(direction, action)
				await inspect_clip("baseline-" + action + "-" + direction + "-" + garment)
	trial.queue_free(); await process_frame
	trial = load("res://dev/characters/character_wardrobe_trial.tscn").instantiate(); root.add_child(trial); review = trial.review_panel
	trial.set_physics_process(false); trial.focused = true
	check("wardrobe_five_loaded", trial.sample_error == "" and trial.sample_library.samples.size() == 5)
	if not s.passed(): finish(); return
	for sample in trial.sample_library.samples:
		sample_subject(sample); trial.select_sample(sample.id)
		await inspect_clip("wardrobe-" + sample.id, 4, true)
	trial.queue_free(); await process_frame
	trial = load("res://dev/characters/character_headwear_trial.tscn").instantiate(); root.add_child(trial); review = trial.review_panel
	trial.set_physics_process(false); trial.focused = true
	check("headwear_four_loaded", trial.head_ready and trial.head_error == "" and trial.head_library.samples.size() == 4)
	if not s.passed(): finish(); return
	for sample in trial.head_library.samples:
		sample_subject(sample)
		bind_file(project.path_join(sample.data.parent_sample))
		trial.select_sample(sample.id)
		for state in trial.HeadLibrary.STATES:
			check("head_control_" + sample.id + "-" + state, trial.select_head_state(state))
			await inspect_clip("headwear-" + sample.id + "-" + state, 4, true)
			await inspect_world(sample, state)
			if sample.id == "hoe-west":
				var backdrops: Array[ColorRect] = []
				for slot in [review.motion_view.get_parent(), review.reference_view.get_parent()]:
					var backdrop := ColorRect.new()
					backdrop.color = Color("e8e0ce"); backdrop.size = slot.size; backdrop.mouse_filter = Control.MOUSE_FILTER_IGNORE
					slot.add_child(backdrop); slot.move_child(backdrop, 0); backdrops.append(backdrop)
				await inspect_clip("headwear-" + sample.id + "-" + state + "-light", 4, true)
				for backdrop in backdrops: backdrop.queue_free()
				await process_frame
	finish()

func finish() -> void:
	check("input_contract_unchanged", FileAccess.get_sha256(evidence.path_join("input-contract.json")) == contract_sha256)
	for path in subjects: check("subject_unchanged_" + path, FileAccess.get_sha256(path) == subjects[path])
	var report := {"scope": "New rooted catalogs: 40 locomotion/farming clips, five wardrobe samples, four headwear samples/four states. Native GPU stopped-frame boards and one timed preview cycle each, plus headwear world run/tool one-shots and live state switches preserving clocks. Logical control handlers; no OS input, export, or user visual acceptance claim.", "timing_precision": "ieee754-f64-le", "input_contract_sha256": contract_sha256, "started_utc": started_utc, "finished_utc": Time.get_datetime_string_from_system(true), "renderer": DisplayServer.get_name(), "subjects": subjects, "checks": s.checks, "timing": timing, "output_hashes": outputs}
	json_file(evidence.path_join("report.json"), report)
	print("CHARACTER_LAYOUT_NATIVE checks=", s.checks.size(), " passed=", s.passed(), " boards=", outputs.size(), " timing=", timing.size())
	quit(0 if s.passed() else 1)
