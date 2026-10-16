extends Node2D

const DEFAULT_CONFIG = preload("res://resources/world/default_water_clip.tres")

@export var clip_config: Resource
var elapsed := 0.0
var last_frame := -1

static func frame_at(seconds: float, phase: int) -> int:
	return (floori(seconds*4.0)+phase)%4

static func is_open_water(point: Vector2, config: Resource = DEFAULT_CONFIG) -> bool:
	var resolved := config if config != null else DEFAULT_CONFIG
	if not resolved.open_water_rect.has_point(point):
		return false
	for excluded: Rect2 in resolved.excluded_rects:
		if excluded.has_point(point):
			return false
	return true

func contains_open_water(point: Vector2) -> bool:
	return is_open_water(point, clip_config)

func _process(delta: float) -> void:
	elapsed += delta
	var next := frame_at(elapsed,0)
	if next != last_frame:
		last_frame = next
		queue_redraw()

func pixel(point: Vector2, color: Color) -> void:
	if contains_open_water(point):
		draw_rect(Rect2(point,Vector2.ONE),color)

func _draw() -> void:
	# Four phase-offset frames change only highlights, never the static terrain.
	for i in range(46):
		var phase := frame_at(elapsed,i%4)
		var x := 9+(i*97)%622
		var y := 303+(i*37)%109
		var color := Color("8bd5ce") if phase < 2 else Color("65b9c0")
		for j in range(3+i%5):
			pixel(Vector2(x+j+phase,y+(1 if j%5 == 0 else 0)),color)
		if i%3 == 0 and phase == 1:
			pixel(Vector2(x+2,y-1),Color("c2e9d9"))
	# Broken foam along the seawall. Pixel clipping keeps all land and pier dry.
	for x in range(0,640,9):
		var phase := frame_at(elapsed,(x/9)%4)
		for j in range(3+phase):
			pixel(Vector2(x+j,293+(x/9)%2),Color("b8e6d8"))
		if phase == 1:
			pixel(Vector2(x+2,295),Color("76c5c9"))
	for i in range(7):
		var phase := frame_at(elapsed,i%4)
		for j in range(3+phase):
			pixel(Vector2(273+i*7+j,322+i%2),Color("c9ecdf"))
	for y in [291,339,395]:
		for x in [401,478]:
			var phase := frame_at(elapsed,(y/3)%4)
			for j in range(5):
				pixel(Vector2(x-3+j,y+phase%2),Color("a9dcd3"))
