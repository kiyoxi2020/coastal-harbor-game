extends "res://tests/test_life_farming_native.gd"
func run():
 evidence="/private/tmp/coastal-P09-layout-native"
 DirAccess.make_dir_recursive_absolute(evidence)
 w=load("res://scenes/harbor.tscn").instantiate()
 w.set_meta("save_directory","/private/tmp/coastal-P09-native-save")
 root.add_child(w)
 check("isolated",w.save_service.directory=="/private/tmp/coastal-P09-native-save")
 if w.save_service.directory!="/private/tmp/coastal-P09-native-save":finish();return
 check("native",DisplayServer.get_name()!="headless")
 check("continue",w.continue_game())
 for i in range(5):await process_frame
 var tools=w.get_node("FarmTools")
 tools.select_tool("water")
 var button=tools.get_node("Panel/Tools/Fertilize")
 check("unselected_text",not button.button_pressed and button.text=="5 ×1" and button.icon!=null and button.get_theme_color("font_color").get_luminance()<0.6)
 var rect=tools.get_node("Panel").get_global_rect()
 var bar=Rect2(rect.position*tools.scale,rect.size*tools.scale)
 for id in ["garden_a:0:0","garden_a:3:1","garden_b:0:0","garden_b:3:1"]:
  check("clear_"+id,not bar.has_point(w.player.get_canvas_transform()*w.farm_cell(id).point))
 await capture("07-readable-fifth-tool")
 w.journal.show_page("bag")
 check("cooked_details",w.journal.bag_page.get_node("Details/Description").text.contains("厨房制作") and not w.journal.bag_page.get_node("Details/Description").text.contains("可在鱼摊出售"))
 await capture("08-crafted-items-in-bag")
 check("crafted_counts",w.foraging.bag.count_item("clam_salad")==1 and w.foraging.bag.count_item("snail_stew")==2 and w.foraging.bag.count_item("marine_fertilizer")==1)
 finish()
