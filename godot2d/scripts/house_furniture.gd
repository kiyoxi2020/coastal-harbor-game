extends Node2D
const CottageArt=preload("res://scripts/cottage_art.gd")
var kind := "bed"
var art_id := ""
var extent := Vector2(48,80)
var pilot_texture: Texture2D
var pilot_pivot := Vector2.ZERO

func _ready() -> void:
	var id := art_id if not art_id.is_empty() else kind
	var data := CottageArt.entry(id)
	pilot_texture = CottageArt.texture_for(id)
	if data.has("pivot"):
		pilot_pivot=Vector2(data.pivot[0],data.pivot[1])
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	if pilot_texture == null:
		push_error("Cottage furniture texture missing: "+id)

func _draw() -> void:
	if pilot_texture:
		draw_texture(pilot_texture,-pilot_pivot)
