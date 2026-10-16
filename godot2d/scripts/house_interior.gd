extends Node2D

@export var floor_rect := Rect2(176, 112, 288, 208)

@onready var sort_layer: Node2D = $Furniture
@onready var door = $Furniture/InteriorDoor

var floor_texture: Texture2D:
	get: return ($StaticArt/Floor as Sprite2D).texture
var wall_texture: Texture2D:
	get: return ($StaticArt/NorthWall as Sprite2D).texture
var rug_texture: Texture2D:
	get: return ($StaticArt/Rug as Sprite2D).texture
var bed_rug_texture: Texture2D:
	get: return ($StaticArt/BedRug as Sprite2D).texture

func spawn_point() -> Vector2:
	return $Spawn.position

func storage_point() -> Vector2:
	return $Storage.position

func locations() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for marker in $InteractPoints.get_children():
		if marker is Marker2D:
			result.append({"id": marker.name, "point": marker.position,
				"title": marker.get_meta("title", ""), "body": marker.get_meta("body", "")})
	return result

func furniture_entries() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for item in $Furniture.get_children():
		if item.has_method("layout_entry"):
			result.append(item.layout_entry())
	return result

func _rect_for(shape: CollisionShape2D) -> Rect2:
	var size := (shape.shape as RectangleShape2D).size
	var center := to_local(shape.to_global(Vector2.ZERO))
	return Rect2(center - size / 2.0, size)

func blockers() -> Array[Rect2]:
	var result: Array[Rect2] = []
	for root_node in [$StaticCollisions, $Furniture]:
		for node in root_node.find_children("*", "CollisionShape2D", true, false):
			var shape := node as CollisionShape2D
			if shape != null and not shape.disabled and shape.shape is RectangleShape2D:
				result.append(_rect_for(shape))
	return result

func safe_position(point: Vector2) -> Vector2:
	var fallback := spawn_point()
	if not floor_rect.grow(-6).has_point(point):
		return fallback
	for rect in blockers():
		if rect.grow(6).has_point(point):
			return fallback
	if Rect2(door.position - Vector2(20, 16), Vector2(40, 40)).has_point(point):
		return fallback
	return point
