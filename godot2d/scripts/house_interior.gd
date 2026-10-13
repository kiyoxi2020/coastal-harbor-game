extends Node2D
const Data=preload("res://scripts/room_data.gd")
const CottageArt=preload("res://scripts/cottage_art.gd")
var sort_layer: Node2D
var door
var floor_texture: Texture2D
var wall_texture: Texture2D
var rug_texture: Texture2D
var bed_rug_texture: Texture2D
func _ready() -> void:
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	floor_texture=CottageArt.texture_for("floor")
	wall_texture=CottageArt.texture_for("wall")
	rug_texture=CottageArt.texture_for("rug")
	bed_rug_texture=CottageArt.texture_for("bed_rug")
	if floor_texture==null or wall_texture==null or rug_texture==null or bed_rug_texture==null:
		push_error("Cottage background texture missing")
	sort_layer=Node2D.new()
	sort_layer.y_sort_enabled=true
	sort_layer.z_index=0
	add_child(sort_layer)
	for item in Data.furniture():
		var node:=Node2D.new()
		node.set_script(preload("res://scripts/house_furniture.gd"))
		node.kind=item.id
		node.art_id=item.get("art",item.id)
		node.name="Bed" if item.id=="bed" else item.id
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
func tile_texture(texture: Texture2D, area: Rect2) -> void:
	if texture==null: return
	var step:=texture.get_size()
	for row in range(int(ceil(area.size.y/step.y))):
		for column in range(int(ceil(area.size.x/step.x))):
			var origin:=area.position+Vector2(column*step.x,row*step.y)
			var remaining:=area.end-origin
			var size:=Vector2(min(step.x,remaining.x),min(step.y,remaining.y))
			draw_texture_rect_region(texture,Rect2(origin,size),Rect2(Vector2.ZERO,size))
func _draw() -> void:
	block(Rect2(-200,-200,1040,900),"183039")
	block(Data.FLOOR.grow(8),"493e35")
	tile_texture(floor_texture,Data.FLOOR)
	tile_texture(wall_texture,Rect2(176,64,288,64))
	block(Rect2(172,112,4,208),"65796a")
	block(Rect2(464,112,4,208),"65796a")
	block(Rect2(176,320,124,7),"6b5c44")
	block(Rect2(340,320,124,7),"6b5c44")
	if rug_texture: draw_texture(rug_texture,Vector2(280,212))
	if bed_rug_texture: draw_texture(bed_rug_texture,Vector2(192,228))
