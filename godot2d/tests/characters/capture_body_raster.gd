extends SceneTree
## Static posed raster observer, not a player, motion clock or contact solver.
var evidence := ""
var repo := ProjectSettings.globalize_path("res://..").simplify_path()
var report := {"kind":"coastal-body-source-native-observation-v1","samples":[],"output_hashes":{},"checks":{}}
var pending := {}

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--evidence="): evidence=arg.trim_prefix("--evidence=")
	call_deferred("run")

func reject(message:String) -> void:
	push_error(message)
	quit(2)

func run() -> void:
	if not evidence.begins_with("/private/tmp/coastal-"): reject("Unmanaged evidence path");return
	var path=evidence.path_join("input-contract.json")
	var contract=JSON.parse_string(FileAccess.get_file_as_string(path))
	if not contract is Dictionary or contract.get("kind")!="coastal-body-source-native-input-v1" or contract.get("observer")!="source-poses":reject("Wrong body material contract");return
	var contents=DirAccess.get_files_at(evidence)
	if contents.size()!=1 or contents[0]!="input-contract.json" or not DirAccess.get_directories_at(evidence).is_empty():reject("Evidence output is not fresh");return
	if DisplayServer.get_name()=="headless":reject("Actual GPU required");return
	for file in contract.files:
		if FileAccess.get_sha256(repo.path_join(file))!=contract.files[file]:reject("Frozen capture input changed: "+file);return
	var trial=load("res://dev/characters/character_motion_lane.tscn").instantiate()
	trial.set_script(load("res://tests/characters/body_raster_fixture.gd"))
	root.add_child(trial)
	await process_frame
	trial.get_node("TrialUI").hide()
	trial.get_node("WorldCamera").zoom=Vector2.ONE*float(contract.camera_zoom)
	trial.actor.position=Vector2(1600,1600)
	trial.pose.centered=false
	var index=0
	for entry in contract.plan:
		var image=Image.load_from_file(repo.path_join(entry.file))
		image.convert(Image.FORMAT_RGBA8)
		var hash=HashingContext.new();hash.start(HashingContext.HASH_SHA256);hash.update(image.get_data())
		if image.get_size()!=Vector2i(entry.canvas_px[0],entry.canvas_px[1]) or hash.finish().hex_encode()!=entry.rgba_sha256:reject("Actual strict texture differs");return
		trial.pose.texture=ImageTexture.create_from_image(image)
		trial.pose.scale=Vector2.ONE*float(entry.display_scale)/float(contract.camera_zoom)
		trial.pose.offset=-Vector2(entry.root_anchor_px[0],entry.root_anchor_px[1])
		await process_frame
		await process_frame
		await RenderingServer.frame_post_draw
		var full=root.get_texture().get_image()
		var anchor=trial.actor.get_global_transform_with_canvas()*Vector2.ZERO
		var origin=Vector2i(anchor)-Vector2i(160,250)
		var box=Rect2i(origin,Vector2i(320,320))
		if not Rect2i(Vector2i.ZERO,full.get_size()).encloses(box):reject("Actual capture outside viewport");return
		var name="pose-%03d.png"%index
		pending[name]=full.get_region(box)
		var transform=trial.pose.get_global_transform_with_canvas()
		report.samples.append({"mode":"source-pose","capture":name,"world_state":{"action":entry.action,"direction":entry.direction},
			"texture":{"clip":entry.action+"-"+entry.direction,"pose_id":entry.pose_id,"rgba_sha256":entry.rgba_sha256},
			"render_source_to_screen":[transform.x.x,transform.x.y,transform.y.x,transform.y.y,transform.origin.x,transform.origin.y],
			"sprite_offset":[trial.pose.offset.x,trial.pose.offset.y],"texture_size_px":entry.canvas_px,
			"actor_capture_origin_px":[origin.x,origin.y],"physics_frame":Engine.get_physics_frames(),"process_frame":Engine.get_process_frames()})
		index+=1
	for file in contract.files:
		if FileAccess.get_sha256(repo.path_join(file))!=contract.files[file]:reject("Inputs changed during capture");return
	for name in pending:
		pending[name].save_png(evidence.path_join(name))
		report.output_hashes[name]=FileAccess.get_sha256(evidence.path_join(name))
	report.renderer=DisplayServer.get_name()
	report.input_contract_sha256=FileAccess.get_sha256(path)
	report.checks={"native_gpu":true,"frozen_inputs_unchanged":true,"all_planned_source_poses":report.samples.size()==contract.plan.size()}
	report.scope="Static source-pose raster correspondence only. No animation, real movement, stance, grip mechanics, soil target or release acceptance."
	var file=FileAccess.open(evidence.path_join("report.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"  "));file.close()
	trial.pose.texture=null
	trial.queue_free()
	pending.clear()
	await process_frame
	await process_frame
	print("BODY_RASTER actual GPU source poses=",index)
	quit()
