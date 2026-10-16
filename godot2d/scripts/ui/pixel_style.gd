@tool
extends StyleBox
# Procedural, resolution-independent implementation of approved pixel concept B.
# No text or game state is baked into art. Coordinates snap to a 2px UI grid.
@export_enum("paper", "canvas", "teal", "hover", "active", "focus", "slot", "selected_slot") var kind := "paper"
@export_group("Palette")
@export var dark_color := Color("605640")
@export var mid_color := Color("b5a17c")
@export var fill_color := Color("efdfb8")
@export var light_color := Color("fff3d2")
@export var shadow_color := Color("24434c")
@export var stitch_color := Color("b6a07b")
@export var focus_color := Color("d56b45")

func _init(value: String = "") -> void:
	if not value.is_empty():
		kind = value
		# Compatibility for procedural callers until their scenes migrate in batch 2.
		set_content_margin_all(10)
		apply_default_palette(value)

func apply_default_palette(value: String) -> void:
	if value == "canvas":
		dark_color = Color("173f49")
		mid_color = Color("3d7277")
		fill_color = Color("285966")
		light_color = Color("6e9c98")
		stitch_color = Color("a7b995")
	elif value in ["teal", "hover"]:
		dark_color = Color("295b67")
		mid_color = Color("639796")
		fill_color = Color("9ac4ba")
		light_color = Color("c9e1cc")
	elif value in ["active", "focus"]:
		dark_color = Color("9d523b")
		mid_color = Color("df8057")
		fill_color = Color("edaa7f")
		light_color = Color("ffe3b7")
	elif value in ["slot", "selected_slot"]:
		fill_color = Color("dbceaa")
		mid_color = Color("df8057") if value == "selected_slot" else Color("a18d6d")
		light_color = Color("f8ebc7")

func block(canvas: RID, rect: Rect2, color: Color) -> void:
	RenderingServer.canvas_item_add_rect(canvas,rect,color)

func stepped(canvas: RID, rect: Rect2, color: Color, corner: float) -> void:
	block(canvas,Rect2(rect.position+Vector2(corner,0),rect.size-Vector2(corner*2,0)),color)
	block(canvas,Rect2(rect.position+Vector2(0,corner),rect.size-Vector2(0,corner*2)),color)

func _draw(canvas: RID, rect: Rect2) -> void:
	var r := Rect2(rect.position.round(),rect.size.round())
	if kind == "focus":
		# Focus must not cover the button text or icon.
		for p in [r.position,r.position+Vector2(r.size.x-12,0),r.position+Vector2(0,r.size.y-12),r.end-Vector2(12,12)]:
			block(canvas,Rect2(p,Vector2(12,4)),focus_color)
			block(canvas,Rect2(p,Vector2(4,12)),focus_color)
		return
	stepped(canvas,Rect2(r.position+Vector2(4,6),r.size),shadow_color,8)
	stepped(canvas,r,dark_color,6)
	stepped(canvas,r.grow(-2),mid_color,4)
	stepped(canvas,r.grow(-6),light_color,2)
	stepped(canvas,r.grow(-10),fill_color,2)
	block(canvas,Rect2(r.position+Vector2(10,r.size.y-8),Vector2(maxf(0,r.size.x-20),2)),mid_color)
	if kind in ["paper","canvas","slot","selected_slot"]:
		var inset := 10.0 if kind in ["slot","selected_slot"] else 16.0
		for x in range(int(r.position.x+inset),int(r.end.x-inset-4),16):
			block(canvas,Rect2(x,r.position.y+inset,6,2),stitch_color)
			block(canvas,Rect2(x,r.end.y-inset,6,2),stitch_color)
		if kind != "slot":
			for y in range(int(r.position.y+inset),int(r.end.y-inset-4),16):
				block(canvas,Rect2(r.position.x+inset,y,2,6),stitch_color)
				block(canvas,Rect2(r.end.x-inset,y,2,6),stitch_color)
