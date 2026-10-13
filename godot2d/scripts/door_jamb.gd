extends Node2D
# Only fixed foreground trim occludes the actor; the open aperture stays clear.
var width:=38.0
var height:=54.0
func _draw() -> void:
	var trim:=4.0
	draw_rect(Rect2(-width/2,-height,trim,height),Color("769185"))
	draw_rect(Rect2(width/2-trim,-height,trim,height),Color("769185"))
	draw_rect(Rect2(-width/2,-height,width,2),Color("a9b9a0"))
