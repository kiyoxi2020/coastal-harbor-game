extends Node
var checks: Dictionary = {}
var output := "res://verification-house"
var scene
var phases: Array[String]=[]
var capture_steps:=true
var recording:=false
var recording_frame:=0
var recording_time:=0.0
var frame_pending:=false

func _process(delta: float) -> void:
	if not recording or DisplayServer.get_name()=="headless" or frame_pending: return
	recording_time+=delta
	if recording_time>=0.1:
		recording_time=0
		capture_frame()
func capture_frame() -> void:
	frame_pending=true
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(output.path_join("frames/%04d.png" % recording_frame))
	recording_frame+=1
	frame_pending=false
func phase_event(value: String) -> void:
	phases.append(value)
func exit_report(value: String) -> void:
	if value!="Idle": return
	var saved: Dictionary=scene.save_service.read_save()
	check("exit_saved_destination",saved.ok and saved.data.location=="house")
	check("exit_saved_safe_point",saved.ok and saved.data.position==[320.0,300.0])
	write_report()
func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	call_deferred("run")
func check(id: String, value: bool) -> void:
	checks[id] = value
	print(("PASS " if value else "FAIL ")+id)
func key(action: String) -> void:
	# A released frame separates physical presses and clears the menu-release latch.
	for i in range(3): await get_tree().process_frame
	press_key(action,true)
	await get_tree().process_frame
	await get_tree().process_frame
	press_key(action,false)
	await get_tree().process_frame
func press_key(action: String,pressed: bool) -> void:
	var event:=InputEventKey.new()
	event.physical_keycode={"inspect":KEY_E,"journal":KEY_B,"reset":KEY_R}[action]
	event.keycode=event.physical_keycode
	event.pressed=pressed
	Input.parse_input_event(event)
func shot(id: String) -> void:
	if DisplayServer.get_name()=="headless": return
	await RenderingServer.frame_post_draw
	check("shot_"+id,get_viewport().get_texture().get_image().save_png(output.path_join(id+".png"))==OK)
func wait_door() -> void:
	var started := Time.get_ticks_msec()
	while scene.home.transition.busy and Time.get_ticks_msec()-started<6000:
		await get_tree().process_frame
	check("transition_finishes_"+str(checks.size()),not scene.home.transition.busy)
	for i in range(3): await get_tree().physics_frame
