extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
var s:=Support.new()
class FailedSave extends RefCounted:
	func write_save(_value: Dictionary) -> bool: return false
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var w=load("res://scenes/harbor.tscn").instantiate()
	w.set_meta("journal_test",true)
	w.set_meta("skip_verification",true)
	w.set_meta("save_directory",s.temporary_directory("polish"))
	root.add_child(w)
	w.start_new_game("修订")
	await process_frame
	await process_frame
	var a=w.sort_layer.get_node("GardenA")
	w.release_input=false
	w.player.global_position=w.farm_cell("garden_a:0:0").point
	w.perform_action("hoe",{"cell_id":"garden_a:0:0"},1)
	var soil=a.get_node("Cell00/Soil") as Sprite2D
	s.check("detailed_soil",soil.texture.get_width()>=128 and is_equal_approx(soil.texture.get_width()*soil.scale.x,16))
	s.check("icon_toolbar",w.get_node("FarmTools/Panel/Tools/Hoe").icon!=null)
	s.check("tab_not_journal",InputMap.action_get_events("journal").all(func(e):return not e is InputEventKey or e.physical_keycode!=KEY_TAB))
	s.check("outside_crate_deleted",not w.sort_layer.has_node("StorageCrates"))
	s.check("no_ghost_storage",not w.exterior.storage_point().is_finite())
	s.check("terrain_surface_api",w.exterior.has_method("can_cultivate"))
	if w.exterior.has_method("can_cultivate"):
		for id in preload("res://scripts/simulation/state_schema.gd").cell_ids():
			s.check("grass_cell_"+id,w.exterior.can_cultivate(w.farm_cell(id).point))
		s.check("grass_allowed",w.exterior.can_cultivate(Vector2(102,200)))
		s.check("stone_denied",not w.exterior.can_cultivate(Vector2(296,200)))
		s.check("partial_road_denied",not w.exterior.can_cultivate(Vector2(270,200)))
		a.position=Vector2(320,224)
		w.player.position=Vector2(296,200)
		var before: Dictionary=w.foraging.to_data(w.player.position)
		var r: Dictionary=w.perform_action("hoe",{"cell_id":"garden_a:0:0"},2)
		s.check("moved_region_on_road_denied",not r.ok and before==w.foraging.to_data(w.player.position))
		a.position=Vector2(84,224)
	s.check("character_action_api",w.player.has_method("play_tool_action"))
	if w.player.has_method("play_tool_action"):
		w.player.global_position=w.farm_cell("garden_a:1:0").point
		var service=w.action_service
		w.action_service=preload("res://scripts/simulation/action_service.gd").new(FailedSave.new())
		var before: Dictionary=w.foraging.to_data(w.player.position)
		s.check("failed_save_fixture_reachable",w._can_perform_action("hoe",{"cell_id":"garden_a:1:0"}))
		w.use_farm_tool(w.farm_cell("garden_a:1:0"))
		s.check("failed_save_no_animation",not w.player.action_busy and before==w.foraging.to_data(w.player.position))
		w.action_service=service
		var foot: Vector2=w.player.position
		w.player.play_tool_action("hoe",Vector2(118,200))
		s.check("action_busy",w.player.action_busy)
		var r: Dictionary=w.perform_action("hoe",{"cell_id":"garden_a:1:0"},2)
		s.check("busy_no_repeat",not r.ok)
		await create_timer(0.8).timeout
		s.check("action_finishes_fixed_feet",not w.player.action_busy and w.player.position==foot and w.player.sprite.visible)
	w.queue_free()
	await process_frame
	print("FARMING_POLISH checks=",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
