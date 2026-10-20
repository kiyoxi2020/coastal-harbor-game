extends Camera2D

@export var exterior: Node2D
var target: Node2D

func _ready() -> void:
	get_viewport().size_changed.connect(update_position)
	update_position()
	reset_smoothing()
	force_update_scroll()

func _process(_delta: float) -> void:
	update_position()

func update_position() -> void:
	if not is_instance_valid(target) or not is_instance_valid(exterior):
		return
	if target.get("world") != null and target.world.foraging.location=="house":
		position=Vector2(320,200)
		return
	var half_view := get_viewport_rect().size / zoom / 2.0
	var area:Node2D=target.world.regions.active_scene() if target.get("world")!=null and target.world.get("regions")!=null else exterior
	var bounds: Rect2 = area.world_bounds
	var desired := target.position + Vector2(0,-40)
	for axis in range(2):
		if bounds.size[axis] <= half_view[axis]*2.0:
			desired[axis] = bounds.get_center()[axis]
		else:
			desired[axis] = clampf(desired[axis],bounds.position[axis]+half_view[axis],bounds.end[axis]-half_view[axis])
	position = desired.round()
