extends "res://tests/test_life_farming_native.gd"
var trial
var review
func click(button: Button) -> void:
	# Let native viewport hover settle before the press/release pair. A single
	# injected motion can be missed while the OS pointer is outside the window.
	for attempt in range(5):
		var point := button.get_global_transform_with_canvas() * (button.size / 2)
		var motion := InputEventMouseMotion.new()
		motion.position = point
		motion.global_position = point
		root.push_input(motion,true)
		for i in range(3): await process_frame
		if button.is_hovered(): break
	if not button.is_hovered():
		printerr("NATIVE_HOVER_FAILED ",button.get_path())
		return
	var point := button.get_global_transform_with_canvas() * (button.size / 2)
	for pressed in [true,false]:
		var event := InputEventMouseButton.new()
		event.position = point
		event.global_position = point
		event.button_index = MOUSE_BUTTON_LEFT
		event.button_mask = MOUSE_BUTTON_MASK_LEFT if pressed else 0
		event.pressed = pressed
		root.push_input(event,true)
		for i in range(2): await process_frame

func fits(control: Control) -> bool:
	var transform := control.get_global_transform_with_canvas()
	var a: Vector2 = transform * Vector2.ZERO
	var b: Vector2 = transform * control.size
	return a.x >= 0 and a.y >= 0 and b.x <= 2560 and b.y <= 1440
