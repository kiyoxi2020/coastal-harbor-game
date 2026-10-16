extends RefCounted
const FLOOR := Rect2(176,112,288,208)
const SPAWN := Vector2(320,288)
const DOOR := Vector2(320,320)
const ENTRANCE_NORMAL := Vector2.UP
const OUTSIDE_ENTRANCE_NORMAL := Vector2.DOWN
const STORAGE := Vector2(416,282)
const OUTSIDE_APPROACH := Vector2(209,194)
const OUTSIDE_DOOR := Vector2(209,165)

static func _default_interior():
	var packed := load("res://scenes/world/house_interior.tscn") as PackedScene
	return packed.instantiate() if packed != null else null

static func furniture(source = null) -> Array[Dictionary]:
	var interior = source if source != null else _default_interior()
	if interior == null:
		return []
	var result: Array[Dictionary] = interior.furniture_entries()
	if source == null:
		interior.free()
	return result

static func blockers(source = null) -> Array[Rect2]:
	var interior = source if source != null else _default_interior()
	if interior == null:
		return []
	var result: Array[Rect2] = interior.blockers()
	if source == null:
		interior.free()
	return result

static func locations(source = null) -> Array[Dictionary]:
	var interior = source if source != null else _default_interior()
	if interior == null:
		return []
	var result: Array[Dictionary] = interior.locations()
	if source == null:
		interior.free()
	return result
