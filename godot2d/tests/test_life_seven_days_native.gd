extends "res://tests/test_life_farming_native.gd"
func click(button: Button) -> void:
	if w.journal.mode=="sleep" and not support.checks.has("capture_07-bed-sleep"):
		await capture("07-bed-sleep")
	await super.click(button)
func pass_door(destination: String,id: String) -> bool:
	var ok: bool=await super.pass_door(destination,id)
	if ok and id=="enter_day1":await capture("08-interior-door")
	return ok
func run() -> void:
	evidence="/private/tmp/coastal-P07-native"
	DirAccess.make_dir_recursive_absolute(evidence)
	w=load("res://scenes/harbor.tscn").instantiate()
	w.set_meta("save_directory","/private/tmp/coastal-P07-native-save")
	root.add_child(w)
	check("native_renderer",DisplayServer.get_name()!="headless")
	check("isolated",w.save_service.directory=="/private/tmp/coastal-P07-native-save")
	if w.save_service.directory!="/private/tmp/coastal-P07-native-save":finish();return
	check("new_game",w.start_new_game("七日验收"))
	for i in range(4): await process_frame
	if OS.get_cmdline_user_args().has("--inspect-bed"):
		await sleep_and_return(1)
		finish()
		return
	if not await walk_to(Vector2(270,244),"market_road"):finish();return
	if not await walk_to(w.exterior.get_node("InteractPoints/market").position,"market"):finish();return
	await tap_e()
	check("market_open",w.journal.mode=="trade")
	var page=w.journal.get_node("Root/TradePage")
	await click(page.get_node("Surface/Submit"))
	check("seed_bought",w.foraging.bag.count_item("lettuce_seed")==1 and w.foraging.life.wallet==95)
	await capture("01-market")
	await click(page.get_node("Surface/Close"))
	if not await walk_to(Vector2(270,244),"farm_road"):finish();return
	if not await walk_to(w.farm_cell("garden_a:0:0").point,"farm"):finish();return
	await apply("garden_a:0:0",KEY_1,"hoe")
	await apply("garden_a:0:0",KEY_3,"plant")
	await apply("garden_a:0:0",KEY_2,"water")
	await capture("02-planted")
	if not await sleep_and_return(1):finish();return
	if not await walk_to(w.farm_cell("garden_a:0:0").point,"day2_farm"):finish();return
	await apply("garden_a:0:0",KEY_2,"water_day2")
	if not await sleep_and_return(2):finish();return
	if not await walk_to(w.farm_cell("garden_a:0:0").point,"mature_farm"):finish();return
	await capture("03-mature")
	await apply("garden_a:0:0",KEY_4,"harvest")
	check("harvest_three",w.foraging.bag.count_item("lettuce")==3)
	if not await walk_to(Vector2(270,244),"sell_road"):finish();return
	if not await walk_to(w.exterior.get_node("InteractPoints/market").position,"sell"):finish();return
	await tap_e()
	await click(page.get_node("Surface/SellTab"))
	await click(page.get_node("Surface/Items/Item3"))
	await click(page.get_node("Surface/Plus"))
	await click(page.get_node("Surface/Plus"))
	await click(page.get_node("Surface/Submit"))
	check("sold_three",w.foraging.life.wallet==131 and w.foraging.bag.count_item("lettuce")==0)
	await capture("04-sold")
	await click(page.get_node("Surface/Close"))
	for day in range(3,8):
		if not await sleep_and_return(day):finish();return
	check("native_day8",w.foraging.life.day_id==8 and w.foraging.life.daily_reports.size()==7)
	await key(KEY_B,true)
	await key(KEY_B,false)
	await click(w.journal.get_node("Root/PauseMenu/Surface/Tabs/tab_daily"))
	check("day7_diary",w.journal.mode=="daily" and w.journal.get_node("Root/DailyPage/Surface/Title").text.contains("第7日"))
	await capture("05-day7-report")
	finish()
