@tool
extends Control

@export_group("Palette")
@export var strap_dark_color := Color("463d31")
@export var strap_light_color := Color("d4ac6a")
@export var outline_color := Color("483c32")
@export var body_shadow_color := Color("986137")
@export var body_color := Color("c28a50")
@export var body_highlight_color := Color("e0b777")
@export var seam_color := Color("74482f")
@export var pocket_shadow_color := Color("694631")
@export var pocket_color := Color("ac7743")
@export var buckle_dark_color := Color("523e2d")
@export var buckle_light_color := Color("ffe0a0")
@export var edge_light_color := Color("e4b977")
@export var edge_dark_color := Color("734b31")

func _draw() -> void:
	var scale_factor := minf(size.x/32.0,size.y/32.0)
	draw_set_transform((size-Vector2(32,32)*scale_factor)/2,0,Vector2.ONE*scale_factor)
	var pieces := [
		[Rect2(11,2,10,5),strap_dark_color],[Rect2(13,4,6,4),strap_light_color],
		[Rect2(7,7,18,22),outline_color],[Rect2(5,11,22,15),outline_color],
		[Rect2(7,10,18,16),body_shadow_color],[Rect2(9,8,14,18),body_color],
		[Rect2(9,9,14,8),body_highlight_color],[Rect2(9,17,14,2),seam_color],
		[Rect2(10,21,12,6),pocket_shadow_color],[Rect2(11,21,10,4),pocket_color],
		[Rect2(14,15,4,7),buckle_dark_color],[Rect2(15,16,2,3),buckle_light_color],
		[Rect2(7,12,2,11),edge_light_color],[Rect2(23,12,2,11),edge_dark_color]]
	for piece in pieces:
		draw_rect(piece[0],piece[1])
