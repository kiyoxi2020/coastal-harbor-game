extends "res://tests/test_bag_navigation.gd"
func run():
	var w=load("res://scenes/harbor.tscn").instantiate()
	w.set_meta("journal_test",true);w.set_meta("skip_verification",true)
	w.set_meta("save_directory",s.temporary_directory("menu-keyboard"))
	root.add_child(w);w.start_new_game("完整导航")
	w.foraging.bag.add("tomato",6)
	var ui=w.journal
	ui.show_page("bag");await process_frame;await process_frame
	await tap(KEY_W)
	s.check("grid_to_filter",get_root().gui_get_focus_owner()==ui.bag_page.get_node("Filter/filter_0"))
	await tap(KEY_W)
	s.check("filter_to_tabs",get_root().gui_get_focus_owner()==ui.get_node("Root/PauseMenu/Surface/Tabs/tab_bag"))
	await tap(KEY_D);await tap(KEY_E)
	s.check("profile_keyboard",ui.mode=="profile")
	await tap(KEY_D);await tap(KEY_E)
	s.check("settings_keyboard",ui.mode=="settings")
	await tap(KEY_S)
	var slider=ui.settings_page.get_node("Master")
	s.check("settings_slider_focus",get_root().gui_get_focus_owner()==slider)
	var volume:float=slider.value
	await tap(KEY_A)
	s.check("slider_changes",slider.value<volume)
	ui.show_page("bag");ui.select_slot("bag",0)
	await tap(KEY_W)
	for i in range(5):await tap(KEY_D)
	s.check("right_actions_reachable",get_root().gui_get_focus_owner()==ui.bag_page.get_node("Details/move"))
	await tap(KEY_S);await tap(KEY_S)
	s.check("sort_reachable",get_root().gui_get_focus_owner()==ui.bag_page.get_node("sort"))
	ui.dismiss()
	for i in range(3):await process_frame
	w.player.position=w.exterior.get_node("InteractPoints/market").position
	ui.show_page("trade");await process_frame;await process_frame
	var page=ui.get_node("Root/TradePage")
	var seq:int=w.foraging.life.action_seq
	await tap(KEY_RIGHT)
	s.check("trade_right_selects",page.item_id=="tomato_seed")
	await tap(KEY_A)
	s.check("trade_A_selects",page.item_id=="lettuce_seed")
	s.check("navigation_no_trade",w.foraging.life.action_seq==seq)
	await tap(KEY_S)
	s.check("trade_controls_reachable",get_root().gui_get_focus_owner()==page.get_node("Surface/Plus"))
	await tap(KEY_E)
	s.check("quantity_keyboard",page.get_node("Surface/Quantity").value==2)
	await tap(KEY_D)
	s.check("submit_reachable",get_root().gui_get_focus_owner()==page.get_node("Surface/Submit"))
	await tap(KEY_E)
	s.check("keyboard_trade_once",w.foraging.life.action_seq==seq+1 and w.foraging.life.wallet==90)
	s.check("purchase_keeps_submit_focus",get_root().gui_get_focus_owner()==page.get_node("Surface/Submit"))
	await tap(KEY_W);await tap(KEY_W);await tap(KEY_D);await tap(KEY_E)
	s.check("buy_to_sell_keyboard",page.direction=="sell")
	ui.confirm("导航隔离",func():pass)
	await tap(KEY_D)
	s.check("modal_navigation_contained",ui.modal.is_ancestor_of(get_root().gui_get_focus_owner()))
	s.check("modal_does_not_trade",w.foraging.life.action_seq==seq+1)
	ui.cancel_modal()
	ui.new_game_dialog()
	var editor=ui.get_node("Root/Dialogs/NameDialog/Panel/player_name")
	editor.grab_focus();editor.select_all()
	var typing=InputEventKey.new();typing.physical_keycode=KEY_D;typing.keycode=KEY_D;typing.unicode=100;typing.pressed=true
	Input.parse_input_event(typing);await process_frame;await process_frame
	typing=typing.duplicate();typing.pressed=false;Input.parse_input_event(typing);await process_frame
	s.check("typing_not_navigation",editor.text=="d" and get_root().gui_get_focus_owner()==editor and ui.modal_kind=="name")
	ui.cancel_modal()
	w.queue_free();await process_frame
	print("MENU_KEYBOARD ",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
