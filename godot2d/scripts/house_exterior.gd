extends Node2D
# Draw the existing atlas in non-overlapping pieces, omitting the old leaf.
# Pixel coordinates are source-atlas coordinates, not destructive image edits.
const REGION := Rect2(34,91,488,448)
const HOLE := Rect2(347,382,63,84)
const FACTOR := 168.0/488.0
var texture: Texture2D
func _ready() -> void:
	texture=load("res://assets/environment.png")
	set_meta("door_cutout",true)
	queue_redraw()
func part(source: Rect2) -> void:
	var point: Vector2=(source.position-REGION.position)*FACTOR+Vector2(-84,-448*FACTOR)
	draw_texture_rect_region(texture,Rect2(point,source.size*FACTOR),source)
func _draw() -> void:
	if not texture: return
	part(Rect2(REGION.position,Vector2(REGION.size.x,HOLE.position.y-REGION.position.y)))
	part(Rect2(REGION.position.x,HOLE.position.y,HOLE.position.x-REGION.position.x,HOLE.size.y))
	part(Rect2(HOLE.end.x,HOLE.position.y,REGION.end.x-HOLE.end.x,HOLE.size.y))
	part(Rect2(REGION.position.x,HOLE.end.y,REGION.size.x,REGION.end.y-HOLE.end.y))
