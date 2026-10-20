extends "res://tests/test_life_farming_native.gd"
func press(code:int):
	await key(code,true);await key(code,false)
func run():
	evidence="/private/tmp/coastal-bag-return-native"
	DirAccess.make_dir_recursive_absolute(evidence)
	w=load("res://scenes/harbor.tscn").instantiate()
	w.set_meta("save_directory","/private/tmp/coastal-bag-return-save")
	root.add_child(w)
	check("isolated",w.save_service.directory=="/private/tmp/coastal-bag-return-save")
	if w.save_service.directory!="/private/tmp/coastal-bag-return-save":finish();return
	check("native",DisplayServer.get_name()!="headless")
	w.start_new_game("返回导航")
	w.foraging.bag.add("tomato",6);w.foraging.bag.add("clam",2);w.foraging.bag.add("snail",2)
	await press(KEY_B);await press(KEY_D);await press(KEY_D);await press(KEY_E)
	var ui=w.journal
	check("middle_item_actions",ui.selected_index==2 and root.gui_get_focus_owner()==ui.bag_page.get_node("Details/move"))
	await capture("01-item-actions")
	await press(KEY_D);await press(KEY_E)
	check("split_modal",ui.modal_kind=="quantity")
	await press(KEY_ESCAPE)
	check("cancel_returns_split",root.gui_get_focus_owner()==ui.bag_page.get_node("Details/split"))
	await press(KEY_ESCAPE)
	check("returns_original",ui.mode=="bag" and ui.selected_index==2 and root.gui_get_focus_owner()==ui.bag_page.get_node("BagGrid").get_child(2))
	await capture("02-return-item")
	await press(KEY_TAB)
	check("tab_actions",root.gui_get_focus_owner()==ui.bag_page.get_node("Details/move"))
	await press(KEY_TAB)
	check("tab_menu",ui.pause_menu.get_node("Surface/Tabs").is_ancestor_of(root.gui_get_focus_owner()))
	await press(KEY_ESCAPE)
	check("closes",ui.mode=="")
	check("inventory_unchanged",w.foraging.bag.count_item("snail")==2 and w.foraging.bag.count_item("tomato")==6)
	finish()
