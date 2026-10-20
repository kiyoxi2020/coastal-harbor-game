extends SceneTree
const State=preload("res://scripts/player_state.gd")
const Support=preload("res://tests/life_test_support.gd")
var t=Support.new()
func _initialize()->void:call_deferred("run")
func run()->void:
	t.check("version5",State.SAVE_VERSION==5)
	t.check("registry_exists",ResourceLoader.exists("res://scripts/region_catalog.gd"))
	t.check("session_exists",ResourceLoader.exists("res://scripts/region_session.gd"))
	var legacy=JSON.parse_string(FileAccess.get_file_as_string("res://tests/fixtures/life_save_v4.json"))
	var district:Dictionary=legacy.duplicate(true)
	district.version=5
	district.location="harbor_district"
	district.position=[320,350]
	t.check("v5_district_valid",State.valid_data(district))
	var original:Dictionary=district.duplicate(true)
	district.life.wallet=-1
	t.check("corrupt_v5_rejected",not State.valid_data(district))
	district=original
	district.version=4
	t.check("v4_location_frozen",not State.valid_data(district))
	district.version=5
	district.location="unknown"
	t.check("unknown_rejected",not State.valid_data(district))
	if not t.passed():finish();return
	var catalog=load("res://scripts/region_catalog.gd")
	t.check("future_region_not_open",not catalog.open_regions().has("hillside"))
	t.check("two_open_regions",catalog.open_regions().size()==2)
	t.check("six_resources",catalog.points().filter(func(p):return p.kind=="resource").size()==6)
	var migrated:Dictionary=State.migrate_data(legacy)
	t.check("migration_preserves",migrated.version==5 and migrated.life==legacy.life and migrated.bag==legacy.bag and migrated.position==legacy.position and legacy.version==4)
	var world=load("res://scenes/harbor.tscn").instantiate()
	world.set_meta("save_directory",t.temporary_directory("map-test"))
	world.set_meta("journal_test",true)
	world.set_meta("skip_verification",true)
	root.add_child(world)
	t.check("new_game",world.start_new_game("分区测试"))
	world.release_input=false
	var before:Dictionary=world.foraging.to_data(world.player.position)
	t.check("far_exit_denied",not world.regions.travel() and world.foraging.to_data(world.player.position)==before)
	world.player.position=Vector2(320,64)
	before=world.foraging.to_data(world.player.position)
	var real=world.save_service
	world.save_service=FailSave.new()
	t.check("failed_travel_atomic",not world.regions.travel() and world.foraging.to_data(world.player.position)==before and world.exterior.visible)
	world.save_service=real
	world.release_input=false
	t.check("travel_success",world.regions.travel() and world.foraging.location=="harbor_district")
	t.check("single_player",world.player.get_parent()==world.get_node("HarborDistrict/DepthSortedObjects") and not world.exterior.visible and world.get_node("HarborDistrict").visible)
	t.check("no_economy_change",world.foraging.life==before.life and world.foraging.bag.snapshot()==before.bag)
	t.check("save_destination",real.read_save().data.location=="harbor_district")
	t.check("continue_destination",world.continue_game() and world.foraging.location=="harbor_district" and world.player.position==Vector2(320,350))
	world.release_input=false
	world.player.position=Vector2(320,380)
	t.check("return",world.regions.travel() and world.foraging.location=="harbor" and world.player.position==Vector2(320,94))
	world.world_map.open()
	t.check("map_pause",world.world_map.visible and paused)
	t.check("no_travel_from_map",not world.regions.travel())
	var snapshot:Dictionary=world.foraging.to_data(world.player.position)
	t.check("no_action_from_map",not world.perform_action("hoe",{"cell_id":"garden_a:0:0"},1).ok and world.foraging.to_data(world.player.position)==snapshot)
	t.check("map_all_points",world.world_map.markers.size()==15)
	world.world_map.get_node("Root/Panel/Resources").button_pressed=false
	t.check("resource_filter",world.world_map.markers.size()==9)
	world.world_map.get_node("Root/Panel/Resources").button_pressed=true
	world.foraging.collected["clam_a"]=true
	world.world_map.render()
	t.check("resource_live_state",world.world_map.markers.filter(func(p):return p.id=="clam_a")[0].collected)
	var marker=world.get_node("HarborDistrict/InteractPoints/restaurant")
	var point:Vector2=marker.position
	marker.position+=Vector2(4,0)
	t.check("scene_poi_source",catalog.points(world).filter(func(p):return p.id=="restaurant")[0].point==marker.position)
	marker.position=point
	world.world_map.close()
	t.check("map_close",not world.world_map.visible and not paused and world.release_input)
	world.queue_free()
	await process_frame
	finish()
class FailSave extends RefCounted:
	var last_error:="故障夹具"
	func write_save(_value:Dictionary)->bool:return false
func finish()->void:
	print("REGION_MAP checks=",t.checks.size()," passed=",t.passed())
	quit(0 if t.passed() else 1)
