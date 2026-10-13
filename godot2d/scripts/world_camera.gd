extends Camera2D

const Data = preload("res://scripts/harbor_data.gd")
var target: Node2D

func _ready() -> void:
	zoom = Vector2(2,2)
	position_smoothing_enabled = false
	get_viewport().size_changed.connect(update_position)
	update_position()
	reset_smoothing()
	force_update_scroll()

func _process(_delta: float) -> void:
	update_position()

func update_position() -> void:
	if not is_instance_valid(target):
		return
	var half_view := get_viewport_rect().size / zoom / 2.0
	var bounds: Rect2 = Data.WORLD_BOUNDS
	var desired := target.position + Vector2(0,-40)
	for axis in range(2):
		if bounds.size[axis] <= half_view[axis]*2.0:
			desired[axis] = bounds.get_center()[axis]
		else:
			desired[axis] = clampf(desired[axis],bounds.position[axis]+half_view[axis],bounds.end[axis]-half_view[axis])
	position = desired.round()
