extends Node2D
# Only fixed foreground trim occludes the actor; the open aperture stays clear.
var width:=38.0
var height:=54.0
func _draw() -> void:
	draw_rect(Rect2(-width/2,-height,3,height),Color("769185"))
	draw_rect(Rect2(width/2-3,-height,3,height),Color("769185"))
	draw_rect(Rect2(-width/2,-height,width,3),Color("a9b9a0"))
