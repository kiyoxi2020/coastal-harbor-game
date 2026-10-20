extends "res://tests/test_life_farming_native.gd"
func press(code:int,shift:bool=false,echo:bool=false):
 var event=InputEventKey.new()
 event.physical_keycode=code;event.pressed=true;event.shift_pressed=shift;event.echo=echo
 Input.parse_input_event(event)
 for i in range(2):await process_frame
 await key(code,false)
func run():
 evidence="/private/tmp/coastal-seed-keyboard"
 DirAccess.make_dir_recursive_absolute(evidence)
 w=load("res://scenes/harbor.tscn").instantiate()
 w.set_meta("save_directory","/private/tmp/coastal-seed-keyboard-save")
 w.set_meta("journal_test",true)
 root.add_child(w);w.start_new_game("种子键盘")
 w.release_input=false
 for i in range(3):await process_frame
 var tools=w.get_node("FarmTools")
 await press(KEY_TAB);await press(KEY_TAB)
 check("tab_opens_plant",tools.tool=="plant" and tools.get_node("Panel/Seeds").visible)
 await press(KEY_Q)
 check("q_next",tools.crop_id=="tomato" and tools.tool=="plant")
 if tools.crop_id!="tomato":finish();return
 await press(KEY_Q,true)
 check("shift_q_previous",tools.crop_id=="lettuce")
 await press(KEY_Q,false,true)
 check("echo_ignored",tools.crop_id=="lettuce")
 await press(KEY_TAB)
 check("tab_leaves_seed_bar",tools.tool=="harvest" and not tools.get_node("Panel/Seeds").visible)
 await press(KEY_Q)
 check("q_other_tool_ignored",tools.crop_id=="lettuce" and tools.tool=="harvest")
 await press(KEY_3)
 var seeds=tools.get_node("Panel/Seeds")
 check("three_reopens",tools.tool=="plant" and seeds.visible)
 check("no_combined_count",not seeds.has_node("Counts"))
 w.foraging.bag.remove_item("lettuce_seed",w.foraging.bag.count_item("lettuce_seed"))
 w.foraging.bag.remove_item("tomato_seed",w.foraging.bag.count_item("tomato_seed"))
 w.foraging.bag.add("tomato_seed",12)
 for i in range(3):await process_frame
 check("individual_counts",seeds.get_node("Lettuce/Count").text=="0" and seeds.get_node("Tomato/Count").text=="12")
 check("zero_seed_selectable",tools.crop_id=="lettuce" and not seeds.get_node("Lettuce").disabled)
 if DisplayServer.get_name()!="headless":await capture("01-zero-lettuce")
 await press(KEY_Q)
 check("highlight_tomato",seeds.get_node("Tomato").button_pressed and not seeds.get_node("Lettuce").button_pressed)
 if DisplayServer.get_name()!="headless":await capture("02-tomato-selected")
 await click(seeds.get_node("Lettuce"))
 check("mouse_still_selects",tools.crop_id=="lettuce")
 var target=w.farm_cell("garden_a:0:0")
 w.player.position=target.point-Vector2(0,12)
 w.player.facing="south"
 tools.mouse_target=false
 var prepared=w.perform_action("hoe",{"cell_id":target.id},int(w.foraging.life.action_seq)+1)
 check("prepare_plot",prepared.ok)
 check("keyboard_targets_plot",w.farm_target(false).get("id")==target.id)
 await press(KEY_E)
 check("zero_seed_no_plant",w.foraging.life.plots[target.id].crop_id=="")
 await press(KEY_Q)
 await press(KEY_E)
 check("e_plants_selected_seed",w.foraging.life.plots[target.id].crop_id=="tomato" and w.foraging.bag.count_item("tomato_seed")==11)
 for i in range(2):await process_frame
 check("badge_after_plant",seeds.get_node("Tomato/Count").text=="11")
 tools.select_seed("lettuce")
 w.journal.show_page("bag");await press(KEY_Q)
 check("menu_blocks_q",tools.crop_id=="lettuce")
 finish()
