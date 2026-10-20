extends "res://tests/test_life_farming_native.gd"
func tap_at(point:Vector2) -> void:
	var motion:=InputEventMouseMotion.new()
	motion.position=point
	root.push_input(motion,true)
	for pressed in [true,false]:
		var event:=InputEventMouseButton.new()
		event.position=point
		event.button_index=MOUSE_BUTTON_LEFT
		event.pressed=pressed
		root.push_input(event,true)
		await process_frame
	await process_frame
func trade_open(id:String) -> bool:
	if not await walk_to(Vector2(270,244),id+"_road"):return false
	if not await walk_to(w.exterior.get_node("InteractPoints/market").position,id):return false
	await tap_e()
	check(id+"_E_open",w.journal.mode=="trade")
	return w.journal.mode=="trade"
func run() -> void:
	evidence="/private/tmp/coastal-P06-native"
	DirAccess.make_dir_recursive_absolute(evidence)
	w=load("res://scenes/harbor.tscn").instantiate()
	w.set_meta("save_directory","/private/tmp/coastal-P06-native-final-save")
	root.add_child(w)
	check("native_renderer",DisplayServer.get_name()!="headless")
	check("isolated_save",w.save_service.directory=="/private/tmp/coastal-P06-native-final-save")
	if w.save_service.directory!="/private/tmp/coastal-P06-native-final-save":finish();return
	check("new_game",w.start_new_game("买种种菜"))
	for i in range(4):await process_frame
	if not await trade_open("initial_market"):finish();return
	var page=w.journal.get_node("Root/TradePage")
	var spin=page.get_node("Surface/Quantity")
	await click(page.get_node("Surface/Plus"))
	check("mouse_quantity_2",spin.value==2)
	await capture("01-buy-seeds")
	await click(page.get_node("Surface/Submit"))
	check("mouse_buy_saved",w.foraging.life.wallet==90 and w.foraging.bag.count_item("lettuce_seed")==2)
	await key(KEY_ESCAPE,true)
	check("esc_closes",w.journal.mode=="" and w.release_input)
	# E before releasing Escape must not reopen the market.
	await key(KEY_E,true)
	check("held_close_no_reopen",w.journal.mode=="")
	await key(KEY_E,false)
	await key(KEY_ESCAPE,false)
	for i in range(3):await process_frame
	await tap_e()
	check("release_can_reopen",w.journal.mode=="trade")
	await click(page.get_node("Surface/Close"))
	if not await walk_to(Vector2(270,244),"to_farm"):finish();return
	if not await walk_to(w.farm_cell("garden_a:0:0").point,"crop"):finish();return
	await apply("garden_a:0:0",KEY_1,"hoe")
	await key(KEY_3,true)
	await key(KEY_3,false)
	await cell_click("garden_a:0:0")
	check("seed_planted",w.foraging.bag.count_item("lettuce_seed")==1 and w.foraging.life.plots["garden_a:0:0"].crop_id=="lettuce")
	await apply("garden_a:0:0",KEY_2,"water_day1")
	if not await sleep_and_return(1):finish();return
	# Reopen the same persisted source-day report from the journal entry.
	await key(KEY_B,true)
	await key(KEY_B,false)
	await click(w.journal.get_node("Root/PauseMenu/Surface/Tabs/tab_daily"))
	check("diary_reopen",w.journal.mode=="daily" and w.journal.get_node("Root/DailyPage/Surface/Title").text.contains("第1日") and w.journal.get_node("Root/DailyPage/Surface/Body").text.contains("支出 10"))
	await capture("02-day1-report")
	await click(w.journal.get_node("Root/DailyPage/Surface/Close"))
	if not await walk_to(w.farm_cell("garden_a:0:0").point,"rewater"):finish();return
	await apply("garden_a:0:0",KEY_2,"water_day2")
	if not await sleep_and_return(2):finish();return
	if not await walk_to(w.farm_cell("garden_a:0:0").point,"harvest_return"):finish();return
	await apply("garden_a:0:0",KEY_4,"harvest")
	check("crop_yield",w.foraging.bag.count_item("lettuce")==3)
	if not await trade_open("sell_market"):finish();return
	await click(page.get_node("Surface/SellTab"))
	await click(page.get_node("Surface/Items/Item3"))
	# Quantity is still 2; one native plus-button click makes 3.
	await click(page.get_node("Surface/Plus"))
	page.get_node("Surface/Submit").grab_focus()
	await tap_e()
	check("keyboard_sell_crop",w.foraging.life.wallet==126 and w.foraging.bag.count_item("lettuce")==0 and w.foraging.life.accounts.market.buy_quota.lettuce==9)
	await capture("03-sell-crop")
	await click(page.get_node("Surface/Close"))
	if not await walk_to(Vector2(296,250),"beach_top"):finish();return
	if not await walk_to(Vector2(296,302),"steps"):finish();return
	if not await walk_to(Vector2(296,330),"beach_row"):finish();return
	if not await walk_to(Vector2(244,330),"clam"):finish();return
	await tap_e()
	check("real_collect",w.foraging.bag.count_item("clam")==1)
	if not await walk_to(Vector2(296,330),"return_beach"):finish();return
	if not await walk_to(Vector2(296,250),"return_steps"):finish();return
	if not await trade_open("clam_market"):finish();return
	await click(page.get_node("Surface/SellTab"))
	# Use the explicit decrement buttons; keyboard E submission was verified above.
	await click(page.get_node("Surface/Minus"))
	await click(page.get_node("Surface/Minus"))
	check("mouse_quantity_1",spin.value==1)
	await click(page.get_node("Surface/Submit"))
	check("sell_collected_clam",w.foraging.life.wallet==134 and w.foraging.bag.count_item("clam")==0)
	await click(page.get_node("Surface/BuyTab"))
	await click(page.get_node("Surface/Items/Item1"))
	await click(page.get_node("Surface/Submit"))
	check("income_buys_next_seed",w.foraging.life.wallet==126 and w.foraging.bag.count_item("tomato_seed")==1)
	await capture("04-rebuy-and-HUD")
	await click(page.get_node("Surface/Close"))
	var life:Dictionary=w.foraging.life.duplicate(true)
	check("resume_full_economy",w.continue_game() and preload("res://scripts/simulation/life_rules.gd")._same_payload(w.foraging.life,life))
	finish()
