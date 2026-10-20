extends "res://tests/test_life_farming_native.gd"
func run():
 evidence="/private/tmp/coastal-hud-map-button"
 DirAccess.make_dir_recursive_absolute(evidence)
 w=load("res://scenes/harbor.tscn").instantiate()
 w.set_meta("save_directory","/private/tmp/coastal-hud-map-button-save")
 w.set_meta("journal_test",true)
 root.add_child(w);w.start_new_game("地图入口")
 for i in range(3):await process_frame
 var button=w.hud.get_node_or_null("Root/MapButton")
 check("map_button_exists",button!=null)
 if button==null:finish();return
 check("buttons_separate",not button.get_global_rect().intersects(w.hud.bag_button.get_global_rect()))
 check("same_size",button.size==w.hud.bag_button.size)
 check("map_key_hint",button.get_node("Hint").text=="M")
 for location in ["harbor","house","harbor_district"]:
  w.home.switch_room(location,Vector2(400,216));w.release_input=false
  check("no_bottom_map_"+location,not "地图" in w.hud.controls.text)
 w.home.switch_room("harbor",Vector2(400,216));w.release_input=false
 if DisplayServer.get_name()!="headless":await capture("01-map-and-bag")
 await click(button)
 check("click_opens_map",w.world_map.visible and paused)
 if DisplayServer.get_name()!="headless":await capture("02-map-open")
 await key(KEY_M,true);await key(KEY_M,false)
 check("m_closes_map",not w.world_map.visible and not paused)
 w.release_input=false
 await key(KEY_M,true);await key(KEY_M,false)
 check("m_opens_map",w.world_map.visible)
 w.world_map.close();w.release_input=false
 w.journal.show_page("bag");button.pressed.emit()
 check("bag_blocks_map",not w.world_map.visible)
 w.journal.close_menu();w.release_input=false
 w.hud.panel.show();button.pressed.emit()
 check("location_blocks_map",not w.world_map.visible)
 w.hud.dismiss();w.release_input=true;button.pressed.emit()
 check("release_blocks_map",not w.world_map.visible)
 finish()
