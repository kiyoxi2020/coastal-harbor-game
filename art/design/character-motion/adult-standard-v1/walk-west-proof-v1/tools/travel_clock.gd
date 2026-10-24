extends RefCounted
## Diagnostic trajectory in screen coordinates; never adjusts individual feet/parts.
const Timeline = preload("res://timeline.gd")
const WORLD_SPEED: float = 72.0
const CAMERA_ZOOM: float = 4.0
const SCREEN_SPEED: float = WORLD_SPEED * CAMERA_ZOOM
const START_X: float = 1100.0
const MIN_ROOT_X: float = 128.0
var timeline = Timeline.new()
var cycle_ms: float = 0.0
var loops_per_pass: int = 1

func configure(durations: Array) -> void:
	timeline.configure(durations)
	cycle_ms = timeline.cycle_ms
	loops_per_pass = maxi(1, floori((START_X - MIN_ROOT_X) / (SCREEN_SPEED * cycle_ms / 1000.0)))

func frame_at(elapsed_ms: float) -> int:
	return timeline.frame_at(elapsed_ms)

func loop_at(elapsed_ms: float) -> int:
	return timeline.loop_at(elapsed_ms)

func pass_at(elapsed_ms: float) -> int:
	return floori(loop_at(elapsed_ms) / float(loops_per_pass))

func root_x_at(elapsed_ms: float) -> float:
	var pass_start_ms: float = pass_at(elapsed_ms) * loops_per_pass * cycle_ms
	return START_X - SCREEN_SPEED * (maxf(0.0, elapsed_ms) - pass_start_ms) / 1000.0

func resets_between(previous_ms: float, elapsed_ms: float) -> Array:
	var events: Array = []
	for pass_index in range(pass_at(maxf(0.0, previous_ms)) + 1, pass_at(elapsed_ms) + 1):
		var boundary: float = pass_index * loops_per_pass * cycle_ms
		events.append({"at_elapsed_ms": boundary, "observed_elapsed_ms": elapsed_ms, "loop": pass_index * loops_per_pass, "from_root_x": START_X - SCREEN_SPEED * loops_per_pass * cycle_ms / 1000.0, "to_root_x": START_X, "reason": "complete_cycle_boundary_reset_not_continuous_motion"})
	return events
