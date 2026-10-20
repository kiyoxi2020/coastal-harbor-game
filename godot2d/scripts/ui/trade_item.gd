@tool
extends Control
@export var item_id: String="":
	set(value):
		item_id=value
		if is_node_ready():refresh()
@export var unavailable:=false:
	set(value):
		unavailable=value
		if is_node_ready():refresh()
const LETTUCE=preload("res://assets/farming-polish-v3/lettuce_mature.png")
const TOMATO=preload("res://assets/farming-polish-v3/tomato_mature.png")
func _ready():
	resized.connect(refresh)
	refresh()
func crop_texture() -> Texture2D:
	return TOMATO if item_id in ["tomato","tomato_seed"] else LETTUCE
func refresh():
	var forage=$Forage
	forage.visible=item_id in ["clam","snail","kelp"]
	if forage.visible:forage.kind=item_id
	forage.position=(size/2+Vector2(0,16)).round()
	modulate=Color(1,1,1,0.4) if unavailable else Color.WHITE
	queue_redraw()
func _draw():
	if item_id=="" or item_id in ["clam","snail","kelp"]:return
	var area=Rect2((size-Vector2(62,66))/2,Vector2(62,66))
	if item_id.ends_with("_seed"):
		draw_rect(area,Color("605640"))
		draw_rect(area.grow(-3),Color("d7b786"))
		draw_rect(Rect2(area.position+Vector2(3,4),Vector2(56,5)),Color("f4dfb1"))
		area=area.grow(-11)
	var texture=crop_texture()
	var ratio=minf(area.size.x/texture.get_width(),area.size.y/texture.get_height())
	var target=Vector2(texture.get_size())*ratio
	draw_texture_rect(texture,Rect2((size-target)/2,target),false)
