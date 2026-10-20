extends SceneTree
const Catalog=preload("res://scripts/region_catalog.gd")
var checks:Dictionary={}
func check(id:String,value:bool)->void:
	checks[id]=value
	print(("PASS " if value else "FAIL ")+id)
func _initialize()->void:call_deferred("run")
func run()->void:
	var origin:Vector2=Catalog.project("harbor",Vector2.ZERO)
	var x:Vector2=Catalog.project("harbor",Vector2(100,0))-origin
	var y:Vector2=Catalog.project("harbor",Vector2(0,100))-origin
	check("uniform_scale",is_equal_approx(x.length(),y.length()))
	var world=load("res://scenes/harbor.tscn").instantiate()
	world.set_meta("save_directory","/private/tmp/coastal-map-projection-save")
	world.set_meta("journal_test",true)
	world.set_meta("skip_verification",true)
	root.add_child(world)
	check("scene_snapshot_api",world.world_map.has_method("snapshot_scene"))
	if not checks.values().has(false):
		world.start_new_game("地图比例")
		world.world_map.open()
		check("two_scene_views",world.world_map.scene_views.size()==2)
		for region in Catalog.open_regions():
			var scene:Node2D=world.exterior if region=="harbor" else world.get_node("HarborDistrict")
			var view:SubViewport=world.world_map.scene_views[region]
			check(region+"_world_bounds",view.size==Vector2i(scene.world_bounds.size))
			check(region+"_no_player",view.find_children("*","CharacterBody2D",true,false).is_empty())
			check(region+"_no_collision",view.find_children("*","CollisionObject2D",true,false).is_empty())
			check(region+"_own_world",view.world_2d!=world.get_world_2d())
			var preview:TextureRect=world.world_map.get_node("Root/Panel/Map/View_"+region)
			check(region+"_display_scale",preview.size*preview.scale==scene.world_bounds.size*0.5)
		var source:Sprite2D=world.get_node("HarborDistrict/DepthSortedObjects/Restaurant/Sprite")
		source.scale=Vector2(.6,.6)
		source.position+=Vector2(3,2)
		world.world_map.render()
		var copy:Sprite2D=world.world_map.scene_views.harbor_district.get_node("Scene/DepthSortedObjects/Restaurant/Sprite")
		check("scene_edits_mirrored",copy.transform==source.transform and copy.texture==source.texture)
		check("copy_has_no_scripts",copy.get_script()==null)
		var parent:Node2D=world.get_node("HarborDistrict/InteractPoints")
		parent.position=Vector2(8,5)
		var poi:Dictionary=Catalog.points(world).filter(func(item):return item.id=="restaurant")[0]
		check("nested_transform_source",poi.point==world.get_node("HarborDistrict").to_local(parent.get_node("restaurant").global_position))
		world.world_map.close()
	world.queue_free()
	await process_frame
	print("MAP_PROJECTION checks=",checks.size()," passed=",not checks.values().has(false))
	quit(1 if checks.values().has(false) else 0)
