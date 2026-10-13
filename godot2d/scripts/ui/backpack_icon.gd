extends Control

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE

func _draw() -> void:
	var scale_factor := minf(size.x/32.0,size.y/32.0)
	draw_set_transform((size-Vector2(32,32)*scale_factor)/2,0,Vector2.ONE*scale_factor)
	var pieces := [
		[Rect2(11,2,10,5),"463d31"],[Rect2(13,4,6,4),"d4ac6a"],
		[Rect2(7,7,18,22),"483c32"],[Rect2(5,11,22,15),"483c32"],
		[Rect2(7,10,18,16),"986137"],[Rect2(9,8,14,18),"c28a50"],
		[Rect2(9,9,14,8),"e0b777"],[Rect2(9,17,14,2),"74482f"],
		[Rect2(10,21,12,6),"694631"],[Rect2(11,21,10,4),"ac7743"],
		[Rect2(14,15,4,7),"523e2d"],[Rect2(15,16,2,3),"ffe0a0"],
		[Rect2(7,12,2,11),"e4b977"],[Rect2(23,12,2,11),"734b31"]]
	for piece in pieces:
		draw_rect(piece[0],Color(piece[1]))
