extends SceneTree
# The detail projection has been removed; validate the retained overview layout.
const Catalog=preload("res://scripts/region_catalog.gd")
var checks:Dictionary={}
func check(id:String,value:bool)->void:
	checks[id]=value
	print(("PASS " if value else "FAIL ")+id)
func _initialize()->void:call_deferred("run")
func run()->void:
	var world=load("res://scenes/harbor.tscn").instantiate()
	world.set_meta("save_directory","/private/tmp/coastal-map-single-layout-save")
	world.set_meta("journal_test",true)
	world.set_meta("skip_verification",true)
	root.add_child(world)
	world.start_new_game("地图布局")
	var map=world.world_map
	map.open()
	var panel:Control=map.get_node("Root/Panel")
	var overview:Control=panel.get_node("Overview")
	check("panel_centered",is_equal_approx(panel.position.x+panel.size.x/2,640.0))
	check("compact_single_column",panel.size.x==820.0)
	check("art_not_stretched",overview.size==Vector2(640,520) and overview.scale==Vector2.ONE and overview.get_node("Art").scale==Vector2.ONE)
	check("overview_centered",is_equal_approx(overview.position.x+overview.size.x/2,panel.size.x/2))
	check("no_detail",not panel.has_node("Detail") and not panel.has_node("Divider") and not panel.has_node("Resources"))
	for region in Catalog.regions():
		var button:Button=map.region_buttons[region.id]
		check(region.id+"_within_map",Rect2(Vector2.ZERO,overview.size).encloses(button.get_rect()))
	for name in ["Title","Date","Close","Overview","Legend","Info"]:
		check(name+"_inside_panel",Rect2(Vector2.ZERO,panel.size).encloses(panel.get_node(name).get_rect()))
	map.close()
	world.queue_free()
	await process_frame
	print("MAP_OVERVIEW_LAYOUT checks=",checks.size()," passed=",not checks.values().has(false))
	quit(1 if checks.values().has(false) else 0)
