extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
var s:=Support.new()
var trial
var review
var evidence:="/private/tmp/coastal-farming24-native"
var samples: Array=[]
var captures: Array=[]
var input_contract_sha256:=""
var started_utc:=""
func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--evidence="):evidence=argument.trim_prefix("--evidence=")
	call_deferred("run")
func check(id:String,ok:bool) -> void:s.check(id,ok)
func save_json(path:String,value) -> void:
	var file:=FileAccess.open(path,FileAccess.WRITE);file.store_string(JSON.stringify(value,"  "));file.close()
func key(code:int,pressed:bool) -> void:
	var event:=InputEventKey.new();event.physical_keycode=code;event.pressed=pressed;Input.parse_input_event(event)
	for i in range(2):await process_frame
func focus() -> void:
	root.grab_focus()
	for i in range(4):await process_frame
func click(button:Button) -> void:
	for attempt in range(5):
		var motion:=InputEventMouseMotion.new();motion.position=button.get_global_transform_with_canvas()*(button.size/2);motion.global_position=motion.position;root.push_input(motion,true)
		for i in range(3):await process_frame
		if button.is_hovered():break
	if not button.is_hovered():check("hover_"+str(button.get_path()),false);return
	for pressed in [true,false]:
		var event:=InputEventMouseButton.new();event.position=button.get_global_transform_with_canvas()*(button.size/2);event.global_position=event.position;event.button_index=MOUSE_BUTTON_LEFT;event.button_mask=MOUSE_BUTTON_MASK_LEFT if pressed else 0;event.pressed=pressed;root.push_input(event,true)
		for i in range(2):await process_frame
func fits(control:Control) -> bool:
	var transform:=control.get_global_transform_with_canvas();var a:Vector2=transform*Vector2.ZERO;var b:Vector2=transform*control.size
	return a.x>=0 and a.y>=0 and b.x<=2560.1 and b.y<=1440.1
func canvas_fits() -> bool:
	var clip:Dictionary=review.farming_clip()
	var end:Vector2=review.motion_view.position+clip.canvas_px*review.motion_view.scale
	var slot:Control=review.motion_view.get_parent()
	return review.motion_view.position.x>=-0.01 and review.motion_view.position.y>=-0.01 and end.x<=slot.size.x+0.01 and end.y<=slot.size.y+0.01
func snapshot(name:String) -> Image:
	await process_frame;await RenderingServer.frame_post_draw
	var picture:=root.get_texture().get_image()
	check("capture_"+name,picture.get_size()==Vector2i(2560,1440) and picture.save_png(evidence.path_join(name+".png"))==OK)
	return picture
func finish() -> void:
	var clips:Dictionary={}
	if is_instance_valid(review) and review.farming_library!=null:
		for id in review.farming_library.clips:
			var clip:Dictionary=review.farming_library.clips[id]
			clips[id]={"candidate_sha256":clip.candidate_sha256,"pose_ids":clip.pose_ids,"durations_ms":clip.durations_ms,"canvas_px":[clip.canvas_px.x,clip.canvas_px.y],"root_anchor_px":[clip.root_anchor_px.x,clip.root_anchor_px.y],"display_scale":clip.display_scale}
	var report:Dictionary={"scope":"24 fixed-outfit four-phase farming candidates: native UI selection/all停帧, ten consecutive panel cycles each, world one-shot each and transition controls. No production gameplay, independent modular composition, strict contact or user visual approval.","started_utc":started_utc,"finished_utc":Time.get_datetime_string_from_system(true),"input_contract_sha256":input_contract_sha256,"clips":clips,"checks":s.checks,"samples":samples,"captures":captures,"catalog_sha256":review.farming_library.catalog_sha256 if is_instance_valid(review) and review.farming_library!=null else ""}
	save_json(evidence.path_join("report.json"),report);save_json(evidence.path_join("checks.json"),s.checks)
	print("FARMING24_NATIVE checks=",s.checks.size()," passed=",s.passed()," samples=",samples.size()," captures=",captures.size())
	quit(0 if s.passed() else 1)
