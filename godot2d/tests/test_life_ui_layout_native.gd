extends "res://tests/test_life_ui_native.gd"
# Read the completed isolated run; verify the final layout without altering its economy.
func run() -> void:
	evidence="/private/tmp/coastal-P06-layout-native"
	DirAccess.make_dir_recursive_absolute(evidence)
	w=load("res://scenes/harbor.tscn").instantiate()
	w.set_meta("save_directory","/private/tmp/coastal-P06-native-final-save")
	root.add_child(w)
	check("native_renderer",DisplayServer.get_name()!="headless")
	check("continue_isolated",w.continue_game())
	for i in range(4):await process_frame
	await tap_e()
	check("E_opens_saved_market",w.journal.mode=="trade")
	var page=w.journal.get_node("Root/TradePage")
	await capture("01-buy-seeds")
	await click(page.get_node("Surface/SellTab"))
	for i in range(3):await process_frame
	check("note_below_rows",page.get_node("Surface/Items/Item17").get_global_rect().end.y+8<=page.get_node("Surface/Note").global_position.y)
	await capture("03-sell-layout")
	check("saved_economy_unchanged",w.foraging.life.wallet==126 and w.foraging.bag.count_item("tomato_seed")==1)
	finish()
