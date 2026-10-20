extends SceneTree
const S=preload("res://tests/life_test_support.gd")
var s=S.new()
var w
class FailedSave extends RefCounted:
 func write_save(_value):return false
func _initialize():call_deferred("run")
func run():
 w=load("res://scenes/harbor.tscn").instantiate()
 w.set_meta("journal_test",true);w.set_meta("skip_verification",true)
 w.set_meta("save_directory",s.temporary_directory("kitchen-v2-ui"))
 root.add_child(w);w.start_new_game("厨房")
 w.home.switch_room("house",Vector2(400,216));w.release_input=false
 for id in {"clam":6,"lettuce":3,"snail":2,"tomato":2,"kelp":4}:w.foraging.bag.add(id,{"clam":6,"lettuce":3,"snail":2,"tomato":2,"kelp":4}[id])
 w.journal.show_page("craft")
 var page=w.journal.get_node("Root/CraftPage")
 s.check("dynamic_browser",page.has_method("select_category"))
 if not page.has_method("select_category"):finish();return
 await process_frame
 s.check("real_recipes_only",page.visible_ids==["clam_salad","snail_stew"] and page.get_node("Surface/RecipesScroll/Recipes").get_child_count()==2)
 var row_controls=["Minus","Batches","Plus","Maximum","Return"]
 var separate=true
 for i in range(row_controls.size()-1):
  var first=page.get_node("Surface/"+row_controls[i]).get_rect()
  var second=page.get_node("Surface/"+row_controls[i+1]).get_rect()
  if first.intersects(second):
   separate=false
   print("OVERLAP ",row_controls[i],first," / ",row_controls[i+1],second)
 s.check("batch_controls_no_overlap",separate)
 var first_card=page.cards.clam_salad

 s.check("no_status_label",not first_card.has_node("Status"))
 var rows=page.get_node("Surface/IngredientScroll/Rows")
 s.check("ingredient_same_component",rows.get_child(0).get_node("Icon").get_script()==load("res://scripts/ui/trade_item.gd"))
 s.check("real_clam_lettuce",rows.get_child(0).get_node("Icon").item_id=="clam" and rows.get_child(1).get_node("Icon").item_id=="lettuce")
 s.check("same_clam_renderer",rows.get_child(0).get_node("Icon/Forage").get_script()==load("res://scripts/forage_pickup.gd"))
 s.check("same_lettuce_texture",rows.get_child(1).get_node("Icon").crop_texture()==preload("res://assets/farming-polish-v3/lettuce_mature.png"))
 page.maximum()
 s.check("max_three_batches",page.get_node("Surface/Batches").value==3 and page.get_node("Surface/Submit").text.contains("3"))
 page.submit()
 s.check("three_portions",w.foraging.bag.count_item("clam_salad")==3 and w.foraging.bag.count_item("lettuce")==0)
 s.check("after_short_disabled",page.get_node("Surface/Submit").disabled)
 page.select_category("processing")
 s.check("fertilizer_separate",page.visible_ids==["marine_fertilizer"])
 s.check("kelp_same_source",rows.get_child(0).get_node("Icon").item_id=="kelp")
 page.get_node("Surface/Search").text="不存在"
 page.get_node("Surface/Search").text_changed.emit("不存在")
 s.check("empty_safe",page.visible_ids.is_empty() and page.get_node("Surface/Submit").disabled and page.get_node("Surface/Empty").visible)
 page.get_node("Surface/Search").text=""
 page.get_node("Surface/Search").text_changed.emit("")
 page.get_node("Surface/Batches").value=1
 var seq=w.foraging.life.action_seq
 var service=w.action_service
 w.action_service=load("res://scripts/simulation/action_service.gd").new(FailedSave.new())
 page.submit()
 s.check("save_fail_atomic",w.foraging.life.action_seq==seq and w.foraging.bag.count_item("kelp")==4)
 w.action_service=service
 page.submit()
 s.check("processing_saves",w.foraging.bag.count_item("marine_fertilizer")==1)
 page.select_category("cooking")
 page.focus_recipe("clam_salad")
 var before_seq=w.foraging.life.action_seq
 press(page,KEY_E)
 s.check("E_enters_no_craft",root.gui_get_focus_owner()==page.get_node("Surface/Plus") and w.foraging.life.action_seq==before_seq)
 press(page,KEY_ESCAPE)
 s.check("back_preserves_recipe",root.gui_get_focus_owner()==page.cards.clam_salad and page.recipe_id=="clam_salad")
 page.get_node("Surface/Search").grab_focus()
 var text_event=InputEventKey.new();text_event.physical_keycode=KEY_W;text_event.pressed=true
 s.check("typing_not_navigation",not page.handle_key(text_event))
 press(page,KEY_ESCAPE)
 s.check("search_escape_to_grid",root.gui_get_focus_owner()==page.cards.clam_salad)
 page.get_node("Surface/Available").button_pressed=true
 s.check("only_available",page.visible_ids==["snail_stew"])
 page.get_node("Surface/Available").button_pressed=false
 page.definitions={}
 for i in range(24):page.definitions["fixture_%02d"%i]={"placeholder":true,"category":"cooking","name":"测试菜谱%02d"%i,"inputs":{"clam":1},"outputs":{"clam_salad":2}}
 page.render()
 s.check("twenty_four_cards",page.visible_ids.size()==24)
 # Extensibility fixture, not production recipes. No fake content is added to the catalog.
 page.definitions={}
 for i in range(60):page.definitions["fixture_%02d"%i]={"placeholder":true,"category":"cooking","name":"测试菜谱%02d"%i,"inputs":{"clam":1},"outputs":{"clam_salad":2}}
 page.select_category("cooking")
 await process_frame;await process_frame
 s.check("sixty_cards",page.visible_ids.size()==60 and page.get_node("Surface/RecipesScroll/Recipes").get_child_count()==60)
 page.focus_recipe("fixture_59")
 await process_frame;await process_frame
 s.check("focus_scrolls",page.get_node("Surface/RecipesScroll").scroll_vertical>0 and root.gui_get_focus_owner()==page.cards["fixture_59"])
 page.get_node("Surface/Search").text="菜谱59"
 page.get_node("Surface/Search").text_changed.emit("菜谱59")
 s.check("sixty_search",page.visible_ids==["fixture_59"])
 page.get_node("Surface/Search").text=""
 page.get_node("Surface/Search").text_changed.emit("")
 var ingredients={}
 for id in preload("res://scripts/inventory/item_catalog.gd").ITEMS:ingredients[id]=1
 page.definitions=preload("res://scripts/simulation/recipe_catalog.gd").all()
 page.definitions.clam_salad.inputs=ingredients
 page.get_node("Surface/Search").text=""
 page.select_recipe("clam_salad")
 await process_frame
 s.check("ten_ingredients",rows.get_child_count()==10 and page.get_node("Surface/IngredientScroll").get_v_scroll_bar().max_value>page.get_node("Surface/IngredientScroll").size.y)
 s.check("fixed_submit",page.get_node("Surface/Submit").position.y==548 and page.get_node("Surface/Submit").is_visible_in_tree())
 s.check("production_still_three",preload("res://scripts/simulation/recipe_catalog.gd").all_ids().size()==3)
 finish()
func press(page,key):
 var event=InputEventKey.new();event.physical_keycode=key;event.pressed=true
 page.handle_key(event)
func finish():
 print("KITCHEN_V2 ",s.checks.size()," passed=",s.passed())
 w.queue_free();await process_frame
 quit(0 if s.passed() else 1)
