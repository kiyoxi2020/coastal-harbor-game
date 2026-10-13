extends Node2D
const Data=preload("res://scripts/room_data.gd")
var sort_layer: Node2D
var door
func _ready() -> void:
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	sort_layer=Node2D.new()
	sort_layer.y_sort_enabled=true
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
	# Cutaway southern wall: the leaf is behind the actor, never hiding their feet.
	add_child(door)
	move_child(door,0)

func block(r: Rect2,c: String) -> void:
	draw_rect(r,Color(c))
func _draw() -> void:
	block(Rect2(-200,-200,1040,900),"183039")
	block(Rect2(72,42,496,318),"493e35")
	block(Data.FLOOR,"b08b5b")
	for row in range(18):
		for column in range(11):
			var x:=80+column*48-(24 if row%2 else 0)
			var rect:=Rect2(x,64+row*16,46,14).intersection(Data.FLOOR)
			if rect.size.x<=0: continue
			block(rect,["c19b69","c8a573","b99565","bc9766"][(row*7+column*3)%4])
			block(Rect2(rect.position+Vector2(4,4),Vector2(maxf(0,rect.size.x-10),1)),"d4b17d")
			if rect.size.x>20: block(Rect2(rect.position+Vector2(9,10),Vector2(9,1)),"aa8256")
	# Wallpaper, teal wainscoting, mullioned windows and sparse seaside ornaments.
	block(Rect2(80,50,480,46),"e2d5b2")
	for x in range(88,552,16): block(Rect2(x,53,1,29),"cec3a2")
	block(Rect2(80,84,480,12),"467375")
	block(Rect2(80,93,480,3),"a9b9a0")
	for x in [126,416]:
		block(Rect2(x,53,60,35),"355860");block(Rect2(x+3,56,54,28),"8cbec3")
		block(Rect2(x+6,59,20,9),"d6e1cc");block(Rect2(x+31,59,22,9),"c5ddd0")
		block(Rect2(x+28,55,3,31),"f4e5bd");block(Rect2(x+3,69,54,3),"f4e5bd")
		block(Rect2(x-4,50,6,35),"efdfb7");block(Rect2(x+59,50,6,35),"efdfb7")
		block(Rect2(x-5,85,70,5),"d4b17c")
	block(Rect2(84,84,5,264),"65796a");block(Rect2(551,84,5,264),"65796a")
	block(Rect2(80,348,220,7),"6b5c44");block(Rect2(340,348,220,7),"6b5c44")
	block(Rect2(298,346,44,9),"d2b88b")
	block(Rect2(252,179,136,92),"547e7e");block(Rect2(256,183,128,84),"92ada0")
	block(Rect2(260,187,120,76),"6c9690")
	for x in range(262,380,10):
		block(Rect2(x,182,4,3),"efe1b5");block(Rect2(x,267,4,3),"efe1b5")
	for x in range(277,372,30): block(Rect2(x,218,8,8),"c6cfaf")
	block(Rect2(113,211,78,15),"b46f51")
	for x in range(117,188,9): block(Rect2(x,214,3,9),"dfb37b")
