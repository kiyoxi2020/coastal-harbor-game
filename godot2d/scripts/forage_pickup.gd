extends Node2D

var kind := "clam"
var highlighted := false:
	set(value):
		if highlighted != value:
			highlighted = value
			queue_redraw()

func _draw() -> void:
	draw_rect(Rect2(-6,0,12,3),Color("a48a68"))
	if highlighted:
		draw_rect(Rect2(-9,-10,18,16),Color("fff0cb"),false,1)
	match kind:
		"clam":
			draw_rect(Rect2(-6,-4,12,5),Color("775b58"))
			draw_rect(Rect2(-5,-7,10,5),Color("dba398"))
			draw_rect(Rect2(-3,-8,6,2),Color("ffe0b8"))
			for x in [-3,0,3]:
				draw_rect(Rect2(x,-6,1,4),Color("f3c8ae"))
		"snail":
			draw_rect(Rect2(-5,-6,10,7),Color("8a664f"))
			draw_rect(Rect2(-4,-8,7,7),Color("e4bd7f"))
			draw_rect(Rect2(-2,-6,4,4),Color("b28456"))
			draw_rect(Rect2(-1,-5,2,2),Color("f6dca4"))
			draw_rect(Rect2(4,-2,3,3),Color("f6dca4"))
		"kelp":
			for i in range(3):
				var x := -5+i*4
				draw_rect(Rect2(x,-8+i,3,9-i),Color("38695b"))
				draw_rect(Rect2(x-1,-5+i,2,4),Color("689473"))
				draw_rect(Rect2(x,-8+i,2,2),Color("91b38a"))
