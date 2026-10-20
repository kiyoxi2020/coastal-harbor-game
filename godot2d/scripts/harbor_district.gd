extends Node2D

@export var world_bounds := Rect2(0, 0, 640, 416)

func spawn_point() -> Vector2:
	return $Spawn.position

func storage_point() -> Vector2:
	return Vector2.INF

func locations() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for marker in $InteractPoints.get_children():
		if marker is Marker2D:
			result.append({"id": String(marker.name), "point": marker.position,
				"title": marker.get_meta("title", ""), "body": marker.get_meta("body", "")})
	return result

func safe_position(point: Vector2) -> Vector2:
	if not point.is_finite() or not world_bounds.grow(-6).has_point(point):
		return spawn_point()
	for collider in find_children("*", "CollisionShape2D", true, false):
		if collider.get_parent() is StaticBody2D and not collider.disabled and collider.shape is RectangleShape2D:
			var extent: Vector2 = collider.shape.size * collider.global_scale.abs()
			var center := to_local(collider.global_position)
			if Rect2(center - extent / 2.0, extent).grow(6).has_point(point):
				return spawn_point()
	return point
