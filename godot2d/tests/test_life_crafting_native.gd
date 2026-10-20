extends "res://tests/test_life_farming_native.gd"
var native_evidence:="/private/tmp/coastal-P09-native"
var native_save:="/private/tmp/coastal-P09-native-save"
func press(code:int):
 await key(code,true);await key(code,false)
func run():
 evidence=native_evidence
 DirAccess.make_dir_recursive_absolute(evidence)
 w=load("res://scenes/harbor.tscn").instantiate()
 w.set_meta("save_directory",native_save)
 root.add_child(w)
 check("native",DisplayServer.get_name()!="headless")
 check("isolated",w.save_service.directory==native_save)
 if w.save_service.directory!=native_save:finish();return
 w.start_new_game("厨房验收")
 # Explicit isolated interaction fixture, not a production economy trajectory.
 for id in {"clam":1,"lettuce":1,"snail":2,"tomato":2,"kelp":4,"tomato_seed":1}:
  w.foraging.bag.add(id,{"clam":1,"lettuce":1,"snail":2,"tomato":2,"kelp":4,"tomato_seed":1}[id])
 if not await walk_to(Vector2(270,244),"road"):finish();return
 if not await walk_to(Vector2(270,194),"door_row"):finish();return
 if not await walk_to(w.home.exterior_door.approach,"door"):finish();return
 if not await pass_door("house","enter"):finish();return
 if not await walk_to(Vector2(320,216),"kitchen_row"):finish();return
 if not await walk_to(Vector2(400,216),"kitchen"):finish();return
 check("kitchen_in_range",w.can_open_craft())
 await tap_e()
 check("E_opens_craft",w.journal.mode=="craft")
 if w.journal.mode!="craft":finish();return
 var page=w.journal.get_node("Root/CraftPage")
 await capture("01-salad-inputs")
 # Keyboard Tab navigation reaches Submit and E crafts once.
 await tap_e()
 await press(KEY_D);await press(KEY_D);await press(KEY_D)
 check("keyboard_submit_focus",root.gui_get_focus_owner()==page.get_node("Surface/Submit"))
 await tap_e()
 check("salad_created",w.foraging.bag.count_item("clam_salad")==1 and w.foraging.bag.count_item("clam")==0)
 await capture("02-salad-complete")
 await click(page.get_node("Surface/RecipesScroll/Recipes/Recipe_snail_stew"))
 await click(page.get_node("Surface/Plus"))
 await click(page.get_node("Surface/Submit"))
 check("stew_two",w.foraging.bag.count_item("snail_stew")==2 and w.foraging.bag.count_item("snail")==0)
 await click(page.get_node("Surface/Processing"))
 await click(page.get_node("Surface/Plus"))
 await capture("03-fertilizer-inputs")
 await click(page.get_node("Surface/Submit"))
 check("fertilizer_two",w.foraging.bag.count_item("marine_fertilizer")==2 and w.foraging.bag.count_item("kelp")==0)
 check("short_disabled",page.get_node("Surface/Submit").disabled)
 await capture("04-fertilizer-complete")
 await press(KEY_ESCAPE)
 await press(KEY_ESCAPE)
 check("close_craft",w.journal.mode=="")
 if not await walk_to(Vector2(320,216),"back_row"):finish();return
 if not await walk_to(w.home.active_door().approach,"exit"):finish();return
 if not await pass_door("harbor","leave"):finish();return
 if not await walk_to(Vector2(270,194),"garden_row"):finish();return
 if not await walk_to(Vector2(270,244),"garden_approach"):finish();return
 var cell="garden_a:0:0"
 if not await walk_to(w.farm_cell(cell).point,"garden"):finish();return
 await apply(cell,KEY_1,"hoe")
 await press(KEY_3)
 await click(w.get_node("FarmTools/Panel/Seeds/Tomato"))
 await cell_click(cell)
 check("planted",w.foraging.life.plots[cell].crop_id=="tomato")
 await apply(cell,KEY_5,"fertilize")
 check("pending_fertilizer",w.foraging.life.plots[cell].fertilized and w.foraging.bag.count_item("marine_fertilizer")==1)
 await capture("05-pending-fertilizer")
 var seq=w.foraging.life.action_seq
 await cell_click(cell)
 check("no_stack",w.foraging.life.action_seq==seq and w.foraging.bag.count_item("marine_fertilizer")==1)
 await press(KEY_TAB)
 check("fifth_wraps_to_hoe",w.get_node("FarmTools").tool=="hoe")
 await apply(cell,KEY_2,"water")
 if not await walk_to(Vector2(270,244),"return_road"):finish();return
 if not await sleep_and_return(1):finish();return
 check("bonus_growth",w.foraging.life.plots[cell].growth==2 and not w.foraging.life.plots[cell].fertilized)
 if not await walk_to(w.farm_cell(cell).point,"grown"):finish();return
 await capture("06-growth2-toolbar")
 var before=w.foraging.to_data(w.player.position)
 check("reload",w.continue_game() and w.foraging.bag.snapshot()==before.bag and preload("res://scripts/simulation/life_rules.gd")._same_payload(w.foraging.life.plots,before.life.plots))
 finish()
