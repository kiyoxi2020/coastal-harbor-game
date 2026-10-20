extends "res://tests/test_life_farming_native.gd"
func press(code:int):
 await key(code,true);await key(code,false)
func type_text(text:String):
 for character in text:
  var event=InputEventKey.new()
  event.unicode=character.unicode_at(0)
  event.pressed=true
  Input.parse_input_event(event)
  await process_frame
func run():
 evidence="/private/tmp/coastal-kitchen-v2-native"
 DirAccess.make_dir_recursive_absolute(evidence)
 w=load("res://scenes/harbor.tscn").instantiate()
 w.set_meta("save_directory","/private/tmp/coastal-kitchen-v2-native-save")
 root.add_child(w)
 check("native",DisplayServer.get_name()!="headless")
 check("isolated",w.save_service.directory=="/private/tmp/coastal-kitchen-v2-native-save")
 if w.save_service.directory!="/private/tmp/coastal-kitchen-v2-native-save":finish();return
 w.start_new_game("食谱本")
 # Isolated interaction fixture, not a natural food-production/economic trajectory.
 for id in {"clam":6,"lettuce":3,"snail":2,"tomato":2,"kelp":4}:
  w.foraging.bag.add(id,{"clam":6,"lettuce":3,"snail":2,"tomato":2,"kelp":4}[id])
 if not await walk_to(Vector2(270,244),"road"):finish();return
 if not await walk_to(Vector2(270,194),"door_row"):finish();return
 if not await walk_to(w.home.exterior_door.approach,"door"):finish();return
 if not await pass_door("house","enter"):finish();return
 if not await walk_to(Vector2(320,216),"kitchen_row"):finish();return
 if not await walk_to(Vector2(400,216),"kitchen"):finish();return
 await tap_e()
 check("kitchen_E_opens",w.journal.mode=="craft")
 if w.journal.mode!="craft":finish();return
 var page=w.journal.get_node("Root/CraftPage")
 check("two_real_foods",page.visible_ids==["clam_salad","snail_stew"])
 await capture("01-cooking-same-ingredients")
 var seq=w.foraging.life.action_seq
 await tap_e()
 check("E_enters_only",w.foraging.life.action_seq==seq and root.gui_get_focus_owner()==page.get_node("Surface/Plus"))
 await press(KEY_D);await tap_e()
 check("max_three",page.get_node("Surface/Batches").value==3 and page.get_node("Surface/Submit").text=="制作 3 份")
 await capture("02-batch-summary")
 await press(KEY_D);await press(KEY_D);await tap_e()
 check("salad_three",w.foraging.bag.count_item("clam_salad")==3 and w.foraging.bag.count_item("lettuce")==0)
 await press(KEY_ESCAPE)
 check("back_same_card",w.journal.mode=="craft" and root.gui_get_focus_owner()==page.cards.clam_salad)
 await click(page.get_node("Surface/Available"))
 check("only_stew",page.visible_ids==["snail_stew"])
 await click(page.get_node("Surface/Processing"))
 check("processing_separate",page.visible_ids==["marine_fertilizer"])
 await click(page.get_node("Surface/Plus"))
 await capture("03-processing-kelp-source")
 await click(page.get_node("Surface/Submit"))
 check("fertilizer_two",w.foraging.bag.count_item("marine_fertilizer")==2 and w.foraging.bag.count_item("kelp")==0)
 check("filtered_empty",page.visible_ids.is_empty() and page.get_node("Surface/Submit").disabled)
 await capture("04-empty-after-making")
 await click(page.get_node("Surface/Available"))
 page.focus_recipe("marine_fertilizer")
 await press(KEY_ESCAPE)
 check("grid_escape_closes",w.journal.mode=="")
 w.journal.show_page("bag")
 await capture("05-bag-shared-products")
 w.journal.dismiss()
 w.release_input=false
 w.journal.show_page("craft")
 var definitions=page.definitions.duplicate(true)
 page.get_node("Surface/Available").button_pressed=false
 page.definitions={}
 for i in range(60):page.definitions["fixture_%02d"%i]={"placeholder":true,"category":"cooking","name":"测试菜谱%02d"%i,"inputs":{"clam":1},"outputs":{"clam_salad":2}}
 page.select_category("cooking")
 page.focus_recipe("fixture_59")
 for i in range(5):await process_frame
 check("sixty_scroll",page.visible_ids.size()==60 and page.get_node("Surface/RecipesScroll").scroll_vertical>0)
 await capture("06-sixty-recipe-fixture")
 page.get_node("Surface/Search").grab_focus()
 await type_text("测试菜谱59")
 for i in range(2):await process_frame
 check("chinese_search",page.get_node("Surface/Search").text=="测试菜谱59" and page.visible_ids==["fixture_59"])
 await capture("07-chinese-search")
 await press(KEY_ESCAPE)
 check("search_escape_preserves_query",root.gui_get_focus_owner()==page.cards.get("fixture_59") and page.get_node("Surface/Search").text=="测试菜谱59")
 var ingredients={}
 for id in preload("res://scripts/inventory/item_catalog.gd").ITEMS:ingredients[id]=1
 page.definitions=definitions.duplicate(true)
 page.definitions.clam_salad.inputs=ingredients
 page.get_node("Surface/Search").text=""
 page.select_recipe("clam_salad")
 for i in range(5):await process_frame
 var scroll=page.get_node("Surface/IngredientScroll")
 scroll.scroll_vertical=500
 await capture("08-ten-ingredient-fixture")
 check("ten_ingredients_scroll",scroll.scroll_vertical>0 and page.get_node("Surface/IngredientScroll/Rows").get_child_count()==10)
 check("actions_fixed",page.get_node("Surface/Submit").position==Vector2(648,548) and page.get_node("Surface/Submit").is_visible_in_tree())
 page.definitions=definitions
 page.get_node("Surface/Search").text=""
 page.select_category("processing")
 page.focus_recipe("marine_fertilizer")
 await press(KEY_ESCAPE)
 check("fixture_not_persisted",preload("res://scripts/simulation/recipe_catalog.gd").all_ids().size()==3)
 check("reload",w.continue_game() and w.foraging.bag.count_item("clam_salad")==3 and w.foraging.bag.count_item("marine_fertilizer")==2)
 finish()
