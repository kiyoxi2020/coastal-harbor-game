extends SceneTree
## Same-pose support-point drift relative to fixed ground; no art changes.
var trial
var samples: Array = []
var poses := {}
var output := "/private/tmp/coastal-contact-audit"
var started: int
func _initialize() -> void:
	call_deferred("run")
func run() -> void:
	var art := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--trial-art-root="): art = arg.trim_prefix("--trial-art-root=")
	if art.is_empty() or DisplayServer.get_name() == "headless": quit(1); return
	DirAccess.make_dir_recursive_absolute(output)
	var observations: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(art.path_join("poses.json")))
	for row in observations.frames: poses[row.pose_id] = row
	trial = load("res://dev/character_walk_trial.tscn").instantiate()
	trial.art_root = art
	root.add_child(trial)
	await process_frame
	if trial.load_error != "": printerr(trial.load_error); quit(1); return
	root.grab_focus()
	for i in range(8): await process_frame
	if not trial.focused: printerr("CONTACT_CAPTURE_NO_FOCUS"); quit(1); return
	started = Time.get_ticks_usec()
	var codes := {"west": KEY_A, "east": KEY_D, "north": KEY_W, "south": KEY_S}
	for direction in ["west", "east", "north", "south"]:
		trial.reset_position()
		if direction == "north": trial.actor.position = Vector2(600, 244)
		elif direction == "south": trial.actor.position = Vector2(296, 244)
		key(codes[direction], true)
		var begin := Time.get_ticks_usec()
		while Time.get_ticks_usec() - begin < 1400000:
			await process_frame
			await RenderingServer.frame_post_draw
			if not trial.focused: key(codes[direction], false); printerr("CONTACT_CAPTURE_LOST_FOCUS"); quit(1); return
			capture()
		key(codes[direction], false)
		for i in range(2): await physics_frame
	var record := {"artifact_digest":trial.artifact_digest,"manifest_sha256":FileAccess.get_sha256(art.path_join("baked/export-manifest.json")),"poses_sha256":FileAccess.get_sha256(art.path_join("poses.json")),"capture_script_sha256":FileAccess.get_sha256("res://tests/capture_character_contacts.gd"),"trial_script_sha256":FileAccess.get_sha256("res://dev/character_walk_trial.gd"),"scope":"actual movement; ground-relative same-pose support drift; anchors approximate; no full rig claim","samples":samples}
	var file := FileAccess.open(output.path_join("capture.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(record,"  ")); file.close()
	print("CONTACT_CAPTURE_OK ",samples.size())
	quit(0)
func key(code: int, pressed: bool) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.pressed = pressed
	Input.parse_input_event(event)
func capture() -> void:
	var pose_id: String = trial.frame_metadata[trial.current_frame()].pose_id
	var observation: Dictionary = poses[pose_id]
	var support := ""
	for side in ["left", "right"]:
		if observation.foot_contact_observation[side] == "support": support = side
	var anchor := Vector2(256,708)
	if not support.is_empty():
		var point: Array = observation.anchors[support+"_foot"].px
		anchor = Vector2(point[0],point[1])
	var foot: Vector2 = trial.pose.get_global_transform_with_canvas() * (anchor + trial.pose.offset)
	var ground: Vector2 = trial.get_node("HarborExterior").get_global_transform_with_canvas() * Vector2(296,244)
	var screenshot := root.get_texture().get_image()
	var center: Vector2 = trial.actor.get_global_transform_with_canvas().origin
	var rect := Rect2i(Vector2i(center)-Vector2i(180,200),Vector2i(360,260)).intersection(Rect2i(Vector2i.ZERO,screenshot.get_size()))
	var filename := "%04d.png" % samples.size()
	screenshot.get_region(rect).save_png(output.path_join(filename))
	samples.append({"file":filename,"png_sha256":FileAccess.get_sha256(output.path_join(filename)),"elapsed_ms":(Time.get_ticks_usec()-started)/1000.0,"pose_id":pose_id,"direction":trial.facing,"support":support,"phase_ms":trial.phase_ms,"world_position":[trial.actor.position.x,trial.actor.position.y],"foot_screen_px":[foot.x,foot.y],"ground_screen_px":[ground.x,ground.y],"crop_px":[rect.position.x,rect.position.y,rect.size.x,rect.size.y],"render_target_px":[screenshot.get_width(),screenshot.get_height()]})
