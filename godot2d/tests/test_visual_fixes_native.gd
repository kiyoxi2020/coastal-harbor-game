extends "res://tests/test_life_farming_native.gd"
func run() -> void:
	evidence="/private/tmp/coastal-v6-native"
	DirAccess.make_dir_recursive_absolute(evidence)
	w=load("res://scenes/harbor.tscn").instantiate()
	w.set_meta("save_directory","/private/tmp/coastal-v6-native-save")
	root.add_child(w)
	check("native_renderer",DisplayServer.get_name()!="headless")
	check("isolated",w.save_service.directory=="/private/tmp/coastal-v6-native-save")
	if w.save_service.directory!="/private/tmp/coastal-v6-native-save":finish();return
	check("new_game",w.start_new_game("精度修订"))
	# Isolated inventory fixture, not production earnings.
	for id in ["clam","snail","kelp","tomato","lettuce"]:w.foraging.bag.add(id,6)
	await key(KEY_B,true);await key(KEY_B,false)
	await capture("01-clear-seafood")
	await key(KEY_RIGHT,true);await key(KEY_RIGHT,false)
	check("right_moves_frame",w.journal.selected_index==1)
	await key(KEY_DOWN,true);await key(KEY_DOWN,false)
	check("down_moves_frame",w.journal.selected_index==7)
	await key(KEY_LEFT,true);await key(KEY_LEFT,false)
	await key(KEY_UP,true);await key(KEY_UP,false)
	check("back_to_first",w.journal.selected_index==0)
	var page=w.journal.bag_page
	await click(page.get_node("Details/move"))
	await key(KEY_DOWN,true);await key(KEY_DOWN,false)
	check("arrows_do_not_commit",w.journal.selected_index==6 and w.foraging.bag.snapshot()[0].id=="clam")
	await capture("02-keyboard-cursor")
	await tap_e()
	check("E_commits_target",w.foraging.bag.snapshot()[0].id=="" and w.foraging.bag.snapshot()[6].id=="clam")
	await key(KEY_ESCAPE,true);await key(KEY_ESCAPE,false)
	check("closed",w.journal.mode=="")
	if not await walk_to(Vector2(124,238),"west_flower_view"):finish();return
	await capture("03-flowers-west")
	if not await walk_to(Vector2(270,244),"middle_flower_view"):finish();return
	await capture("04-flowers-middle")
	if not await walk_to(Vector2(296,302),"beach_steps"):finish();return
	if not await walk_to(Vector2(296,330),"beach_row"):finish();return
	if not await walk_to(Vector2(244,330),"clam_pickup"):finish();return
	await capture("05-same-seafood-world")
	await tap_e()
	check("pickup_still_works",w.foraging.bag.count_item("clam")==7)
	finish()
