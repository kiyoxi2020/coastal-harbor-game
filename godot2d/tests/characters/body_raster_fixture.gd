extends "res://dev/characters/character_walk_trial.gd"
## Initialization-only static raster fixture; inherits the existing controller.
## It deliberately loads no old character package and runs no animation clock.
func _ready() -> void:
	initialize_trial_shell()
	set_physics_process(false)
