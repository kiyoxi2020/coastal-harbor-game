extends "res://tests/test_life_farming_native.gd"
func press(code:int):
	await key(code,true);await key(code,false)
func run():
	evidence="/private/tmp/coastal-trade-return-native"
	DirAccess.make_dir_recursive_absolute(evidence)
	w=load("res://scenes/harbor.tscn").instantiate()
	w.set_meta("save_directory","/private/tmp/coastal-trade-return-native-save")
	root.add_child(w)
	check("native",DisplayServer.get_name()!="headless")
	check("isolated",w.save_service.directory=="/private/tmp/coastal-trade-return-native-save")
	if w.save_service.directory!="/private/tmp/coastal-trade-return-native-save":finish();return
	w.start_new_game("买卖导航")
	w.foraging.bag.add("clam",2) # isolated sell UI fixture
	if not await walk_to(w.exterior.get_node("InteractPoints/market").position,"market"):finish();return
	await tap_e()
	var ui=w.journal
	var page=ui.get_node("Root/TradePage")
	await press(KEY_D);await press(KEY_E)
	check("E_actions_no_charge",page.item_id=="tomato_seed" and w.foraging.life.wallet==100 and root.gui_get_focus_owner()==page.get_node("Surface/Plus"))
	await press(KEY_E);await press(KEY_D)
	check("quantity_two",page.get_node("Surface/Quantity").value==2)
	await capture("01-buy-controls")
	await press(KEY_E)
	check("purchase_saved",w.foraging.life.wallet==84 and w.foraging.bag.count_item("tomato_seed")==2)
	await press(KEY_ESCAPE)
	check("back_to_selected",ui.mode=="trade" and root.gui_get_focus_owner()==page.get_node("Surface/Items/Item1"))
	await press(KEY_TAB);await press(KEY_TAB);await press(KEY_D);await press(KEY_E)
	check("tab_sell",page.direction=="sell")
	await press(KEY_ESCAPE);await press(KEY_E);await press(KEY_D);await press(KEY_E)
	check("sell_saved",w.foraging.life.wallet==100 and w.foraging.bag.count_item("clam")==0)
	await capture("02-sell-result")
	await press(KEY_ESCAPE)
	check("sell_back_item",ui.mode=="trade" and page.item_id=="clam")
	await press(KEY_ESCAPE)
	check("second_escape_closes",ui.mode=="")
	finish()