func run() -> void:
	if not evidence.begins_with("/private/tmp/coastal-"):printerr("isolated evidence path required");quit(2);return
	DirAccess.make_dir_recursive_absolute(evidence.path_join("sequence"));DirAccess.make_dir_recursive_absolute(evidence.path_join("boards"))
	var contract:=evidence.path_join("input-contract.json")
	if not FileAccess.file_exists(contract):printerr("pre-capture input contract required");quit(2);return
	input_contract_sha256=FileAccess.get_sha256(contract);started_utc=Time.get_datetime_string_from_system(true)
	trial=load("res://dev/characters/character_walk_trial.tscn").instantiate()
	var project:=ProjectSettings.globalize_path("res://..")
	trial.art_root=project.path_join("art/characters/builds/locomotion-r001")
	trial.run_candidate_root=project.path_join("art/characters/builds/run-r001")
	trial.run_diagnostics_enabled=true;trial.farming_review_enabled=true;trial.farming_transitions_enabled=true;trial.review_enabled=true
	trial.farming_review_action="hoe";trial.farming_catalog_path=project.path_join("art/characters/reviews/farming/catalog.json")
	root.add_child(trial);await focus();review=trial.review_panel
	check("native_renderer",DisplayServer.get_name()!="headless");check("all_24_actual_clips",review.farming_library.clips.size()==24)
	check("panel_fits",fits(review));check("top_controls_fit",fits(trial.get_node("TrialUI/Panel")))
	print("LAYOUT ",review.position," size=",review.size," slot=",review.motion_view.get_parent().size)
	for action in ["hoe","water","harvest"]:
		for direction in ["south","west","east","north"]:
			for garment in ["A","B"]:
				trial.set_garment(garment);review.select_clip(direction,action);check(action+direction+garment+"_full_canvas_fits",canvas_fits())
	if not s.passed():finish();return
	for action in ["hoe","water","harvest"]:
		for direction in ["south","west","east","north"]:
			for garment in ["A","B"]:
				await inspect_clip(action,direction,garment)
	await focus();await key(KEY_R,true);await key(KEY_R,false);await key(KEY_1,true);await key(KEY_1,false)
	await key(KEY_A,true);await key(KEY_SHIFT,true);await create_timer(0.1).timeout
	check("real_run_before_tool",trial.current_action=="run" and trial.facing=="west")
	await key(KEY_G,true);await key(KEY_G,false);await key(KEY_SHIFT,false);await key(KEY_A,false)
	var locked:Vector2=trial.actor.position
	await key(KEY_D,true);await key(KEY_2,true);await key(KEY_2,false)
	check("direction_and_wardrobe_queued",trial.current_action=="hoe" and trial.facing=="west" and trial.garment=="A")
	var deadline:=Time.get_ticks_msec()+3000
	while not trial.farming_clip.is_empty() and Time.get_ticks_msec()<deadline:await process_frame
	check("queued_wardrobe_after_end",trial.garment=="B")
	await key(KEY_D,false);await create_timer(0.08).timeout
	check("back_to_idle",trial.current_action=="idle")
	await key(KEY_G,true);await key(KEY_G,false);await key(KEY_R,true);await key(KEY_R,false)
	check("real_reset_cancels",trial.farming_clip.is_empty() and trial.current_action=="idle" and trial.actor.velocity==Vector2.ZERO)
	await snapshot("world-transitions-final")
	finish()
