extends SceneTree
# Run against the isolated project after the native EditorPlugin saves GardenA at (330,224).
const Support = preload("res://tests/life_test_support.gd")
var s := Support.new()
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var w=load("res://scenes/harbor.tscn").instantiate()
	w.set_meta("journal_test",true)
	w.set_meta("skip_verification",true)
	w.set_meta("save_directory",s.temporary_directory("grid-editor-reload"))
	root.add_child(w)
	await process_frame
	var a=w.sort_layer.get_node("GardenA")
	s.check("editor_saved_position",a.position==Vector2(330,224))
	s.check("stable_identity",a.region_id=="garden_a")
	s.check("sixteen_static_cell_sprites",a.get_child_count()==8 and a.get_node("Cell00/Soil") is Sprite2D and a.get_node("Cell00/Crop") is Sprite2D)
	s.check("cell_follows_region",a.cell_center("garden_a:0:0")==Vector2(306,200))
	s.check("target_follows_region",a.cell_at(Vector2(306,200))=="garden_a:0:0" and a.cell_at(Vector2(102,200))=="")
	s.check("walkable_new_and_old",w.exterior.safe_position(Vector2(306,216))==Vector2(306,216) and w.exterior.safe_position(Vector2(102,216))==Vector2(102,216))
	s.check("background_retained",w.sort_layer.has_node("DaisiesWest") and w.sort_layer.get_node("DaisiesWest").texture!=null)
	w.start_new_game("移位验收")
	w.foraging.bag.add("lettuce_seed",1)
	await process_frame
	await process_frame
	w.release_input=false
	w.player.position=Vector2(102,216)
	var r: Dictionary=w.perform_action("hoe",{"cell_id":"garden_a:0:0"},1)
	s.check("old_point_rejected",not r.ok)
	w.player.position=Vector2(306,200)
	r=w.perform_action("hoe",{"cell_id":"garden_a:0:0"},1)
	s.check("new_point_can_hoe",r.ok and a.get_node("Cell00/Soil").visible)
	r=w.perform_action("plant",{"cell_id":"garden_a:0:0","crop_id":"lettuce"},2)
	s.check("plant_root_follows",r.ok and a.get_node("Cell00/Crop").global_position==Vector2(306,206) and a.get_node("Cell00/Crop").visible)
	w.queue_free()
	await process_frame
	print("GRID_EDITOR checks=",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
