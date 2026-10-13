extends SceneTree
const Room=preload("res://scripts/room_data.gd")
var failures:=0

func _initialize() -> void:
	call_deferred("run")

func check(name: String, condition: bool) -> void:
	print(("PASS " if condition else "FAIL ")+name)
	if not condition: failures+=1

func run() -> void:
	var scene=load("res://scenes/harbor.tscn").instantiate()
	scene.set_meta("journal_test",true)
	scene.set_meta("save_directory","/private/tmp/coastal-cottage-runtime-"+str(Time.get_ticks_usec()))
	root.add_child(scene)
	await process_frame
	check("spawn_clear_of_tall_leaf",Room.SPAWN==Vector2(320,160))
	check("legacy_door_save_normalized",scene.home.safe_position("house",Vector2(320,328))==Room.SPAWN)
	check("bed_footprint",Room.furniture()[0].rect==Rect2(192,144,48,80))
	var bed=scene.home.interior.sort_layer.get_node("Bed")
	check("bed_texture_loaded",bed.pilot_texture is Texture2D and bed.pilot_texture.get_size()==Vector2(48,80))
	var expected_art := ["nightstand", "kitchen", "table", "chair", "chest", "shelf", "photo", "plant", "window_left", "window_right"]
	for art_id in expected_art:
		var furniture_node=scene.home.interior.sort_layer.get_node_or_null(art_id)
		check("generated_furniture_"+art_id,furniture_node!=null and furniture_node.pilot_texture is Texture2D)
	check("generated_floor",scene.home.interior.get("floor_texture") is Texture2D)
	check("generated_wall",scene.home.interior.get("wall_texture") is Texture2D)
	check("generated_rugs",scene.home.interior.get("rug_texture") is Texture2D and scene.home.interior.get("bed_rug_texture") is Texture2D)
	var door=scene.home.interior.door
	check("indoor_three_shared_frames",door.pilot_frames.size()==3 and door.pilot_frames.all(func(t): return t is Texture2D and t.get_size()==Vector2(30,59)))
	check("indoor_closed_leaf_height",door.pilot_leaf_height>=44)
	check("frame_clears_spawn_feet",door.get("pilot_frame_top")==-54.0)
	check("inside_front_allowed",door.can_interact(door.approach))
	check("inside_back_rejected",not door.can_interact(door.position-Vector2(0,12)))
	check("outside_size_unchanged",scene.home.exterior_door.render_size==Vector2(22,29))
	scene.player.position=Room.SPAWN
	check("indoor_crossing_duration",scene.home.transition.travel_duration(Room.DOOR)>0.4)
	check("former_bed_side_safe",scene.home.safe_position("house",Vector2(280,180))==Vector2(280,180))
	check("game_started",scene.start_new_game("test"))
	check("enter_house_for_crossing",scene.home.switch_room("house",Room.SPAWN))
	check("exit_transition_started",scene.home.transition.begin())
	var started:=Time.get_ticks_msec()
	while scene.home.transition.phase!="Crossing" and Time.get_ticks_msec()-started<3000:
		await process_frame
	check("crossing_phase_reached",scene.home.transition.phase=="Crossing")
	var crossing_start: float=scene.player.position.y
	await create_timer(0.25).timeout
	check("crossing_progresses_without_teleport",scene.home.transition.phase=="Crossing" and scene.player.position.y<crossing_start-5 and scene.player.position.y>Room.DOOR.y-8)
	started=Time.get_ticks_msec()
	while scene.home.transition.busy and Time.get_ticks_msec()-started<6000:
		await process_frame
	check("crossing_completes",not scene.home.transition.busy and scene.foraging.location=="harbor")
	scene.queue_free()
	quit(1 if failures else 0)
