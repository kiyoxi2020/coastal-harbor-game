extends RefCounted

const State = preload("res://scripts/player_state.gd")
const Rules = preload("res://scripts/simulation/life_rules.gd")
var _save_service: RefCounted

func _init(save_service: RefCounted) -> void:
	_save_service = save_service

static func failure(code: String) -> Dictionary:
	return {"ok":false, "code":code, "next_state":null, "events":[], "duplicate":false}

func execute(current: RefCounted, position: Vector2, kind: String, args: Dictionary, request_id: int) -> Dictionary:
	if current == null or not current.has_method("to_data"):
		return failure("invalid_state")
	var snapshot: Dictionary = current.to_data(position)
	var result: Dictionary = Rules.plan(snapshot, kind, args, request_id)
	if not result.ok:
		return failure(result.code)
	if request_id == int(snapshot.life.action_seq):
		return {"ok":true, "code":"ok", "next_state":current, "events":[], "duplicate":true}
	# Restore before writing: a persisted candidate must already be publishable.
	var next_state = State.new()
	if not State.valid_data(result.state) or not next_state.restore(result.state):
		return failure("invalid_state")
	if _save_service == null or not _save_service.write_save(result.state):
		return failure("save_failed")
	return {"ok":true, "code":"ok", "next_state":next_state, "events":result.events.duplicate(true), "duplicate":false}
