extends RefCounted
const Crops = preload("res://scripts/simulation/crop_catalog.gd")
const Schema = preload("res://scripts/simulation/state_schema.gd")
const Inventory = preload("res://scripts/inventory/inventory_container.gd")

static func _failure(code: String) -> Dictionary:
	return {"ok":false, "code":code, "state":{}, "events":[]}

static func act(data: Dictionary, kind: String, args: Dictionary) -> Dictionary:
	if not Schema.validate_v4(data):
		return _failure("invalid_state")
	if kind not in ["hoe", "plant", "water", "harvest"]:
		return _failure("unknown_action")
	var fields := ["cell_id", "crop_id"] if kind == "plant" else ["cell_id"]
	if not Schema._exact_keys(args, fields) or not args.cell_id is String or not data.life.plots.has(args.cell_id):
		return _failure("invalid_request")
	var definition: Dictionary = {}
	if kind == "plant":
		if not args.crop_id is String:
			return _failure("invalid_request")
		definition = Crops.get_crop(args.crop_id)
		if definition.is_empty():
			return _failure("invalid_request")
	var candidate := data.duplicate(true)
	var plot: Dictionary = candidate.life.plots[args.cell_id]
	var bag = Inventory.new(24)
	if not bag.restore_slots(candidate.bag):
		return _failure("invalid_state")
	var event := {"day_id":int(candidate.life.day_id), "kind":kind, "source":"player", "target":args.cell_id, "items":{}, "cash":0, "reason":kind}
	if kind == "hoe":
		if plot.tilled: return _failure("already_tilled")
		plot.tilled = true
	elif kind == "plant":
		if not plot.tilled: return _failure("not_tilled")
		if plot.crop_id != "":
			return _failure("plot_occupied")
		if not bag.remove_item(definition.seed_id, 1):
			return _failure("insufficient_stock")
		plot.crop_id = args.crop_id
		plot.growth = 0
		plot.fertilized = false
		event.kind = "consume"
		event.target = "consumed"
		event.items = {definition.seed_id:1}
		event.reason = "plant:" + args.cell_id
	else:
		if not plot.tilled: return _failure("not_tilled")
		definition = Crops.get_crop(plot.crop_id)
		var mature: bool = not definition.is_empty() and plot.growth >= definition.growth_days
		if kind == "water":
			if plot.watered:
				return _failure("already_watered")
			plot.watered = true
		else:
			if not mature:
				return _failure("not_mature")
			if bag.add(definition.yield_item_id, definition.yield_amount) != definition.yield_amount:
				return _failure("inventory_full")
			event.kind = "production"
			event.source = args.cell_id
			event.target = "player"
			event.inputs = {}
			event.outputs = {definition.yield_item_id:definition.yield_amount}
			event.items = event.outputs.duplicate(true)
			candidate.life.plots[args.cell_id] = {"tilled":true, "crop_id":"", "growth":0, "watered":plot.watered, "fertilized":false}
	candidate.bag = bag.snapshot()
	if not Schema.validate_v4(candidate):
		return _failure("invalid_state")
	return {"ok":true, "code":"ok", "state":candidate, "events":[event]}

static func grow(data: Dictionary) -> Dictionary:
	if not Schema.validate_v4(data):
		return _failure("invalid_state")
	var candidate := data.duplicate(true)
	var events: Array = []
	for id in Schema.cell_ids():
		var plot: Dictionary = candidate.life.plots[id]
		if plot.crop_id == "":
			plot.watered = false
			continue
		var definition := Crops.get_crop(plot.crop_id)
		if plot.watered and plot.growth < definition.growth_days:
			plot.growth = mini(int(plot.growth) + 1, int(definition.growth_days))
			events.append({"day_id":int(candidate.life.day_id), "kind":"growth", "source":id, "target":id, "items":{}, "cash":0, "reason":"mature" if plot.growth == definition.growth_days else "growth"})
		plot.watered = false
		if plot.growth == definition.growth_days:
			plot.fertilized = false
	if not Schema.validate_v4(candidate):
		return _failure("invalid_state")
	return {"ok":true, "code":"ok", "state":candidate, "events":events}
