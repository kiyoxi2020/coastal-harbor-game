extends "res://tests/test_life_farming_native.gd"
func run():
 evidence="/private/tmp/coastal-kitchen-feedback-layout"
 DirAccess.make_dir_recursive_absolute(evidence)
 w=load("res://scenes/harbor.tscn").instantiate()
 w.set_meta("save_directory","/private/tmp/coastal-kitchen-feedback-layout-save")
 root.add_child(w);w.start_new_game("厨房反馈")
 check("native",DisplayServer.get_name()!="headless")
 check("isolated",w.save_service.directory=="/private/tmp/coastal-kitchen-feedback-layout-save")
 if w.save_service.directory!="/private/tmp/coastal-kitchen-feedback-layout-save":finish();return
 w.home.switch_room("house",Vector2(400,216));w.release_input=false
 w.foraging.bag.add("clam",1);w.foraging.bag.add("lettuce",1)
 w.journal.show_page("craft")
 var page=w.journal.get_node("Root/CraftPage")
 for i in range(5):await process_frame
 check("color_and_gray",not page.cards.clam_salad.get_node("Icon").material.get_shader_parameter("gray") and page.cards.snail_stew.get_node("Icon").material.get_shader_parameter("gray"))
 check("pot_transparent",page.get_node("Surface/HeaderIcon").texture.get_image().get_pixel(0,0).a==0)
 check("no_status_text",not page.cards.clam_salad.has_node("Status") and not page.get_node("Surface/IngredientScroll/Rows").get_child(0).has_node("Missing"))
 await capture("09-final-color-gray-and-header")
 page.get_node("Surface/Search").grab_focus()
 await capture("10-final-search-focus")
 w.foraging.bag.add("kelp",2)
 page.select_category("processing")
 page.get_node("Surface/Available").button_pressed=true;page.render()
 await capture("12-processing-available-filter")
 page.get_node("Surface/Available").button_pressed=false
 page.definitions={}
 for i in range(60):page.definitions["blank_%02d"%i]={"placeholder":true,"category":"cooking","name":"占位","inputs":{"clam":1},"outputs":{"clam_salad":1}}
 page.select_category("cooking");page.focus_recipe("blank_59")
 for i in range(5):await process_frame
 check("empty_card_art",not page.cards.blank_59.get_node("Icon").visible and page.cards.blank_59.get_node("Name").text=="")
 check("no_fake_output",not page.get_node("Surface/OutputIcon").visible and not page.get_node("Surface/Submit").visible)
 check("blank_scroll",page.get_node("Surface/RecipesScroll").scroll_vertical>0)
 await capture("11-final-empty-placeholders")
 finish()
