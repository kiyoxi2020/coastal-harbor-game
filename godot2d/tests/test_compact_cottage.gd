extends SceneTree
const Room=preload("res://scripts/room_data.gd")
var failures:=0
func check(id: String,value: bool) -> void:
	if not value: failures+=1
	print(("PASS " if value else "FAIL ")+id)
func _initialize() -> void:
	call_deferred("run")
func run() -> void:
	var scene=load("res://scenes/harbor.tscn").instantiate()
	scene.set_meta("journal_test",true)
	scene.set_meta("save_directory","/private/tmp/compact-cottage-"+str(Time.get_ticks_usec()))
	root.add_child(scene)
	await process_frame
	scene.start_new_game("compact")
	for location in ["harbor","house"]:
		scene.home.switch_room(location,Vector2.ZERO)
		var door=scene.home.active_door()
		var all_depths:=true
		for depth in range(57):
			for lateral in [-24,0,24]:
				all_depths=door.can_interact(door.position+door.entrance_normal*depth+Vector2(lateral,0)) and all_depths
		check(location+"_continuous_depth_0_56_lateral_24",all_depths)
		check(location+"_back_rejected",not door.can_interact(door.position-door.entrance_normal))
		check(location+"_far_rejected",not door.can_interact(door.position+door.entrance_normal*57))
		check(location+"_side_rejected",not door.can_interact(door.position+door.entrance_normal*24+Vector2(25,0)))
	check("compact_floor",Room.FLOOR==Rect2(176,112,288,208))
	check("south_entry",Room.DOOR==Vector2(320,320) and Room.SPAWN==Vector2(320,288))
	check("valid_old_save_preserved",scene.home.safe_position("house",Vector2(320,300))==Vector2(320,300))
	check("old_north_save_reset",scene.home.safe_position("house",Vector2(320,128))==Room.SPAWN)
	check("new_door_save_reset",scene.home.safe_position("house",Room.DOOR)==Room.SPAWN)
	check("new_bed_blocks_save",scene.home.safe_position("house",Vector2(216,190))==Room.SPAWN)
	scene.home.switch_room("house",Room.SPAWN)
	scene.player.position=Room.DOOR+Vector2(12,-12)
	check("near_begin",scene.home.transition.begin())
	var initial_y: float=scene.player.position.y
	await create_timer(0.08).timeout
	check("near_does_not_retreat",scene.player.position.y>=initial_y-0.1)
	check("no_forced_player_layer",scene.player.z_index==0)
	var started:=Time.get_ticks_msec()
	var partial:=false
	var fully_visible_on_floor:=true
	var fade_observed:=false
	while scene.home.transition.busy and Time.get_ticks_msec()-started<6000:
		partial=partial or (scene.player.doorway_hidden>0 and scene.player.doorway_hidden<1)
		if scene.home.transition.phase=="Crossing" and scene.player.position.y>=Room.DOOR.y:
			fully_visible_on_floor=fully_visible_on_floor and scene.player.doorway_hidden==0
		if scene.home.transition.phase=="FadeOut":
			fade_observed=true
			check("fully_hidden_before_fade",scene.player.doorway_hidden==1)
			break
		await process_frame
	check("progressive_clip_seen",partial)
	check("fade_out_observed",fade_observed)
	check("full_character_until_inside_aperture",fully_visible_on_floor)
	while scene.home.transition.busy and Time.get_ticks_msec()-started<6000: await process_frame
	check("transition_completed_at_expected_destination",not scene.home.transition.busy and scene.foraging.location=="harbor")
	check("clip_cleanup",scene.player.doorway_hidden==0 and scene.player.modulate.a==1 and scene.player.z_index==0)
	check("aperture_cleanup",scene.player.doorway_material.get_shader_parameter("aperture_top")< -999999)
	scene.home.switch_room("house",Room.SPAWN)
	await physics_frame
	scene.player.position=Room.DOOR+Vector2(20,-28)
	var blocker:=StaticBody2D.new()
	var collision:=CollisionShape2D.new()
	var box:=RectangleShape2D.new()
	box.size=Vector2(4,14)
	collision.shape=box
	blocker.position=Room.DOOR+Vector2(10,-28)
	blocker.add_child(collision)
	scene.home.interior.add_child(blocker)
	await physics_frame
	await physics_frame
	var before: Vector2=scene.player.position
	check("blocked_alignment_rejected",not scene.home.transition.begin())
	check("blocked_alignment_control_and_position",not scene.home.transition.busy and scene.player.position==before)
	blocker.position=Room.DOOR+Vector2(0,-20)
	scene.player.position=Room.SPAWN
	await physics_frame
	await physics_frame
	check("wall_between_actor_and_door_rejected",not scene.home.transition.begin())
	blocker.queue_free()
	await physics_frame
	scene.journal.mode="bag"
	check("menu_rejects_door",not scene.home.transition.begin())
	scene.journal.mode=""
	# Sweep the actual character shape along routes to each functional area.
	for route in [
		[Vector2(320,240),Vector2(216,240)],
		[Vector2(320,192),Vector2(400,192)],
		[Vector2(320,306),Vector2(416,306)],
		[Vector2(320,180),Vector2(280,180),Vector2(280,142)],
		[Vector2(320,240),Vector2(190,240),Vector2(190,252)]]:
		scene.player.position=Room.SPAWN
		var clear:=true
		for point in route:
			clear=(scene.player.move_and_collide(point-scene.player.position)==null) and clear
		check("physics_route_"+str(route[-1]),clear)
	scene.player.set_doorway_hidden(0.8)
	scene.player.doorway_material.set_shader_parameter("aperture_top",136.0)
	scene.home.switch_room("house",Vector2(320,300))
	check("load_clears_visual_and_preserves_valid_legacy_point",scene.player.doorway_hidden==0 and scene.player.position==Vector2(320,300))
	check("load_clears_aperture",scene.player.doorway_material.get_shader_parameter("aperture_top")< -999999)
	scene.player.set_doorway_hidden(0.5)
	scene.player.doorway_material.set_shader_parameter("aperture_top",136.0)
	scene.home.reset_player()
	check("reset_clears_visual_to_south_spawn",scene.player.doorway_hidden==0 and scene.player.position==Room.SPAWN)
	check("reset_clears_aperture",scene.player.doorway_material.get_shader_parameter("aperture_top")< -999999)
	if DisplayServer.get_name()!="headless":
		await render_clipping(scene)
		await render_aperture_top(scene)
		if OS.get_cmdline_user_args().has("--capture-doorways"):
			await capture_doorways(scene)
	quit(1 if failures else 0)

