extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
var s=Support.new()
func _initialize():call_deferred("run")
func tap(code:int):
	for down in [true,false]:
		var e=InputEventKey.new();e.physical_keycode=code;e.keycode=code;e.pressed=down
		Input.parse_input_event(e)
		await process_frame
	await process_frame
func run():
	var w=load("res://scenes/harbor.tscn").instantiate()
	w.set_meta("journal_test",true);w.set_meta("skip_verification",true)
	w.set_meta("save_directory",s.temporary_directory("navigation"))
	root.add_child(w);w.start_new_game("导航")
	w.foraging.bag.add("tomato",6);w.foraging.bag.add("clam",1)
	w.foraging.bag.add("lettuce",1);w.foraging.bag.add("snail",1)
	var ui=w.journal
	ui.show_page("bag");await process_frame
	ui.select_slot("bag",2)
	await tap(KEY_E)
	s.check("E_enters_actions",root.gui_get_focus_owner()==ui.bag_page.get_node("Details/move") and ui.selected_index==2)
	await tap(KEY_ESCAPE)
	s.check("escape_returns_item",ui.mode=="bag" and root.gui_get_focus_owner()==ui.bag_page.get_node("BagGrid").get_child(2))
	if ui.mode!="bag":ui.show_page("bag")
	ui.select_slot("bag",0)
	await tap(KEY_TAB)
	s.check("tab_changes_region",ui.mode=="bag" and root.gui_get_focus_owner()==ui.bag_page.get_node("Details/move"))
	if ui.mode!="bag":ui.show_page("bag")
	ui.select_slot("bag",0)
	ui._start_move()
	await tap(KEY_DOWN);await tap(KEY_ESCAPE)
	s.check("cancel_move_restores_source",ui.pending=="" and ui.selected_index==0 and w.foraging.bag.snapshot()[0].amount==6)
	ui.select_slot("bag",8);await tap(KEY_E)
	s.check("empty_no_actions",root.gui_get_focus_owner()==ui.bag_page.get_node("BagGrid").get_child(8))
	ui.select_slot("bag",0);await tap(KEY_E);await tap(KEY_RIGHT);await tap(KEY_E)
	s.check("split_dialog",ui.modal_kind=="quantity")
	await tap(KEY_ESCAPE)
	s.check("modal_restores_split",root.gui_get_focus_owner()==ui.bag_page.get_node("Details/split") and ui.mode=="bag")
	ui.bag_page.get_node("return_item").pressed.emit();await process_frame
	s.check("return_button",root.gui_get_focus_owner()==ui.bag_page.get_node("BagGrid").get_child(0))
	var tab=InputEventKey.new();tab.physical_keycode=KEY_TAB;tab.pressed=true;tab.shift_pressed=true
	Input.parse_input_event(tab);await process_frame;await process_frame
	s.check("reverse_tab_filter",ui.bag_page.get_node("Filter").is_ancestor_of(root.gui_get_focus_owner()))
	ui.select_slot("bag",0)
	await tap(KEY_RIGHT)
	s.check("right_selection",ui.selected_index==1)
	await tap(KEY_DOWN);s.check("down_selection",ui.selected_index==7)
	await tap(KEY_LEFT);s.check("left_selection",ui.selected_index==6)
	await tap(KEY_UP);s.check("up_selection",ui.selected_index==0)
	await tap(KEY_LEFT);s.check("left_boundary",ui.selected_index==0)
	ui._set_category("seafood")
	await tap(KEY_RIGHT);s.check("filter_skip",ui.selected_index==3)
	ui._set_category("");ui.select_slot("bag",0);ui._start_move()
	await tap(KEY_DOWN)
	s.check("move_preview_only",ui.selected_index==6 and w.foraging.bag.snapshot()[0].amount==6 and w.foraging.bag.snapshot()[6].id=="")
	await tap(KEY_E)
	s.check("E_confirms_move",w.foraging.bag.snapshot()[6].id=="tomato" and w.foraging.bag.snapshot()[0].id=="")
	ui.action_split()
	var selected:int=ui.selected_index
	await tap(KEY_DOWN)
	s.check("modal_keeps_bag_cursor",ui.selected_index==selected)
	ui.cancel_modal()
	ui.select_slot("bag",23)
	await tap(KEY_DOWN);s.check("bottom_boundary",ui.selected_index==23)
	await tap(KEY_RIGHT);s.check("right_boundary",ui.selected_index==23)
	ui.select_slot("bag",0)
	var repeat=InputEventKey.new();repeat.physical_keycode=KEY_RIGHT;repeat.pressed=true;repeat.echo=true
	Input.parse_input_event(repeat);await process_frame;await process_frame
	s.check("repeat_arrow_moves",ui.selected_index==1)
	w.queue_free();await process_frame
	print("BAG_NAVIGATION ",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
