extends SceneTree
const S=preload("res://tests/life_test_support.gd")
var s=S.new()
var w
func _initialize():call_deferred("run")
func run():
 var recipes=preload("res://scripts/simulation/recipe_catalog.gd")
 s.check("one_per_batch",recipes.get_recipe("clam_salad").outputs.clam_salad==1 and recipes.get_recipe("snail_stew").outputs.snail_stew==1)
 w=load("res://scenes/harbor.tscn").instantiate()
 w.set_meta("journal_test",true);w.set_meta("skip_verification",true)
 w.set_meta("save_directory",s.temporary_directory("kitchen-feedback"))
 root.add_child(w);w.start_new_game("反馈")
 w.foraging.bag.add("clam",1);w.foraging.bag.add("lettuce",1)
 w.home.switch_room("house",Vector2(400,216));w.release_input=false
 w.journal.show_page("craft")
 var page=w.journal.get_node("Root/CraftPage")
 s.check("pot_in_header",page.has_node("Surface/HeaderIcon"))
 s.check("no_recipe_status",not page.cards.clam_salad.has_node("Status"))
 s.check("no_ingredient_status",not page.get_node("Surface/IngredientScroll/Rows").get_child(0).has_node("Missing"))
 s.check("no_yield_caption",not page.has_node("Surface/Yield") and not page.has_node("Surface/Summary"))
 var icon=page.cards.snail_stew.get_node("Icon")
 s.check("unavailable_gray_shader",icon.material is ShaderMaterial and icon.material.get_shader_parameter("gray"))
 if not page.has_node("Surface/HeaderIcon"):
  finish();return
 await process_frame
 s.check("title_clear_pot",not page.get_node("Surface/Title").get_rect().intersects(page.get_node("Surface/HeaderIcon").get_rect()))
 s.check("help_clear_grid",not page.get_node("Surface/Help").get_rect().intersects(page.get_node("Surface/RecipesScroll").get_rect()))
 page.definitions={"blank":{"placeholder":true,"category":"cooking","name":"测试菜谱","inputs":{"clam":1},"outputs":{"clam_salad":1}}}
 page.render()
 s.check("blank_placeholders",not page.cards.blank.get_node("Icon").visible and page.cards.blank.get_node("Name").text=="")
 s.check("blank_no_fake_details",not page.get_node("Surface/OutputIcon").visible)
 finish()
func finish():
 print("KITCHEN_FEEDBACK ",s.checks.size()," passed=",s.passed())
 w.queue_free();await process_frame
 quit(0 if s.passed() else 1)
