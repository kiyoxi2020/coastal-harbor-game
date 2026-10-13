extends Node2D
# Separate interactive body, frame, darkness and leaf. No rotated smooth sprites.
const CottageArt=preload("res://scripts/cottage_art.gd")
var inside := false
var entrance_normal := Vector2.DOWN
var approach := Vector2.ZERO
var pose := 0
var collision: CollisionShape2D
var body: StaticBody2D
var texture: Texture2D
var pilot_frames: Array[Texture2D]=[]
var pilot_anchor := Vector2(15,54)
var pilot_leaf_height := 0
var pilot_frame_top := -9.0
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
		render_size=Vector2(38,12)
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	body=StaticBody2D.new()
	body.name="DoorCollision"
	collision=CollisionShape2D.new()
	var shape:=RectangleShape2D.new()
	shape.size=Vector2(30 if inside else 20,8)
	collision.shape=shape
	body.add_child(collision)
	add_child(body)
	var jamb_body:=StaticBody2D.new()
	jamb_body.name="JambCollision"
	var jamb_center:=17.0 if inside else 12.0
	for side in [-1.0,1.0]:
		var jamb_shape:=CollisionShape2D.new()
		var jamb_box:=RectangleShape2D.new()
		jamb_box.size=Vector2(4,8)
		jamb_shape.shape=jamb_box
		jamb_shape.position=Vector2(side*jamb_center,0)
		jamb_body.add_child(jamb_shape)
	add_child(jamb_body)
	var jamb:=Node2D.new()
	jamb.set_script(preload("res://scripts/door_jamb.gd"))
	jamb.width=38.0 if inside else 28.0
	jamb.height=9.0 if inside else 32.0
	jamb.z_index=0 if inside else 2
	add_child(jamb)
	set_pose(0)

func can_interact(point: Vector2) -> bool:
	var offset:=point-position
	var depth:=offset.dot(entrance_normal)
	var lateral:=offset.dot(Vector2(entrance_normal.y,-entrance_normal.x))
	return depth>=0 and depth<=56 and absf(lateral)<=24

func aperture_top() -> float:
	return global_position.y+(pilot_frame_top+4 if inside else -29.0)

func set_pose(value: int) -> void:
	pose=clampi(value,0,2)
	if is_instance_valid(collision): collision.set_deferred("disabled",pose==2)
	queue_redraw()

func _draw() -> void:
	if inside:
		# Use the same registered waist-height strip in each pose, at native pixel scale.
		# It retains the rail and handle without laying a tall front-facing door on the floor.
		draw_rect(Rect2(-19,-9,38,12),Color("264d51"))
		draw_rect(Rect2(-15,-7,30,8),Color("172e34"))
		if pilot_frames.size()==3 and pilot_frames[pose]:
			draw_texture_rect_region(pilot_frames[pose],Rect2(-15,-7,30,8),Rect2(0,29,30,8))
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
