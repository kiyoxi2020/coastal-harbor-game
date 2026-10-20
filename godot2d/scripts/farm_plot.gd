@tool
extends Node2D
# Region transforms own cell coordinates; persistent IDs never depend on position.
const Crops = preload("res://scripts/simulation/crop_catalog.gd")
const DRY = preload("res://assets/farming-polish-v3/soil_dry.png")
const WET = preload("res://assets/farming-polish-v3/soil_wet.png")
const SEED = preload("res://assets/farming-polish-v3/seed.png")
const SPROUT = preload("res://assets/farming-polish-v3/sprout.png")
const LETTUCE = preload("res://assets/farming-polish-v3/lettuce_mature.png")
const TOMATO_YOUNG = preload("res://assets/farming-polish-v3/tomato_young.png")
const TOMATO = preload("res://assets/farming-polish-v3/tomato_mature.png")
@export_enum("garden_a", "garden_b") var region_id := "garden_a"
const GRID_ORIGIN := Vector2(-32,-32)
const SIDES := {"left":Vector2i.LEFT,"right":Vector2i.RIGHT,"top":Vector2i.UP,"bottom":Vector2i.DOWN}
var selected_cell := ""
var target_reachable := false

func cell_at(global_point: Vector2) -> String:
	var point := to_local(global_point) - GRID_ORIGIN
	if not Rect2(Vector2.ZERO,Vector2(64,32)).has_point(point): return ""
	return "%s:%d:%d" % [region_id,int(point.x/16),int(point.y/16)]

func cell_center(id: String) -> Vector2:
	var parts := id.split(":")
	if parts.size()!=3 or parts[0]!=region_id or not parts[1].is_valid_int() or not parts[2].is_valid_int(): return Vector2.INF
	var x := int(parts[1])
	var y := int(parts[2])
	if x<0 or x>=4 or y<0 or y>=2: return Vector2.INF
	return to_global(GRID_ORIGIN+Vector2(x*16+8,y*16+8))

func refresh(cells: Dictionary) -> void:
	for node in get_children():
		if not node is Node2D or not node.has_meta("cell_coord"): continue
		var coord: Vector2i = node.get_meta("cell_coord")
		var id := "%s:%d:%d" % [region_id,coord.x,coord.y]
		var cell: Dictionary = cells.get(id,{})
		if cell.is_empty(): continue
		var soil := node.get_node("Soil") as Sprite2D
		soil.visible = cell.tilled
		soil.texture = WET if cell.watered else DRY
		var material := soil.material as ShaderMaterial
		for side in SIDES:
			var neighbor: Vector2i=coord+SIDES[side]
			var other: Dictionary=cells.get("%s:%d:%d" % [region_id,neighbor.x,neighbor.y],{})
			material.set_shader_parameter("join_"+side,other.get("tilled",false))
		var crop := node.get_node("Crop") as Sprite2D
		crop.visible = cell.crop_id != ""
		if cell.crop_id != "":
			var mature: bool = cell.growth >= Crops.get_crop(cell.crop_id).growth_days
			crop.texture = (LETTUCE if cell.crop_id=="lettuce" else TOMATO) if mature else (SEED if cell.growth==0 else (TOMATO_YOUNG if cell.crop_id=="tomato" and cell.growth>=2 else SPROUT))
			crop.offset = Vector2(0,-crop.texture.get_height()/2.0)
	queue_redraw()

func select_cell(id: String, reachable: bool) -> void:
	if selected_cell==id and target_reachable==reachable: return
	selected_cell=id
	target_reachable=reachable
	queue_redraw()

func _draw() -> void:
	# Faint corner marks identify unworked ground without replacing grass art.
	for y in range(2):
		for x in range(4):
			var p := GRID_ORIGIN+Vector2(x*16,y*16)
			draw_line(p+Vector2(1,3),p+Vector2(1,1),Color(0.65,0.56,0.30,0.5))
			draw_line(p+Vector2(1,1),p+Vector2(3,1),Color(0.65,0.56,0.30,0.5))
	if selected_cell == "": return
	var center := cell_center(selected_cell)
	if not center.is_finite(): return
	var p := to_local(center)-Vector2(8,8)
	var color := Color(1,0.88,0.38) if target_reachable else Color(1,0.45,0.40)
	for corner in [Vector2(0,0),Vector2(16,0),Vector2(0,16),Vector2(16,16)]:
		var dx := 4 if corner.x==0 else -4
		var dy := 4 if corner.y==0 else -4
		draw_line(p+corner,p+corner+Vector2(dx,0),color,1)
		draw_line(p+corner,p+corner+Vector2(0,dy),color,1)