func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output=arg.trim_prefix("--output=")
	DirAccess.make_dir_recursive_absolute(output)
	scene=get_parent()
	await get_tree().process_frame
	if OS.get_cmdline_user_args().has("--resume-check"):
		check("restart",scene.continue_game())
		check("restart_house",scene.foraging.location=="house")
		check("restart_position",scene.player.position.distance_to(Vector2(320,300))<1)
		check("restart_inventory",scene.foraging.chest.count_item("clam")==1)
		check("restart_doors_closed",scene.home.active_door().pose==0)
		await shot("12-restarted")
		finish()
		return
	check("new_game",scene.start_new_game("海风"))
	await get_tree().process_frame
	var home=scene.home
	home.transition.phase_changed.connect(phase_event)
	if OS.get_cmdline_user_args().has("--exit-check"):
		scene.player.position=home.active_door().approach
		home.transition.phase_changed.connect(exit_report)
		check("exit_begin",home.transition.begin())
		scene.request_exit()
		check("exit_deferred",home.transition.exit_pending and home.transition.busy)
		return
	var door=home.active_door()
	check("separate_door",door.get_parent()!=scene.sort_layer.get_node("House"))
	check("front_valid",door.can_interact(door.approach))
	check("back_rejected",not door.can_interact(door.position-Vector2(0,30)))
	check("far_rejected",not door.can_interact(door.approach+Vector2(40,0)))
	check("closed_collision",not door.collision.disabled)
	check("body_cutout",scene.sort_layer.get_node("House").has_meta("door_cutout"))
	check("house_above_ground",scene.sort_layer.get_node("House").z_index>=0 and door.z_index>=0)
	scene.player.position=door.approach
	for pose in [1,2,0]:
		door.set_pose(pose)
		for i in range(2): await get_tree().physics_frame
		check("door_pose_"+str(pose),door.pose==pose and door.collision.disabled==(pose==2))
		await shot("00-exterior-pose-"+str(pose))
	await shot("01-outside-closed")
	if OS.get_cmdline_user_args().has("--record-house"):
		DirAccess.make_dir_recursive_absolute(output.path_join("frames"))
		recording=true
	await key("inspect")
	check("e_starts_opening",home.transition.busy)
	check("duplicate_rejected",not home.transition.begin())
	check("save_during_crossing",scene.save_progress() and scene.save_service.read_save().data.location=="harbor")
	await key("journal")
	check("no_menu_during_transition",scene.journal.mode=="")
	await key("reset")
	check("reset_locked",scene.player.position.distance_to(scene.data.SPAWN)>10)
	await wait_door()
	check("entered",scene.foraging.location=="house")
	check("indoor_safe",scene.player.position.distance_to(Vector2(320,300))<1)
	check("outdoor_disabled",home.outdoor.process_mode==Node.PROCESS_MODE_DISABLED and not home.outdoor.visible)
	check("indoor_enabled",home.interior.visible and home.interior.process_mode!=Node.PROCESS_MODE_DISABLED)
	check("camera_fixed",scene.get_node("WorldCamera").position==Vector2(320,200))
	check("door_closed_after",home.active_door().pose==0)
	check("phase_sequence",phases==["Approach","Opening","Crossing","FadeOut","Swap","FadeIn","Arrival","Closing","AwaitRelease","Idle"])
	check("no_outdoor_pickups",scene.nearest_pickup(Vector2(244,330)).is_empty())
	await shot("04-interior")
	scene.foraging.collect("clam_a","clam")
	scene.player.position=Vector2(448,316)
	await key("inspect")
	check("inside_storage",scene.journal.mode=="storage")
	check("store",scene.foraging.bag.transfer_to(scene.foraging.chest,0,1)==1)
	scene.journal.close_menu()
	for i in range(3): await get_tree().process_frame
	await key("reset")
	check("indoor_reset",scene.player.position.distance_to(Vector2(320,300))<1)
	scene.player.position=Vector2(144,228)
	await key("inspect")
	check("bed_view",scene.hud.panel.visible and "休息" in scene.hud.description.text)
	await key("inspect")
	check("e_closes_view",not scene.hud.panel.visible)
	scene.player.position=home.active_door().approach
	await key("inspect")
	await wait_door()
	check("exited",scene.foraging.location=="harbor")
	check("shared_storage",scene.foraging.chest.count_item("clam")==1)
	check("outdoor_restored",home.outdoor.visible and home.outdoor.process_mode!=Node.PROCESS_MODE_DISABLED)
	check("indoor_disabled",not home.interior.visible and home.interior.process_mode==Node.PROCESS_MODE_DISABLED)
	check("collected_not_reset",scene.foraging.collected.has("clam_a") and not scene.pickup_nodes.clam_a.visible)
	await shot("08-exterior-return")
	capture_steps=false
	recording=false
	while frame_pending: await get_tree().process_frame
	# Hold interaction through a full crossing: landing must remain locked until release.
	scene.player.position=home.active_door().approach
	for i in range(3): await get_tree().process_frame
	press_key("inspect",true)
	await get_tree().process_frame
	await get_tree().process_frame
	var hold_start:=Time.get_ticks_msec()
	while home.transition.phase!="AwaitRelease" and Time.get_ticks_msec()-hold_start<6000:
		await get_tree().process_frame
	check("hold_e_await_release",home.transition.busy and home.transition.phase=="AwaitRelease")
	check("hold_e_one_crossing",scene.foraging.location=="house")
	press_key("inspect",false)
	await wait_door()
	# Switch failure injection uses the actual missing destination, not a mock transition.
	home.switch_room("harbor",home.exterior_door.approach)
	var saved_interior=home.interior
	check("failure_begin",home.transition.begin())
	home.interior=null
	await wait_door()
	check("failure_restores_source",scene.foraging.location=="harbor" and scene.player.position==home.exterior_door.approach)
	check("failure_clears_fade",home.transition.fade.modulate.a==0 and home.exterior_door.pose==0)
	home.interior=saved_interior
	for i in range(3): await get_tree().process_frame
	var nodes_before:=get_tree().get_node_count()
	for i in range(20):
		scene.player.position=home.active_door().approach
		check("repeat_begin_"+str(i),home.transition.begin())
		await wait_door()
	check("20_crossings_no_nodes_leaked",get_tree().get_node_count()==nodes_before)
	check("20_crossings_inventory",scene.foraging.chest.count_item("clam")==1 and scene.foraging.total_collected==1)
	# Real physics: indoor furniture and wall contacts, not only rectangle math.
	home.switch_room("house",Vector2(144,228))
	Input.action_press("up")
	for i in range(45): await get_tree().physics_frame
	Input.action_release("up")
	check("bed_blocks",scene.player.position.y>=211)
	scene.player.position=Vector2(116,228)
	Input.action_press("up")
	for i in range(45): await get_tree().physics_frame
	Input.action_release("up")
	check("old_bed_side_walkable",scene.player.position.y<200)
	scene.player.position=Vector2(540,240)
	Input.action_press("right")
	for i in range(45): await get_tree().physics_frame
	Input.action_release("right")
	check("wall_blocks",scene.player.position.x<558)
	home.switch_room("house",Vector2(320,300))
	check("save_inside",scene.save_progress())
	scene.return_to_title()
	check("continue_inside",scene.continue_game() and scene.foraging.location=="house")
	check("continue_inventory",scene.foraging.chest.count_item("clam")==1)
	var bad: Dictionary=scene.foraging.to_data(Vector2(140,140))
	check("bad_house_written",scene.save_service.write_save(bad))
	scene.return_to_title()
	# Returning to title autosaves: inject the bad fixture after that save.
	scene.save_service.write_save(bad)
	check("bad_house_continue",scene.continue_game() and scene.player.position==Vector2(320,300))
	var legacy: Dictionary=scene.foraging.to_data(Vector2(330,250))
	legacy.version=1
	legacy.erase("location")
	scene.return_to_title()
	var fixture:=FileAccess.open(scene.save_service.directory+"/progress.json",FileAccess.WRITE)
	fixture.store_string(JSON.stringify(legacy))
	fixture.close()
	check("old_save_continues_outside",scene.continue_game() and scene.foraging.location=="harbor" and scene.player.position==Vector2(330,250))
	check("old_save_keeps_inventory",scene.foraging.chest.count_item("clam")==1)
	home.switch_room("house",Vector2(320,300))
	check("final_indoor_save",scene.save_progress())
	var normal_save=scene.save_service
	scene.save_service=load("res://scripts/save_service.gd").new(normal_save.directory+"/progress.json/impossible")
	check("save_failure_explicit",not scene.save_progress() and scene.save_message!="进度已保存。")
	scene.save_service=normal_save
	scene.hud.toast_remaining=0
	check("bad_position_fallback",home.safe_position("house",Vector2(140,140))==Vector2(320,300))
	check("bad_outdoor_fallback",home.safe_position("harbor",Vector2(-50,-50))==scene.data.SPAWN)
	await shot("10-interior-saved")
	finish()
func finish() -> void:
	write_report()
	get_tree().quit(1 if checks.values().has(false) else 0)
func write_report() -> void:
	var f:=FileAccess.open(output.path_join("tests.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":not checks.values().has(false),"checks":checks},"\t"))
	f.close()
	print("HOUSE ",checks.size()," passed=",not checks.values().has(false))
