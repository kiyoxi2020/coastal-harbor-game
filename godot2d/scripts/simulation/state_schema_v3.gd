extends RefCounted

const Catalog = preload("res://scripts/inventory/item_catalog.gd")
const Data = preload("res://scripts/harbor_data.gd")
const INVENTORY_ITEMS := ["clam", "snail", "kelp", "lettuce_seed", "tomato_seed", "lettuce", "tomato"]
const SEAFOOD := ["clam", "snail", "kelp"]
const RECEIPT_KINDS := ["trade", "sleep", "plant", "water", "harvest", "collect", "craft", "fertilize", "supply", "open_restaurant"]

static func _integer(value) -> bool:
	return (value is int or value is float) and not value is bool and is_finite(float(value)) and float(value) == floor(float(value))

static func _bounded_integer(value, minimum: int, maximum: int) -> bool:
	return _integer(value) and value >= minimum and value <= maximum

static func _true_bool(value) -> bool:
	return value is bool and value

static func _exact_keys(value: Dictionary, expected: Array) -> bool:
	if value.size() != expected.size():
		return false
	var keys: Array = []
	for key in value:
		keys.append(str(key))
	keys.sort()
	var sorted_expected := expected.duplicate()
	sorted_expected.sort()
	return keys == sorted_expected

static func _clean_name(value: String) -> String:
	var result := ""
	for character in value:
		if character.unicode_at(0) >= 32 and character.unicode_at(0) != 127:
			result += character
	result = result.strip_edges().left(12)
	return "归乡人" if result.is_empty() else result

static func _empty_slots(capacity: int) -> Array:
	var result: Array = []
	for index in range(capacity):
		result.append({"id":"", "amount":0})
	return result

static func default_life() -> Dictionary:
	var market_slots := _empty_slots(48)
	market_slots[0] = {"id":"lettuce_seed", "amount":20}
	market_slots[1] = {"id":"tomato_seed", "amount":20}
	return {
		"day_id":1, "last_settled_day":0, "action_seq":0, "last_receipt":{}, "wallet":100,
		"accounts":{"market":{"cash":1000, "slots":market_slots, "buy_quota":{"clam":12, "snail":12, "kelp":12, "lettuce":12, "tomato":12}}},
		"plots":{
			"plot_a":{"crop_id":"", "growth":0, "watered":false, "fertilized":false},
			"plot_b":{"crop_id":"", "growth":0, "watered":false, "fertilized":false}
		},
		"events":[], "daily_reports":[]
	}.duplicate(true)

static func _valid_slots(slots, capacity: int, allowed: Array = INVENTORY_ITEMS) -> bool:
	if not slots is Array or slots.size() != capacity:
		return false
	var catalog := Catalog.new()
	for slot in slots:
		if not slot is Dictionary or not _exact_keys(slot, ["id", "amount"]):
			return false
		if not slot.id is String or not _integer(slot.amount):
			return false
		if slot.id == "":
			if slot.amount != 0:
				return false
		elif slot.id not in allowed or slot.amount < 1 or slot.amount > catalog.stack_limit(slot.id):
			return false
	return true

static func _valid_common(data: Dictionary, version: int, allowed_items: Array) -> bool:
	var expected := ["version", "location", "player_name", "bag", "chest", "collected", "discovered", "total_collected", "position"]
	if version == 1:
		expected.erase("location")
	elif version == 3:
		expected.append("life")
	if not _exact_keys(data, expected) or data.version != version:
		return false
	if version > 1 and (not data.location is String or data.location not in ["harbor", "house"]):
		return false
	if not data.player_name is String or _clean_name(data.player_name) != data.player_name:
		return false
	if not _valid_slots(data.bag, 24, allowed_items) or not _valid_slots(data.chest, 48, allowed_items):
		return false
	if not data.collected is Dictionary or not data.discovered is Dictionary:
		return false
	if not _bounded_integer(data.total_collected, 0, 1000000):
		return false
	if not data.position is Array or data.position.size() != 2:
		return false
	for coordinate in data.position:
		if not (coordinate is int or coordinate is float) or coordinate is bool or not is_finite(float(coordinate)):
			return false
	return true

static func validate_legacy(data: Dictionary) -> bool:
	if not data.has("version") or not _integer(data.version) or int(data.version) not in [1, 2]:
		return false
	if not _valid_common(data, int(data.version), SEAFOOD):
		return false
	var known: Dictionary = {}
	for entry in Data.pickups():
		known[str(entry.id)] = str(entry.kind)
	var earned := {"clam":0, "snail":0, "kelp":0}
	var found: Dictionary = {}
	for id in data.collected:
		if not id is String or not known.has(id) or not _true_bool(data.collected[id]):
			return false
		earned[known[id]] += 1
		found[known[id]] = true
	if data.total_collected != data.collected.size() or data.discovered != found:
		return false
	for kind in SEAFOOD:
		var held := 0
		for slots in [data.bag, data.chest]:
			for slot in slots:
				if slot.id == kind:
					held += int(slot.amount)
		if held > earned[kind]:
			return false
	return true

static func _valid_receipt(receipt: Dictionary, sequence: int) -> bool:
	if sequence == 0:
		return receipt.is_empty()
	return _exact_keys(receipt, ["request_id", "kind", "args"]) and _integer(receipt.request_id) and receipt.request_id == sequence and receipt.kind is String and receipt.kind in RECEIPT_KINDS and receipt.args is Dictionary

