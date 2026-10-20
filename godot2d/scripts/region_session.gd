extends Node
const Catalog=preload("res://scripts/region_catalog.gd")
var world
func initialize(value)->void:world=value
func active_scene()->Node2D:
	if world.foraging.location=="house":return world.home.interior
	return world.get_node("HarborDistrict") if world.foraging.location=="harbor_district" else world.exterior
func nearby_exit()->Dictionary:
	var e:=Catalog.exit_for(world.foraging.location,world)
	if e.is_empty() or world.player.position.distance_to(e.point)>22:return {}
	return e
func travel()->bool:
	if not world.session_started or world.release_input or world.home.transition.busy or world.journal.mode!="" or world.world_map.visible or world.player.action_busy:return false
	var e:=nearby_exit()
	if e.is_empty():return false
	var destination:Node2D=world.get_node("HarborDistrict") if e.target=="harbor_district" else world.exterior
	if destination.safe_position(e.spawn)!=e.spawn:
		world.hud.show_toast("目的地暂时无法通行。")
		return false
	var candidate:Dictionary=world.foraging.to_data(e.spawn)
	candidate.location=e.target
	# Publish only after destination state is durable. No date or action seq change.
	if not world.save_service.write_save(candidate):
		world.hud.show_toast(world.save_service.last_error)
		return false
	world.home.switch_room(e.target,e.spawn)
	world.release_input=true
	world.hud.show_toast(("已到达港口街区" if e.target=="harbor_district" else "已回到旧屋海港")+" · M 查看全镇地图",3)
	return true
