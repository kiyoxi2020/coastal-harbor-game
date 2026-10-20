@tool
extends Node2D

@export_enum("clam", "snail", "kelp", "生种", "番种", "生菜", "番茄") var kind := "clam":
	set(value):
		kind = value
		queue_redraw()
var highlighted := false:
	set(value):
		if highlighted != value:
			highlighted = value
			queue_redraw()

const SEA_TEXTURES={
	"clam":preload("res://assets/visual-polish-v6/clam.png"),
	"snail":preload("res://assets/visual-polish-v6/snail.png"),
	"kelp":preload("res://assets/visual-polish-v6/kelp.png")
}
func _draw() -> void:
	if highlighted:
		draw_rect(Rect2(-9,-10,18,16),Color("fff0cb"),false,1)
	if kind in SEA_TEXTURES:
		draw_texture_rect(SEA_TEXTURES[kind],Rect2(-6,-9,12,11),false)
	else:
		draw_rect(Rect2(-10,-10,20,12), Color("f7e7c4"))
		draw_string(ThemeDB.fallback_font, Vector2(-9,-1), kind, HORIZONTAL_ALIGNMENT_CENTER, 18, 8, Color("4b3b32"))