func render_aperture_top(scene) -> void:
	# Use the real transition's material and real animation, rendered at world coordinates.
	scene.home.switch_room("harbor",Room.OUTSIDE_DOOR-Vector2(0,4))
	scene.player.position=Room.OUTSIDE_DOOR-Vector2(0,4)
	scene.home.transition.clipping_door=scene.home.active_door()
	scene.home.transition.update_clip()
	var viewport:=SubViewport.new()
	viewport.size=Vector2i(400,240)
	viewport.transparent_bg=true
	viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var sprite:=AnimatedSprite2D.new()
	sprite.sprite_frames=scene.player.sprite.sprite_frames
	sprite.animation="north"
	sprite.scale=scene.player.sprite.scale
	sprite.position=scene.player.position+scene.player.sprite.position
	sprite.material=scene.player.doorway_material
	viewport.add_child(sprite)
	await process_frame
	await RenderingServer.frame_post_draw
	var rendered:=viewport.get_texture().get_image()
	var above:=0
	var below:=0
	for y in range(240):
		for x in range(400):
			if rendered.get_pixel(x,y).a>0.5:
				if y<136: above+=1
				else: below+=1
	check("exterior_actual_pixels_occluded_above_awning",above==0)
	check("exterior_actual_pixels_preserved_below_aperture",below>0)
	rendered.save_png("/private/tmp/compact-aperture-top.png")
	scene.home.transition.clipping_door=null
	scene.player.reset_doorway_visual()
	viewport.queue_free()

func render_clipping(scene) -> void:
	var viewport:=SubViewport.new()
	viewport.size=Vector2i(96,96)
	viewport.transparent_bg=true
	viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var sprite:=AnimatedSprite2D.new()
	sprite.sprite_frames=scene.player.sprite.sprite_frames
	sprite.scale=scene.player.sprite.scale
	sprite.position=Vector2(48,48)
	sprite.material=scene.player.doorway_material
	viewport.add_child(sprite)
	for direction in ["north","south"]:
		sprite.animation=direction
		var counts: Array[int]=[]
		for hidden in [0.0,0.5,1.0]:
			scene.player.set_doorway_hidden(hidden)
			await process_frame
			await RenderingServer.frame_post_draw
			var rendered:=viewport.get_texture().get_image()
			var count:=0
			for y in range(96):
				for x in range(96):
					if rendered.get_pixel(x,y).a>0.5: count+=1
			counts.append(count)
			rendered.save_png("/private/tmp/compact-clip-"+direction+"-"+str(hidden)+".png")
		check(direction+"_actual_shader_progressive",counts[0]>counts[1] and counts[1]>0 and counts[2]==0)
	scene.player.reset_doorway_visual()
	viewport.queue_free()

func capture_doorways(scene) -> void:
	DirAccess.make_dir_recursive_absolute("/private/tmp/compact-door-stages")
	for location in ["harbor","house"]:
		scene.home.switch_room(location,Room.OUTSIDE_APPROACH if location=="harbor" else Room.SPAWN)
		await physics_frame
		await capture_stage(location+"-before")
		check(location+"_capture_begin",scene.home.transition.begin())
		var captured: Dictionary={}
		var start:=Time.get_ticks_msec()
		while scene.home.transition.busy and Time.get_ticks_msec()-start<7000:
			var phase: String=scene.home.transition.phase
			var hidden: float=scene.player.doorway_hidden
			var id: String=""
			if phase=="Crossing" and hidden>0.2 and hidden<0.8: id="partial"
			if phase=="FadeOut" and hidden==1: id="full"
			if phase=="Arrival" and hidden>0.2 and hidden<0.8: id="emerging"
			if id!="" and not captured.has(id):
				captured[id]=true
				await capture_stage(location+"-"+id)
			await process_frame
		check(location+"_all_visual_stages",captured.size()==3 and not scene.home.transition.busy)
		await capture_stage(location+"-closed")
func capture_stage(id: String) -> void:
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("/private/tmp/compact-door-stages/"+id+".png")
