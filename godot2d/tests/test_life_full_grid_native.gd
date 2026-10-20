extends "res://tests/test_life_farming_native.gd"
func run() -> void:
	evidence="/private/tmp/coastal-P07-full-grid-native"
	DirAccess.make_dir_recursive_absolute(evidence)
	w=load("res://scenes/harbor.tscn").instantiate()
	w.set_meta("save_directory","/private/tmp/coastal-P07-full-grid-native-save")
	root.add_child(w)
	check("isolated",w.save_service.directory=="/private/tmp/coastal-P07-full-grid-native-save")
	if w.save_service.directory!="/private/tmp/coastal-P07-full-grid-native-save":finish();return
	check("native",DisplayServer.get_name()!="headless")
	check("new_game",w.start_new_game("满田操作夹具"))
	# Explicit interaction fixture; seed procurement/economic balances are covered
	# through real transactions in test_life_seven_days, not claimed here.
	w.foraging.bag.add("lettuce_seed",8)
	w.foraging.bag.add("tomato_seed",8)
	w._set_state(w.foraging)
	for i in range(4):await process_frame
	if not await walk_to(Vector2(270,244),"approach"):finish();return
	var started:=Time.get_ticks_msec()
	for id in preload("res://scripts/simulation/state_schema.gd").cell_ids():
		if not await walk_to(w.farm_cell(id).point,id):finish();return
		await apply(id,KEY_1,"hoe_"+id)
		await key(KEY_3,true)
		await key(KEY_3,false)
		await click(w.get_node("FarmTools/Panel/Seeds/"+("Lettuce" if id.begins_with("garden_a") else "Tomato")))
		await cell_click(id)
		while w.player.action_busy:await process_frame
		check("plant_"+id,w.foraging.life.plots[id].crop_id==("lettuce" if id.begins_with("garden_a") else "tomato"))
		await apply(id,KEY_2,"water_"+id)
	print("FULL_GRID_AUTOMATED_MS ",Time.get_ticks_msec()-started)
	await capture("01-sixteen-planted")
	check("all_watered",w.foraging.life.plots.values().all(func(p):return p.watered and p.crop_id!=""))
	finish()
