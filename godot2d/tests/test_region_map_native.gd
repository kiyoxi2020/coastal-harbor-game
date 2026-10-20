extends "res://tests/test_life_farming_native.gd"
func run()->void:
	evidence="/private/tmp/coastal-map-native"
	DirAccess.make_dir_recursive_absolute(evidence)
	w=load("res://scenes/harbor.tscn").instantiate()
	w.set_meta("save_directory","/private/tmp/coastal-map-native-save")
	root.add_child(w)
	check("native",DisplayServer.get_name()!="headless")
	check("isolated",w.save_service.directory=="/private/tmp/coastal-map-native-save")
	if w.save_service.directory!="/private/tmp/coastal-map-native-save":finish();return
	check("new_game",w.start_new_game("港口漫步"))
	for i in range(4):await process_frame
	if not await walk_to(Vector2(320,250),"north_road"):finish();return
	if not await walk_to(Vector2(320,64),"old_exit"):finish();return
	await capture("01-old-north-exit")
	await tap_e()
	for i in range(5):await process_frame
	check("district_arrival",w.foraging.location=="harbor_district" and w.player.position.distance_to(Vector2(320,350))<1)
	if not await walk_to(Vector2(320,220),"plaza"):finish();return
	await capture("02-district-plaza")
	if not await walk_to(Vector2(180,220),"restaurant_front"):finish();return
	if not await walk_to(Vector2(180,190),"restaurant"):finish();return
	await tap_e()
	check("restaurant_info",w.hud.panel.visible and not paused)
	await capture("03-restaurant-info")
	await tap_e()
	await key(KEY_M,true)
	await key(KEY_M,false)
	check("map_open",w.world_map.visible and paused and w.world_map.selected_region=="harbor_district")
	var before:Dictionary=w.foraging.to_data(w.player.position)
	w.world_map.select_region("harbor")
	w.world_map.region_buttons.harbor.grab_focus()
	await key(KEY_W,true)
	await key(KEY_E,true)
	await key(KEY_E,false)
	await key(KEY_W,false)
	check("map_input_isolation",w.world_map.visible and w.foraging.to_data(w.player.position)==before and w.journal.mode=="")
	await capture("04-world-map")
	await key(KEY_ESCAPE,true)
	await key(KEY_ESCAPE,false)
	check("map_close",not paused and not w.world_map.visible)
	for i in range(4):await process_frame
	var saved_point:Vector2=w.player.position
	check("district_save",w.save_progress())
	check("district_reload",w.continue_game() and w.foraging.location=="harbor_district" and w.player.position.distance_to(saved_point)<0.1)
	if not await walk_to(Vector2(180,220),"back_from_restaurant"):finish();return
	if not await walk_to(Vector2(320,220),"return_plaza"):finish();return
	if not await walk_to(Vector2(320,380),"district_exit"):finish();return
	await tap_e()
	for i in range(4):await process_frame
	check("returned_harbor",w.foraging.location=="harbor" and w.player.position.distance_to(Vector2(320,94))<1)
	# Revisit original door after crossing regions to protect room choreography.
	if not await walk_to(Vector2(320,194),"old_road"):finish();return
	if not await walk_to(w.home.exterior_door.approach,"old_door"):finish();return
	if not await pass_door("house","old_house"):finish();return
	await capture("05-old-house-after-travel")
	await key(KEY_M,true)
	await key(KEY_M,false)
	check("house_map",w.world_map.visible and paused and w.world_map.selected_region=="harbor")
	await capture("06-house-map")
	await key(KEY_M,true)
	await key(KEY_M,false)
	finish()