static func _valid_plot(plot: Dictionary) -> bool:
	if not _exact_keys(plot, ["crop_id", "growth", "watered", "fertilized"]):
		return false
	if not plot.crop_id is String or plot.crop_id not in ["", "lettuce", "tomato"] or not _bounded_integer(plot.growth, 0, 4):
		return false
	if not plot.watered is bool or not plot.fertilized is bool:
		return false
	if plot.crop_id == "":
		return plot.growth == 0 and not plot.watered and not plot.fertilized
	var mature_at: int = {"lettuce":2,"tomato":4}[plot.crop_id]
	return plot.growth <= mature_at and (plot.growth < mature_at or (not plot.watered and not plot.fertilized))

static func _valid_reports(reports: Array, current_day: int) -> bool:
	if reports.size() > 30:
		return false
	var previous_day := 0
	for report in reports:
		if not report is Dictionary or not _exact_keys(report, ["day_id", "cash_in", "cash_out", "pickups", "mature_plots", "summary"]):
			return false
		if not _bounded_integer(report.day_id, 1, current_day - 1) or report.day_id <= previous_day:
			return false
		for key in ["cash_in", "cash_out"]:
			if not _bounded_integer(report[key], 0, 1000000000):
				return false
		if not _bounded_integer(report.pickups, 0, 6):
			return false
		if not report.mature_plots is Array or not report.summary is Array:
			return false
		var unique_plots: Dictionary = {}
		for id in report.mature_plots:
			if not id is String or id not in ["plot_a", "plot_b"]:
				return false
			if unique_plots.has(id):
				return false
			unique_plots[id] = true
		for line in report.summary:
			if not line is String:
				return false
		previous_day = report.day_id
	return true

static func _valid_events(events: Array, current_day: int) -> bool:
	if events.size() > 256:
		return false
	var ids: Dictionary = {}
	for event in events:
		if not event is Dictionary:
			return false
		var fields := ["event_id", "day_id", "kind", "source", "target", "items", "cash", "reason"]
		if event.get("kind") == "production":
			fields.append_array(["inputs", "outputs"])
		if not _exact_keys(event, fields):
			return false
		if not event.event_id is String or event.event_id.is_empty() or ids.has(event.event_id):
			return false
		ids[event.event_id] = true
		if not _bounded_integer(event.day_id, 1, current_day) or not _bounded_integer(event.cash, 0, 1000000000):
			return false
		for key in ["kind", "source", "target", "reason"]:
			if not event[key] is String or event[key].is_empty():
				return false
		if not event.items is Dictionary:
			return false
		var item_maps: Array = [event.items]
		if event.kind == "production":
			if not event.inputs is Dictionary or not event.outputs is Dictionary or event.outputs.is_empty() or event.items != event.outputs:
				return false
			item_maps.append_array([event.inputs, event.outputs])
		for items in item_maps:
			for id in items:
				if not id is String or id not in INVENTORY_ITEMS or not _bounded_integer(items[id], 1, 1000000):
					return false
	return true

static func validate_v3(data: Dictionary) -> bool:
	if not _valid_common(data, 3, INVENTORY_ITEMS):
		return false
	if not _exact_keys(data, ["version", "location", "player_name", "bag", "chest", "collected", "discovered", "total_collected", "position", "life"]):
		return false
	var known: Dictionary = {}
	for entry in Data.pickups():
		known[str(entry.id)] = str(entry.kind)
	for id in data.collected:
		if not id is String or not known.has(id) or not _true_bool(data.collected[id]):
			return false
		if not _true_bool(data.discovered.get(known[id])):
			return false
	if data.total_collected < data.collected.size():
		return false
	for kind in data.discovered:
		if kind not in SEAFOOD or not _true_bool(data.discovered[kind]):
			return false
	if not data.life is Dictionary or not _exact_keys(data.life, ["day_id", "last_settled_day", "action_seq", "last_receipt", "wallet", "accounts", "plots", "events", "daily_reports"]):
		return false
	var life: Dictionary = data.life
	if not _bounded_integer(life.day_id, 1, 1000000) or not _bounded_integer(life.last_settled_day, 0, 999999) or life.last_settled_day != life.day_id - 1:
		return false
	if not _bounded_integer(life.action_seq, 0, 1000000) or not life.last_receipt is Dictionary or not _valid_receipt(life.last_receipt, int(life.action_seq)):
		return false
	if not _bounded_integer(life.wallet, 0, 1000000000):
		return false
	if not life.accounts is Dictionary or not _exact_keys(life.accounts, ["market"]) or not life.accounts.market is Dictionary:
		return false
	var market: Dictionary = life.accounts.market
	if not _exact_keys(market, ["cash", "slots", "buy_quota"]) or not _bounded_integer(market.cash, 0, 1000000000) or not _valid_slots(market.slots, 48):
		return false
	if not market.buy_quota is Dictionary or not _exact_keys(market.buy_quota, ["clam", "snail", "kelp", "lettuce", "tomato"]):
		return false
	for quota in market.buy_quota.values():
		if not _bounded_integer(quota, 0, 12):
			return false
	if not life.plots is Dictionary or not _exact_keys(life.plots, ["plot_a", "plot_b"]):
		return false
	for plot in life.plots.values():
		if not plot is Dictionary or not _valid_plot(plot):
			return false
	if not life.events is Array or not _valid_events(life.events, int(life.day_id)):
		return false
	if not life.daily_reports is Array or not _valid_reports(life.daily_reports, int(life.day_id)):
		return false
	return true

static func migrate_legacy(data: Dictionary) -> Dictionary:
	if not validate_legacy(data):
		return {}
	var result := data.duplicate(true)
	if result.version == 1:
		result["location"] = "harbor"
	result["version"] = 3
	result["life"] = default_life()
	return result if validate_v3(result) else {}
