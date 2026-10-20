extends Node2D

@export var world_bounds: Rect2
@export var foraging_area: Rect2

func locations() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var points := get_node_or_null("InteractPoints")
	if points == null:
		return result
	for marker in points.get_children():
		if marker is Marker2D:
			result.append({"id": marker.name, "point": marker.position,
				"title": marker.get_meta("title", ""), "body": marker.get_meta("body", "")})
	return result

func pickups() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var points := get_node_or_null("DepthSortedObjects/ForagePickups")
	if points == null:
		return result
	for pickup in points.get_children():
		result.append({"id": pickup.name, "kind": pickup.kind, "point": pickup.position})
	return result

func storage_point() -> Vector2:
	return Vector2.INF # Outdoor stack removed; storage remains in the house.

func spawn_point() -> Vector2:
	return $Spawn.position

func safe_position(point: Vector2) -> Vector2:
	if not world_bounds.grow(-6).has_point(point):
		return spawn_point()
	for shape in find_children("*", "CollisionShape2D", true, false):
		if shape.get_parent() is StaticBody2D and not shape.disabled and shape.shape is RectangleShape2D:
			var size: Vector2 = shape.shape.size
			var center := to_local(shape.global_position)
			var rect := Rect2(center - size / 2.0, size)
			if rect.grow(6).has_point(point):
				return spawn_point()
	var door := get_node_or_null("DepthSortedObjects/ExteriorDoor") as Node2D
	if door != null and Rect2(door.position - Vector2(24, 36), Vector2(48, 46)).has_point(point):
		return spawn_point()
	return point

# Consult the actual rendered scene rather than a duplicate hard-coded road map.
# A whole 16-unit cell must lie on grass and outside every stone tile.
func can_cultivate(global_center: Vector2) -> bool:
	var terrain := $Terrain
	var grass := $Terrain/GrassField as Sprite2D
	for y in [-7.9,0.0,7.9]:
		for x in [-7.9,0.0,7.9]:
			var point := global_center+Vector2(x,y)
			if not grass.get_rect().has_point(grass.to_local(point)): return false
			for tile in $Terrain/StonePaths.get_children():
				if tile is Sprite2D and tile.get_rect().has_point(tile.to_local(point)): return false
	return true