func inspect_clip(action:String,direction:String,garment:String) -> void:
	await focus();await key(KEY_R,true);await key(KEY_R,false)
	await key(KEY_1 if garment=="A" else KEY_2,true);await key(KEY_1 if garment=="A" else KEY_2,false)
	var dir_index:int=["south","west","east","north"].find(direction)
	await click(review.direction_buttons[dir_index]);await click(review.action_buttons[{"water":3,"hoe":4,"harvest":5}[action]])
	if review.playing:await click(review.play_button)
	var id:=action+"-"+direction+"-"+garment
	var clip:Dictionary=review.farming_library.get_clip(action,direction,garment)
	check(id+"_native_selection",review.review_direction==direction and review.review_action==action and trial.garment==garment and not review.playing)
	var slot:Control=review.motion_view.get_parent();var reference:Control=review.reference_view.get_parent()
	var board:=Image.create(2240,480,false,Image.FORMAT_RGBA8)
	for index in range(4):
		if index>0:await click(review.get_node("Margin/Rows/Playback/Next"))
		check(id+"_real_pose_"+str(index),review.motion_view.texture==clip.textures[index] and review.current_pose_index()==index)
		var picture:Image=await snapshot(id+"-pose-"+str(index))
		var transform:Transform2D=slot.get_global_transform_with_canvas();var at:Vector2=transform*Vector2.ZERO;var size:Vector2=transform.get_scale()*slot.size
		board.blit_rect(picture,Rect2i(Vector2i(at),Vector2i(size)),Vector2i((index+1)*448,0))
		if index==0:
			var ref_transform:Transform2D=reference.get_global_transform_with_canvas();var ref_at:Vector2=ref_transform*Vector2.ZERO
			board.blit_rect(picture,Rect2i(Vector2i(ref_at),Vector2i(size)),Vector2i.ZERO)
	board.save_png(evidence.path_join("boards/"+id+".png"))
	# Use actual movement key to set the world's direction, independent of panel.
	var direction_key:int={"south":KEY_S,"west":KEY_A,"east":KEY_D,"north":KEY_W}[direction]
	await key(direction_key,true);await key(direction_key,false);await create_timer(0.05).timeout
	check(id+"_world_direction_key",trial.facing==direction)
	# Reset preview to ready through the real next-frame and play controls.
	await click(review.get_node("Margin/Rows/Playback/Next"));await click(review.play_button)
	var action_key:int={"hoe":KEY_G,"water":KEY_F,"harvest":KEY_H}[action]
	await key(action_key,true);await key(action_key,false)
	check(id+"_world_action_key",trial.current_action==action)
	var position_before:Vector2=trial.actor.position
	var duration:float=review.preview_duration();var last:float=review.preview_phase_ms;var unwrapped:=0.0;var seen:Dictionary={};var world_seen:Dictionary={};var locked:=true;var pending:Array=[]
	var started:=Time.get_ticks_msec();var last_capture:=-100
	while unwrapped<duration*10 and Time.get_ticks_msec()-started<30000:
		await process_frame
		if not trial.focused:await focus()
		var phase:float=review.preview_phase_ms;unwrapped+=fposmod(phase-last,duration);last=phase
		var index:int=review.current_pose_index();seen[index]=true
		if not trial.farming_clip.is_empty():world_seen[trial.farming_pose_index()]=true;locked=locked and trial.actor.position==position_before
		var row:Dictionary={"clip":id,"wall_ms":Time.get_ticks_msec(),"phase_ms":phase,"unwrapped_ms":unwrapped,"pose":index,"world_action":trial.current_action,"world_elapsed_ms":trial.farming_elapsed_ms,"focused":trial.focused}
		if Time.get_ticks_msec()-last_capture>=200:
			RenderingServer.force_draw();var picture:=root.get_texture().get_image();picture.resize(1280,720,Image.INTERPOLATE_NEAREST)
			var path:="sequence/%s-%05d.png"%[id,pending.size()];pending.append({"file":path,"image":picture});row.capture=path;last_capture=Time.get_ticks_msec()
		samples.append(row)
	await click(review.play_button)
	check(id+"_ten_cycles",unwrapped>=duration*10 and seen.size()==4)
	check(id+"_world_all_poses_locked_then_idle",world_seen.size()==4 and locked and trial.farming_clip.is_empty() and trial.current_action=="idle")
	for entry in pending:entry.image.save_png(evidence.path_join(entry.file));captures.append(entry.file)
