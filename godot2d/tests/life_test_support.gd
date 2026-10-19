extends RefCounted

const State = preload("res://scripts/player_state.gd")

var checks: Dictionary = {}

func make_state() -> Dictionary:
	return State.new().to_data(Vector2(330, 250)).duplicate(true)

func check(id: String, passed: bool) -> void:
	checks[id] = passed
	print(("PASS " if passed else "FAIL ") + id)

func temporary_directory(prefix: String = "P02") -> String:
	return "/private/tmp/coastal-%s-%s" % [prefix, Time.get_ticks_usec()]

func passed() -> bool:
	return not checks.values().has(false)
