extends "res://tests/test_life_farming_native.gd"
var trial
var samples: Array = []
var images: Array = []
var focus_recoveries := 0
func regain_focus() -> void:
	root.grab_focus()
	for i in range(4): await process_frame
func run() -> void:
	evidence = "/private/tmp/coastal-farming-transitions-native-final"
	DirAccess.make_dir_recursive_absolute(evidence.path_join("sequence"))
	trial = load("res://dev/character_walk_trial.tscn").instantiate()
	trial.art_root = ProjectSettings.globalize_path("res://../art/design/character-motion/adult-standard-v1/locomotion-v1")
	trial.run_candidate_root = ProjectSettings.globalize_path("res://../art/design/character-motion/adult-standard-v1/run-four-directions-v1")
	trial.farming_review_enabled = true
	trial.farming_transitions_enabled = true
	root.add_child(trial)
	root.grab_focus()
	for i in range(8): await process_frame
	check("native_renderer", DisplayServer.get_name() != "headless")
	check("catalog_loaded", trial.review_panel.farming_library.clips.size() == 3)
	# Hide inspector panel through the same C control available to the user.
	if trial.review_panel.visible:
		await key(KEY_C,true);await key(KEY_C,false)
	await key(KEY_A,true);await key(KEY_SHIFT,true)
	await create_timer(0.12).timeout
	check("real_run_before_action",trial.current_action == "run" and trial.facing == "west")
	await key(KEY_G,true);await key(KEY_G,false)
	check("key_enters_hoe_from_run",trial.current_action == "hoe")
	var locked: Vector2 = trial.actor.position
	await key(KEY_A,false);await key(KEY_SHIFT,false)
	await key(KEY_D,true)
	await key(KEY_2,true);await key(KEY_2,false)
	check("real_direction_and_wardrobe_locked",trial.facing == "west" and trial.garment == "A")
	await capture("hoe-world-locked")
	var lock_deadline := Time.get_ticks_msec()+4000
	while not trial.farming_clip.is_empty() and Time.get_ticks_msec() < lock_deadline:
		samples.append({"phase":"locked","action":trial.current_action,"elapsed_ms":trial.farming_elapsed_ms,"position":[trial.actor.position.x,trial.actor.position.y],"locked":trial.actor.position == locked,"focused":trial.focused})
		await process_frame
	check("locked_position_throughout",samples.all(func(row): return row.locked))
	await key(KEY_D,false)
	check("queued_wardrobe_applied",trial.garment == "B")
	await create_timer(0.08).timeout
	check("released_idle_after_action",trial.current_action == "idle")
	await capture("returned-idle-long-sleeve")
	await key(KEY_A,true);await create_timer(0.05).timeout;await key(KEY_A,false)
	await key(KEY_1,true);await key(KEY_1,false)
	var original_scale: Vector2 = trial.pose.scale
	for action in ["water","hoe","harvest"]:
		var code: int = {"water":KEY_F,"hoe":KEY_G,"harvest":KEY_H}[action]
		var seen := {}
		var last_capture := -100
		for cycle in range(10):
			await regain_focus()
			await key(code,true);await key(code,false)
			check(action+"_key_enters_"+str(cycle),trial.current_action == action)
			var before: Vector2 = trial.actor.position
			var started := Time.get_ticks_msec()
			while not trial.farming_clip.is_empty() and Time.get_ticks_msec()-started < 6000:
				if not trial.focused:
					focus_recoveries += 1
					await regain_focus()
				var index: int = trial.farming_pose_index()
				seen[index] = true
				var row := {"action":action,"cycle":cycle,"wall_ms":Time.get_ticks_msec(),"elapsed_ms":trial.farming_elapsed_ms,"pose":index,"locked":trial.actor.position == before,"focused":trial.focused}
				if Time.get_ticks_msec()-last_capture >= 150:
					RenderingServer.force_draw()
					var picture := root.get_texture().get_image()
					picture.resize(1280,720,Image.INTERPOLATE_NEAREST)
					var path := "sequence/%s-%02d-%04d.png" % [action,cycle,samples.size()]
					images.append({"file":path,"image":picture})
					row.capture = path
					last_capture = Time.get_ticks_msec()
				samples.append(row)
				await process_frame
			check(action+"_completed_idle_"+str(cycle),trial.farming_clip.is_empty() and trial.current_action == "idle" and trial.actor.position == before and trial.pose.scale == original_scale)
			if not trial.farming_clip.is_empty():
				printerr("FOCUS_DIAGNOSTIC ",trial.focused," elapsed_ms=",trial.farming_elapsed_ms)
				trial.reset_position()
		check(action+"_all_poses_rendered",seen.size() == trial.review_panel.farming_library.clips[action].textures.size())
		await capture(action+"-returned-idle")
	# Rejection through real controls, without turning or swapping silently.
	await key(KEY_2,true);await key(KEY_2,false)
	await key(KEY_G,true);await key(KEY_G,false)
	check("unsupported_B_key_rejected",trial.farming_clip.is_empty() and trial.garment == "B" and trial.motion_error != "")
	await capture("unsupported-long-sleeve")
	var metadata := {"scope":"Isolated world actor key-pose transitions; hard cuts, no gameplay transactions, no user visual acceptance", "samples":samples,"captures":images.size(),"focus_recoveries":focus_recoveries,"inputs":{},"clips":{},"checks":support.checks}
	for path in ["res://dev/character_walk_trial.gd","res://dev/character_walk_trial.tscn","res://dev/character_farming_review.gd","res://dev/farming_review_catalog.json","res://tests/test_character_farming_transitions_native.gd"]:
		metadata.inputs[path] = FileAccess.get_sha256(path)
	for action in ["water","hoe","harvest"]:
		var clip: Dictionary = trial.review_panel.farming_library.clips[action]
		metadata.clips[action] = {"candidate_sha256":clip.candidate_sha256,"poses":clip.pose_ids,"durations_ms":clip.durations_ms}
	for item in images: item.image.save_png(evidence.path_join(item.file))
	var file := FileAccess.open(evidence.path_join("report.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(metadata,"  "));file.close()
	trial.queue_free()
	finish()
