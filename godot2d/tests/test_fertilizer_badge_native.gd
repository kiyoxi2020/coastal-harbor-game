extends "res://tests/test_life_farming_native.gd"
func run():
 evidence="/private/tmp/coastal-fertilizer-badge"
 DirAccess.make_dir_recursive_absolute(evidence)
 w=load("res://scenes/harbor.tscn").instantiate()
 w.set_meta("save_directory","/private/tmp/coastal-fertilizer-badge-save")
 w.set_meta("journal_test",true)
 root.add_child(w);w.start_new_game("肥料角标")
 w.release_input=false
 w.get_node("FarmTools").select_tool("fertilize")
 for i in range(3):await process_frame
 var tools=w.get_node("FarmTools/Panel/Tools")
 var button=tools.get_node("Fertilize")
 check("no_shortcut_text",button.text=="")
 check("same_tool_width",button.size==tools.get_node("Hoe").size)
 check("zero_badge",button.get_node("Count").text=="0")
 await capture("01-zero-badge")
 w.foraging.bag.add("marine_fertilizer",12)
 for i in range(2):await process_frame
 check("quantity_updates",button.get_node("Count").text=="12")
 check("badge_inside",button.get_global_rect().encloses(button.get_node("Count").get_global_rect()))
 await capture("02-quantity-badge")
 finish()