func run() -> void:
	evidence = "/private/tmp/coastal-hoe-v4-native"
	DirAccess.make_dir_recursive_absolute(evidence)
	trial = load("res://dev/character_walk_trial.tscn").instantiate()
	trial.art_root = ProjectSettings.globalize_path("res://../art/design/character-motion/adult-standard-v1/locomotion-v1")
	trial.run_candidate_root = ProjectSettings.globalize_path("res://../art/design/character-motion/adult-standard-v1/run-four-directions-v1")
	trial.run_diagnostics_enabled = true
	trial.review_enabled = true
	trial.farming_review_enabled = true
	trial.farming_review_action = "hoe"
	root.add_child(trial)
	for i in range(4): await process_frame
	review = trial.review_panel
	root.grab_focus()
	for i in range(4): await process_frame
	check("native_renderer", DisplayServer.get_name() != "headless")
	check("all_three_samples_loaded", review.farming_library != null and review.farming_library.clips.size() == 3)
	check("default_hoe_west_short_sleeve", review.visible and review.review_action == "hoe" and review.review_direction == "west" and trial.garment == "A")
	check("review_panel_fits", fits(review))
	check("top_controls_fit", fits(trial.get_node("TrialUI/Panel")))
	await click(review.play_button)
	check("mouse_pause", not review.playing)
	var position_before: Vector2 = trial.actor.position
	var phase_before: float = trial.phase_ms
	var counts := {"water":2,"hoe":4,"harvest":2}
	var actions := ["water","hoe","harvest"]
	for index in range(actions.size()):
		var action: String = actions[index]
		await click(review.action_buttons[index+3])
		check(action+"_mouse_selects", review.review_action == action)
		var clip: Dictionary = review.farming_library.clips[action]
		check(action+"_pose_count", clip.textures.size() == counts[action])
		check(action+"_actual_density_matches_idle", is_equal_approx(review.motion_view.get_global_transform_with_canvas().get_scale().x*2,review.reference_view.get_global_transform_with_canvas().get_scale().x))
		var sprite_end: Vector2 = review.motion_view.position + clip.canvas_px * review.motion_view.scale
		check(action+"_full_canvas_fits_slot", review.motion_view.position.x >= 0 and review.motion_view.position.y >= 0 and sprite_end.x <= review.motion_view.get_parent().size.x and sprite_end.y <= review.motion_view.get_parent().size.y)
		for pose in range(counts[action]):
			if pose > 0: await click(review.get_node("Margin/Rows/Playback/Next"))
			check(action+"_real_pose_"+str(pose), review.motion_view.texture == clip.textures[pose])
			await capture("%s-key-%d" % [action,pose])
		await click(review.play_button)
		var before: float = review.preview_phase_ms
		await create_timer(0.55).timeout
		check(action+"_playback_clock", review.playing and review.preview_phase_ms != before)
		await click(review.play_button)
		check(action+"_sample_note_fits", fits(review))
	await record_hoe_cycles()
	check("preview_does_not_change_world", trial.actor.position == position_before and trial.phase_ms == phase_before and trial.facing == "south")
	await click(review.direction_buttons[0])
	check("missing_farm_direction_explicit", review.motion_view.texture == null and review.message.text.contains("西"))
	await click(review.direction_buttons[1])
	await key(KEY_2,true);await key(KEY_2,false)
	check("missing_farm_long_sleeve_explicit", review.motion_view.texture == null and review.message.text.contains("短袖"))
	await capture("unsupported-long-sleeve")
	await key(KEY_1,true);await key(KEY_1,false)
	await click(review.action_buttons[1])
	check("walk_still_available_and_geometry_restored", review.review_action == "walk" and review.motion_view.texture != null and review.motion_view.scale == review.reference_view.scale and review.motion_view.position == review.reference_view.position)
	await capture("return-to-approved-walk")
	await key(KEY_C,true);await key(KEY_C,false)
	check("C_hides_expanded_panel", not review.visible)
	root.grab_focus()
	for i in range(4): await process_frame
	await key(KEY_A,true);await key(KEY_SHIFT,true)
	await create_timer(0.12).timeout
	check("world_run_not_replaced_by_farm_preview", trial.current_action == "run" and trial.facing == "west")
	await key(KEY_2,true);await key(KEY_2,false)
	check("world_running_wardrobe_preserved", trial.garment == "B" and trial.current_action == "run")
	await key(KEY_SHIFT,false);await key(KEY_A,false)
	for i in range(3): await physics_frame
	check("world_returns_idle", trial.current_action == "idle")
	var metadata := {"scope":"Existing farming key poses in inspection panel only; no gameplay transactions or full-action acceptance", "catalog_sha256":review.farming_library.catalog_sha256, "clips":{}, "inputs":{}}
	for action in actions:
		var clip: Dictionary = review.farming_library.clips[action]
		metadata.clips[action] = {"candidate_sha256":clip.candidate_sha256,"pose_ids":clip.pose_ids,"display_scale":clip.display_scale,"root_anchor_px":[clip.root_anchor_px.x,clip.root_anchor_px.y]}
	for path in ["res://dev/character_walk_trial.gd","res://dev/character_walk_trial.tscn","res://dev/character_motion_review.gd","res://dev/character_motion_review.tscn","res://dev/character_farming_review.gd","res://dev/farming_review_catalog.json","res://tests/test_character_farming_panel_native.gd"]:
		metadata.inputs[path] = FileAccess.get_sha256(path)
	var file := FileAccess.open(evidence.path_join("metadata.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(metadata,"  "));file.close()
	trial.queue_free()
	finish()

func record_hoe_cycles() -> void:
	review.select_clip("west","hoe")
	review.set_playing(true)
	var duration: float = review.preview_duration()
	var start := Time.get_ticks_msec()
	var last_phase: float = review.preview_phase_ms
	var unwrapped := 0.0
	var last_capture := -100
	var samples: Array = []
	var images: Array = []
	var seen := {}
	DirAccess.make_dir_recursive_absolute(evidence.path_join("hoe-sequence"))
	while unwrapped < duration * 10.0 and Time.get_ticks_msec()-start < duration * 20.0:
		await process_frame
		var phase: float = review.preview_phase_ms
		unwrapped += fposmod(phase-last_phase,duration)
		last_phase = phase
		var elapsed := Time.get_ticks_msec()-start
		var pose: int = review.current_pose_index()
		seen[pose] = true
		samples.append({"wall_ms":elapsed,"phase_ms":phase,"unwrapped_ms":unwrapped,"pose_index":pose})
		if elapsed-last_capture >= 90:
			RenderingServer.force_draw()
			var picture := root.get_texture().get_image()
			picture.resize(1280,720,Image.INTERPOLATE_NEAREST)
			var file := "hoe-sequence/%06d.png" % samples.size()
			images.append({"file":file,"image":picture})
			samples[-1].capture_file = file
			last_capture = elapsed
	review.set_playing(false)
	check("hoe_ten_native_cycles", unwrapped >= duration*10 and seen.size() == 4 and images.size() >= 40)
	for item in images: item.image.save_png(evidence.path_join(item.file))
	var file := FileAccess.open(evidence.path_join("hoe-sequence.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify({"cycle_ms":duration,"candidate_sha256":review.farming_library.clips.hoe.candidate_sha256,"catalog_sha256":review.farming_library.catalog_sha256,"samples":samples,"capture_px":[1280,720],"scope":"Actual native preview playback; visual acceptance and strict tool/contact trajectories pending"},"  "));file.close()
