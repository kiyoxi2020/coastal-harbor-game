extends StyleBox
# Procedural, resolution-independent implementation of approved pixel concept B.
# No text or game state is baked into art. Coordinates snap to a 2px UI grid.
var kind := "paper"

func _init(value: String = "paper") -> void:
	kind = value
	set_content_margin_all(10)

func block(canvas: RID, rect: Rect2, color: String) -> void:
	RenderingServer.canvas_item_add_rect(canvas,rect,Color(color))

func stepped(canvas: RID, rect: Rect2, color: String, corner: float) -> void:
	block(canvas,Rect2(rect.position+Vector2(corner,0),rect.size-Vector2(corner*2,0)),color)
	block(canvas,Rect2(rect.position+Vector2(0,corner),rect.size-Vector2(0,corner*2)),color)

func _draw(canvas: RID, rect: Rect2) -> void:
	var r := Rect2(rect.position.round(),rect.size.round())
	var dark := "605640"
	var mid := "b5a17c"
	var fill := "efdfb8"
	var light := "fff3d2"
	if kind == "canvas":
		dark = "173f49"
		mid = "3d7277"
		fill = "285966"
		light = "6e9c98"
	elif kind in ["teal","hover"]:
		dark = "295b67"
		mid = "639796"
		fill = "9ac4ba"
		light = "c9e1cc"
	elif kind in ["active","focus"]:
		dark = "9d523b"
		mid = "df8057"
		fill = "edaa7f"
		light = "ffe3b7"
	elif kind in ["slot","selected_slot"]:
		fill = "dbceaa"
		mid = "df8057" if kind == "selected_slot" else "a18d6d"
		light = "f8ebc7"
	if kind == "focus":
		# Focus must not cover the button text or icon.
		for p in [r.position,r.position+Vector2(r.size.x-12,0),r.position+Vector2(0,r.size.y-12),r.end-Vector2(12,12)]:
			block(canvas,Rect2(p,Vector2(12,4)),"d56b45")
			block(canvas,Rect2(p,Vector2(4,12)),"d56b45")
		return
	stepped(canvas,Rect2(r.position+Vector2(4,6),r.size),"24434c",8)
	stepped(canvas,r,dark,6)
	stepped(canvas,r.grow(-2),mid,4)
	stepped(canvas,r.grow(-6),light,2)
	stepped(canvas,r.grow(-10),fill,2)
	block(canvas,Rect2(r.position+Vector2(10,r.size.y-8),Vector2(maxf(0,r.size.x-20),2)),mid)
	if kind in ["paper","canvas","slot","selected_slot"]:
		var inset := 10.0 if kind in ["slot","selected_slot"] else 16.0
		var stitch := "b6a07b" if kind != "canvas" else "a7b995"
		for x in range(int(r.position.x+inset),int(r.end.x-inset-4),16):
			block(canvas,Rect2(x,r.position.y+inset,6,2),stitch)
			block(canvas,Rect2(x,r.end.y-inset,6,2),stitch)
		if kind != "slot":
			for y in range(int(r.position.y+inset),int(r.end.y-inset-4),16):
				block(canvas,Rect2(r.position.x+inset,y,2,6),stitch)
				block(canvas,Rect2(r.end.x-inset,y,2,6),stitch)
