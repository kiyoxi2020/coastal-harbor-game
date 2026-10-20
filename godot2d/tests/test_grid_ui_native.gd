extends "res://tests/test_life_farming_native.gd"
func run() -> void:
	evidence="/private/tmp/coastal-grid-ui-native"
	DirAccess.make_dir_recursive_absolute(evidence)
	w=load("res://scenes/harbor.tscn").instantiate()
	root.add_child(w)
	await process_frame
	await process_frame
	check("title_hides_tools",not w.get_node("FarmTools").visible)
	await capture("title-without-tools")
	w.start_new_game("界面验收")
	await process_frame
	await process_frame
	check("play_shows_tools",w.get_node("FarmTools").visible)
	await click(w.hud.bag_button)
	check("bag_open",w.journal.mode=="bag")
	check("paused_bag_hides_tools",not w.get_node("FarmTools").visible)
	await capture("paused-bag-without-tools")
	w.journal.dismiss()
	await process_frame
	await process_frame
	check("close_restores_tools",w.get_node("FarmTools").visible)
	finish()
