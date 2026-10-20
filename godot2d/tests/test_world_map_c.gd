extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
var t=Support.new()
func _initialize()->void:call_deferred("run")
func key(map,code:int,shift:bool=false)->void:
	var event:=InputEventKey.new()
	event.physical_keycode=code
	event.pressed=true
	event.shift_pressed=shift
	map._input(event)
func run()->void:
	var world=load("res://scenes/harbor.tscn").instantiate()
	world.set_meta("save_directory",t.temporary_directory("map-single"))
	world.set_meta("journal_test",true)
	world.set_meta("skip_verification",true)
	root.add_child(world)
	t.check("new_game",world.start_new_game("海湾地图"))
	var map=world.world_map
	map.open()
	t.check("right_detail_removed",not map.has_node("Root/Panel/Detail"))
	t.check("resource_controls_removed",not map.has_node("Root/Panel/Resources"))
	t.check("divider_removed",not map.has_node("Root/Panel/Divider"))
	t.check("no_scene_snapshot",map.find_children("*","SubViewport",true,false).is_empty())
	if not t.passed():
		map.close()
		world.queue_free()
		await process_frame
		finish()
		return
	t.check("default_actual_region",map.selected_region=="harbor")
	t.check("paused",paused and map.visible)
	t.check("five_regions",map.region_buttons.size()==5)
	var before:Dictionary=world.foraging.to_data(world.player.position)
	for region in ["harbor_district","hillside","residential_lane","cape_coast"]:
		map.select_region(region)
		t.check(region+"_selectable",map.selected_region==region and map.region_buttons[region].button_pressed)
	t.check("actual_region_still_marked",map.region_buttons.harbor.text.contains("你在这里") and not map.region_buttons.cape_coast.text.contains("你在这里"))
	map.select_region("not_a_region")
	t.check("invalid_region_ignored",map.selected_region=="cape_coast")
	map.select_region("harbor")
	key(map,KEY_TAB)
	t.check("tab_close",root.gui_get_focus_owner()==map.get_node("Root/Panel/Close"))
	key(map,KEY_TAB)
	t.check("tab_wrap",root.gui_get_focus_owner()==map.region_buttons.harbor)
	key(map,KEY_TAB,true)
	t.check("reverse_tab_close",root.gui_get_focus_owner()==map.get_node("Root/Panel/Close"))
	map.region_buttons.harbor.grab_focus()
	key(map,KEY_W)
	t.check("direction_selects_district",map.selected_region=="harbor_district")
	key(map,KEY_E)
	t.check("E_keeps_region_selected",map.selected_region=="harbor_district" and map.region_buttons.harbor_district.button_pressed)
	t.check("pause_state_unchanged",world.foraging.to_data(world.player.position)==before and not world.regions.travel())
	key(map,KEY_ESCAPE)
	t.check("escape_closes_directly",not map.visible and not paused and world.release_input)
	world.foraging.location="house"
	map.open()
	t.check("house_default_harbor",map.selected_region=="harbor" and map.region_buttons.harbor.text.contains("屋内"))
	key(map,KEY_B)
	t.check("B_closes_directly",not map.visible and not paused)
	map.open()
	key(map,KEY_M)
	t.check("M_closes_directly",not map.visible and not paused)
	map.open()
	t.check("reopen_resets_current_region",map.selected_region=="harbor")
	map.close()
	world.queue_free()
	await process_frame
	finish()
func finish()->void:
	print("WORLD_MAP_SINGLE checks=",t.checks.size()," passed=",t.passed())
	quit(0 if t.passed() else 1)
