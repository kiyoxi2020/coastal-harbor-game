extends Node2D

@export var kind := "bed"
@export var art_id := ""
@export var layout_rect := Rect2()

var pilot_texture: Texture2D:
	get:
		var sprite := get_node_or_null("Sprite2D") as Sprite2D
		return sprite.texture if sprite != null else null

var pilot_pivot: Vector2:
	get:
		var sprite := get_node_or_null("Sprite2D") as Sprite2D
		return -sprite.position if sprite != null else Vector2.ZERO

func layout_entry() -> Dictionary:
	var result := {"id": kind, "rect": layout_rect}
	if not art_id.is_empty() and art_id != kind:
		result.art = art_id
	var shape := get_node_or_null("BaseCollision/CollisionShape2D") as CollisionShape2D
	if shape != null and not shape.disabled and shape.shape is RectangleShape2D:
		var size := (shape.shape as RectangleShape2D).size
		var interior := get_parent().get_parent() as Node2D
		var center := interior.to_local(shape.to_global(Vector2.ZERO))
		result.base = Rect2(center - size / 2.0, size)
	return result
