extends Node2D
const Data=preload("res://scripts/room_data.gd")
var sort_layer: Node2D
var door
func _ready() -> void:
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	sort_layer=Node2D.new()
	sort_layer.y_sort_enabled=true
	sort_layer.z_index=0
	add_child(sort_layer)
	for item in Data.furniture():
		var node:=Node2D.new()
		node.set_script(preload("res://scripts/house_furniture.gd"))
		node.kind=item.id
		node.name=item.id.capitalize()
		node.extent=item.rect.size
		node.position=Vector2(item.rect.get_center().x,item.rect.end.y)
		sort_layer.add_child(node)
	for rect in Data.blockers():
		var body:=StaticBody2D.new()
		var shape:=CollisionShape2D.new()
		var box:=RectangleShape2D.new()
		box.size=rect.size
		shape.shape=box
		body.position=rect.get_center()
		body.add_child(shape)
		add_child(body)
	door=Node2D.new()
	door.set_script(preload("res://scripts/interactive_door.gd"))
	door.name="InteriorDoor"
	door.position=Data.DOOR
	door.approach=Data.SPAWN
	door.inside=true
	door.entrance_normal=Data.ENTRANCE_NORMAL
	sort_layer.add_child(door)

func block(r: Rect2,c: String) -> void:
	draw_rect(r,Color(c))
func _draw() -> void:
	block(Rect2(-200,-200,1040,900),"183039")
	block(Data.FLOOR.grow(8),"493e35")
	block(Data.FLOOR,"b08b5b")
	for row in range(13):
		for column in range(7):
			var x:=176+column*48-(24 if row%2 else 0)
			var rect:=Rect2(x,112+row*16,46,14).intersection(Data.FLOOR)
			if rect.size.x>0: block(rect,["c19b69","c8a573","b99565","bc9766"][(row*7+column*3)%4])
	# North wall leaves the central aperture clear; southern edge is continuous.
	block(Rect2(176,68,124,60),"e2d5b2")
	block(Rect2(340,68,124,60),"e2d5b2")
	block(Rect2(176,116,124,12),"467375")
	block(Rect2(340,116,124,12),"467375")
	block(Rect2(172,112,4,208),"65796a")
	block(Rect2(464,112,4,208),"65796a")
	block(Rect2(176,320,288,7),"6b5c44")
	block(Rect2(280,204,72,64),"547e7e")
	block(Rect2(284,208,64,56),"92ada0")
	block(Rect2(192,228,48,16),"b46f51")
