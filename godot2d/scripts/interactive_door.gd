extends Node2D
# Separate interactive body, frame, darkness and leaf. No rotated smooth sprites.
const CottageArt=preload("res://scripts/cottage_art.gd")
var inside := false
var approach := Vector2.ZERO
var pose := 0
var collision: CollisionShape2D
var body: StaticBody2D
var texture: Texture2D
var pilot_frames: Array[Texture2D]=[]
var pilot_anchor := Vector2(15,54)
var pilot_leaf_height := 0
var pilot_frame_top := -54.0
var render_size := Vector2(22,29)

func _ready() -> void:
	texture=load("res://assets/environment.png")
	if inside:
		var data:=CottageArt.entry("door_closed")
		if data.has("floor_anchor"):
			pilot_anchor=Vector2(data.floor_anchor[0],data.floor_anchor[1])
		if data.has("closed_leaf_size"):
			pilot_leaf_height=int(data.closed_leaf_size[1])
		for id in ["door_closed","door_half","door_open"]:
			pilot_frames.append(CottageArt.texture_for(id))
		render_size=Vector2(30,59)
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	body=StaticBody2D.new()
	body.name="DoorCollision"
	collision=CollisionShape2D.new()
	var shape:=RectangleShape2D.new()
	shape.size=Vector2(38 if inside else 26,8)
	collision.shape=shape
	body.add_child(collision)
	add_child(body)
	set_pose(0)

func can_interact(point: Vector2) -> bool:
	var offset:=point-approach
	return offset.length()<=24 and absf(offset.x)<=16 and (point.y<=position.y-4 if inside else point.y>=position.y+12)

func set_pose(value: int) -> void:
	pose=clampi(value,0,2)
	if is_instance_valid(collision): collision.set_deferred("disabled",pose==2)
	queue_redraw()

func _draw() -> void:
	if inside and pilot_frames.size()==3 and pilot_frames.all(func(t): return t != null):
		# Aperture and jamb are fixed; only the registered leaf pose changes.
		draw_rect(Rect2(-19,pilot_frame_top,38,55),Color("264d51"))
		draw_rect(Rect2(-17,pilot_frame_top+2,34,52),Color("769185"))
		draw_rect(Rect2(-15,pilot_frame_top+4,30,50),Color("172e34"))
		draw_texture(pilot_frames[pose],-pilot_anchor)
		draw_rect(Rect2(-19,0,38,3),Color("d6c7a0"))
		return
	var width:=32.0 if inside else 22.0
	var height:=16.0 if inside else 29.0
	var r:=Rect2(-width/2,-8.0 if inside else -height,width,height)
	draw_rect(r.grow(3),Color("264d51"))
	draw_rect(r.grow(1),Color("769185"))
	draw_rect(r,Color("172e34"))
	# Hinged leaf uses three integer widths, reusing the exact original teal leaf.
	var leaf_width: float=[width,roundf(width*0.5),3.0][pose]
	if texture:
		draw_texture_rect_region(texture,Rect2(r.position,Vector2(leaf_width,height)),Rect2(348,383,61,81))
	if pose>0:
		draw_rect(Rect2(r.position+Vector2(leaf_width-2,0),Vector2(2,height)),Color("38747b"))
	draw_rect(Rect2(-width/2-3,8 if inside else 0,width+6,3),Color("d6c7a0"))
