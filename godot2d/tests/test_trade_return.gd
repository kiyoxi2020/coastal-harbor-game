extends "res://tests/test_bag_navigation.gd"
func run():
	var w=load("res://scenes/harbor.tscn").instantiate()
	w.set_meta("journal_test",true);w.set_meta("skip_verification",true)
	w.set_meta("save_directory",s.temporary_directory("trade-return"))
	root.add_child(w);w.start_new_game("买卖返回")
	w.foraging.bag.add("clam",2)
	var ui=w.journal
	ui.dismiss()
	for i in range(3):await process_frame
	w.player.position=w.exterior.get_node("InteractPoints/market").position
	ui.show_page("trade");await process_frame;await process_frame
	var page=ui.get_node("Root/TradePage")
	await tap(KEY_D);await tap(KEY_E)
	s.check("E_enters_trade_controls",root.gui_get_focus_owner()==page.get_node("Surface/Plus"))
	s.check("E_preview_no_transaction",w.foraging.life.wallet==100 and page.item_id=="tomato_seed")
	await tap(KEY_ESCAPE)
	s.check("escape_returns_current_item",ui.mode=="trade" and root.gui_get_focus_owner()==page.get_node("Surface/Items/Item1"))
	if ui.mode!="trade":ui.show_page("trade")
	await tap(KEY_TAB)
	s.check("tab_keeps_trade",ui.mode=="trade")
	if ui.mode!="trade":ui.show_page("trade")
	await tap(KEY_TAB)
	s.check("tab_tabs",root.gui_get_focus_owner()==page.get_node("Surface/BuyTab"))
	await tap(KEY_ESCAPE)
	s.check("tabs_back_to_item",ui.mode=="trade" and root.gui_get_focus_owner()==page.get_node("Surface/Items/Item1"))
	var reverse=InputEventKey.new();reverse.physical_keycode=KEY_TAB;reverse.pressed=true;reverse.shift_pressed=true
	Input.parse_input_event(reverse);await process_frame;await process_frame
	s.check("reverse_tab_tabs",root.gui_get_focus_owner()==page.get_node("Surface/BuyTab"))
	await tap(KEY_D);await tap(KEY_E)
	s.check("sell_tab",page.direction=="sell")
	await tap(KEY_S);await tap(KEY_D);await tap(KEY_E)
	s.check("sell_item_actions",page.item_id=="snail" and root.gui_get_focus_owner()==page.get_node("Surface/Plus"))
	page.get_node("Surface/ReturnItem").pressed.emit();await process_frame
	s.check("return_button_keeps_item",root.gui_get_focus_owner()==page.get_node("Surface/Items/Item1") and page.item_id=="snail")
	page.submitting=true
	await tap(KEY_TAB);await tap(KEY_ESCAPE)
	s.check("submitting_blocks_exit",ui.mode=="trade" and root.gui_get_focus_owner()==page.get_node("Surface/Items/Item1"))
	page.submitting=false
	ui.confirm("确认",func():pass)
	await tap(KEY_ESCAPE)
	s.check("modal_cancel_keeps_trade",ui.modal==null and ui.mode=="trade")
	page.return_to_item();await tap(KEY_ESCAPE)
	s.check("browse_escape_closes",ui.mode=="")
	ui.show_page("trade");await process_frame;await process_frame
	page.enter_actions();page.get_node("Surface/Close").pressed.emit()
	s.check("close_direct",ui.mode=="")
	w.queue_free();await process_frame
	print("TRADE_RETURN ",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
