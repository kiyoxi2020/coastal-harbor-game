extends Node
const State = preload("res://scripts/player_state.gd")
var world
var outdoor: Node2D
var interior
var exterior_door
var transition
func initialize(world_ref, outdoor_ref: Node2D, interior_ref: Node2D, exterior_door_ref: Node2D, transition_ref: CanvasLayer) -> void:
	world = world_ref
	outdoor = outdoor_ref
	interior = interior_ref
	exterior_door = exterior_door_ref
	transition = transition_ref
	transition.initialize(self)
func active_door():
	return interior.door if world.foraging.location=="house" else exterior_door
func switch_room(location: String,point: Vector2,transient: bool=false) -> bool:
	if location not in ["harbor","house","harbor_district"]: return false
	var inside:=location=="house"
	if inside and not is_instance_valid(interior): return false
	# Reparent before disabling the source so the one persistent player stays live.
	var district:bool=location=="harbor_district"
	var district_scene:Node2D=world.get_node("HarborDistrict")
	world.player.reparent(interior.sort_layer if inside else (district_scene.get_node("DepthSortedObjects") if district else world.sort_layer))
	district_scene.visible=district
	district_scene.process_mode=Node.PROCESS_MODE_INHERIT if district else Node.PROCESS_MODE_DISABLED
	outdoor.visible=not inside and not district
	outdoor.process_mode=Node.PROCESS_MODE_DISABLED if inside or district else Node.PROCESS_MODE_INHERIT
	if is_instance_valid(interior):
		interior.visible=inside
		interior.process_mode=Node.PROCESS_MODE_INHERIT if inside else Node.PROCESS_MODE_DISABLED
	world.foraging.location=location
	exterior_door.set_pose(0)
	if is_instance_valid(interior): interior.door.set_pose(0)
	world.player.position=point if transient else safe_position(location,point)
	world.player.velocity=Vector2.ZERO
	world.player.reset_doorway_visual()
	world.hud.dismiss()
	world.hud.region.text="旧屋 / 海风入窗" if inside else ("港口街区 / 海风石巷" if district else "晴 / 渔港的一天")
	world.hud.controls.text="WASD 移动   Shift 跑步   E 查看 / 开门   M 地图   B 手账   R 回入口" if inside else ("WASD 移动   Shift 跑步   E 查看   M 地图   B 手账   R 回街口" if district else "WASD 移动   Shift 跑步   Tab 换工具   E 操作   M 地图   B 手账   R 回路口")
	world.get_node("FarmTools").visible=location=="harbor"
	world.get_node("WorldCamera").update_position()
	world.get_node("WorldCamera").force_update_scroll()
	world.refresh_pickups()
	return true
func safe_position(location: String,point: Vector2) -> Vector2:
	return State.safe_position(location, point, interior if location == "house" else (world.get_node("HarborDistrict") if location=="harbor_district" else outdoor))
func storage_point() -> Vector2:
	return interior.storage_point() if world.foraging.location=="house" else Vector2.INF
func reset_player() -> void:
	world.player.reset_doorway_visual()
	world.player.position=world.regions.active_scene().spawn_point()
	world.player.velocity=Vector2.ZERO
	world.hud.dismiss()
