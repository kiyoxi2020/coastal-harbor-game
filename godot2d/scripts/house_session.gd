extends Node
const Room=preload("res://scripts/room_data.gd")
var world
var outdoor: Node2D
var interior
var exterior_door
var transition
func _ready() -> void:
	outdoor=Node2D.new()
	outdoor.name="HarborExterior"
	world.add_child(outdoor)
	world.move_child(outdoor,0)
	# Preserve the existing sort layer and its references for outdoor regressions.
	for child in world.get_children():
		if child==world.sort_layer or child.name=="Terrain" or child is StaticBody2D:
			child.reparent(outdoor)
	var house=world.sort_layer.get_node("House")
	house.get_child(0).hide()
	house.set_script(preload("res://scripts/house_exterior.gd"))
	house.z_index=0
	house._ready()
	exterior_door=Node2D.new()
	exterior_door.set_script(preload("res://scripts/interactive_door.gd"))
	exterior_door.name="ExteriorDoor"
	exterior_door.position=Room.OUTSIDE_DOOR
	exterior_door.approach=Room.OUTSIDE_APPROACH
	exterior_door.entrance_normal=Room.OUTSIDE_ENTRANCE_NORMAL
	exterior_door.z_index=0
	world.sort_layer.add_child(exterior_door)
	interior=Node2D.new()
	interior.set_script(preload("res://scripts/house_interior.gd"))
	interior.name="HouseInterior"
	world.add_child(interior)
	interior.hide()
	interior.process_mode=Node.PROCESS_MODE_DISABLED
	transition=Node.new()
	transition.set_script(preload("res://scripts/room_transition.gd"))
	transition.home=self
	add_child(transition)
func active_door():
	return interior.door if world.foraging.location=="house" else exterior_door
func switch_room(location: String,point: Vector2,transient: bool=false) -> bool:
	if location not in ["harbor","house"]: return false
	var inside:=location=="house"
	if inside and not is_instance_valid(interior): return false
	# Reparent before disabling the source so the one persistent player stays live.
	world.player.reparent(interior.sort_layer if inside else world.sort_layer)
	outdoor.visible=not inside
	outdoor.process_mode=Node.PROCESS_MODE_DISABLED if inside else Node.PROCESS_MODE_INHERIT
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
	world.hud.region.text="旧屋 / 海风入窗" if inside else "晴 / 渔港的一天"
	world.hud.controls.text="WASD / 方向键 移动   E 查看 / 开门   B / Tab 手账   R 回入口" if inside else "WASD / 方向键 移动   E 拾取 / 查看   B / Tab 手账   R 回路口"
	world.get_node("WorldCamera").update_position()
	world.get_node("WorldCamera").force_update_scroll()
	world.refresh_pickups()
	return true
func safe_position(location: String,point: Vector2) -> Vector2:
	var inside:=location=="house"
	var bounds: Rect2=Room.FLOOR if inside else world.data.WORLD_BOUNDS
	var fallback: Vector2=Room.SPAWN if inside else world.data.SPAWN
	if not bounds.grow(-6).has_point(point): return fallback
	var blocks: Array[Rect2]=Room.blockers() if inside else world.data.blockers()
	for rect in blocks:
		if rect.grow(6).has_point(point): return fallback
	var door_position: Vector2=Room.DOOR if inside else Room.OUTSIDE_DOOR
	if inside:
		if Rect2(door_position-Vector2(20,16),Vector2(40,40)).has_point(point): return fallback
	elif Rect2(door_position-Vector2(24,10),Vector2(48,20)).has_point(point): return fallback
	return point
func storage_point() -> Vector2:
	return Room.STORAGE+Vector2(0,24) if world.foraging.location=="house" else world.STORAGE_POINT
func reset_player() -> void:
	world.player.reset_doorway_visual()
	world.player.position=Room.SPAWN if world.foraging.location=="house" else world.data.SPAWN
	world.player.velocity=Vector2.ZERO
	world.hud.dismiss()
