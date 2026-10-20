extends RefCounted

const Schema = preload("res://scripts/simulation/state_schema.gd")
const Inventory = preload("res://scripts/inventory/inventory_container.gd")
const Farming = preload("res://scripts/simulation/farming_rules.gd")
const Day = preload("res://scripts/simulation/day_rules.gd")
const Data = preload("res://scripts/harbor_data.gd")
const Catalog = preload("res://scripts/inventory/item_catalog.gd")
# Shared contract E: fixed prototype prices, never supplied by the caller.
const BUY_PRICES := {"lettuce_seed":5, "tomato_seed":8}
const SELL_PRICES := {"clam":8, "snail":10, "kelp":6, "lettuce":12, "tomato":20}

static func _failure(code: String) -> Dictionary:
	return {"ok":false, "code":code, "state":{}, "events":[]}

# JSON reloads integral numbers as floats. Compare their values while retaining
# strict types for strings/bools and recursive structure independent of key order.
static func _same_payload(left, right) -> bool:
	if (left is int or left is float) and (right is int or right is float):
		return left == right
	if typeof(left) != typeof(right):
		return false
	if left is Dictionary:
		if left.size() != right.size():
			return false
		for key in left:
			if not right.has(key) or not _same_payload(left[key], right[key]):
				return false
		return true
	if left is Array:
		if left.size() != right.size():
			return false
		for index in range(left.size()):
			if not _same_payload(left[index], right[index]):
				return false
		return true
	return left == right

static func plan(data: Dictionary, kind: String, args: Dictionary, request_id: int) -> Dictionary:
	if not Schema.validate_v4(data):
		return _failure("invalid_state")
	var sequence: int = data.life.action_seq
	if request_id <= sequence:
		var receipt: Dictionary = data.life.last_receipt
		if request_id == sequence and not receipt.is_empty() and receipt.kind == kind and _same_payload(receipt.args, args):
			return {"ok":true, "code":"ok", "state":data.duplicate(true), "events":[]}
		return _failure("stale_request")
	if request_id != sequence + 1:
		return _failure("invalid_request")
	if kind == "sleep":
		if not Schema._exact_keys(args, ["expected_day"]) or not (args.expected_day is int or args.expected_day is float) or args.expected_day is bool:
			return _failure("invalid_request")
		if not Schema._bounded_integer(args.expected_day, 1, 1000000):
			return _failure("invalid_day")
		var advanced: Dictionary = Day.advance(data, int(args.expected_day))
		if not advanced.ok:
			return advanced
		return _finish(advanced.state, kind, args, request_id, advanced.events)
	if kind in ["hoe", "plant", "water", "harvest"]:
		var farmed: Dictionary = Farming.act(data, kind, args)
		if not farmed.ok:
			return farmed
		return _finish(farmed.state, kind, args, request_id, farmed.events)
	if kind == "collect":
		return _collect(data, args, request_id)
	if kind != "trade":
		return _failure("unknown_action")
	if not Schema._exact_keys(args, ["direction", "account_id", "item_id", "amount"]):
		return _failure("invalid_request")
	for key in ["direction", "account_id", "item_id"]:
		if not args[key] is String:
			return _failure("invalid_request")
	if not (args.amount is int or args.amount is float) or args.amount is bool:
		return _failure("invalid_request")
	if args.account_id != "market":
		return _failure("unknown_account")
	if not Catalog.ITEMS.has(args.item_id):
		return _failure("unknown_item")
	if args.direction not in ["buy", "sell"]:
		return _failure("not_allowed")
	var buy: bool = args.direction == "buy"
	var prices: Dictionary = BUY_PRICES if buy else SELL_PRICES
	if not prices.has(args.item_id):
		return _failure("not_allowed")
	if not Schema._bounded_integer(args.amount, 1, 99):
		return _failure("invalid_amount")
	var amount: int = int(args.amount)
	var item: String = args.item_id
	var total: int = int(prices[item]) * amount
	var candidate := data.duplicate(true)
	var market: Dictionary = candidate.life.accounts.market
	var bag = Inventory.new(24)
	var stock = Inventory.new(48)
	if not bag.restore_slots(candidate.bag) or not stock.restore_slots(market.slots):
		return _failure("invalid_state")
	var source = stock if buy else bag
	var target = bag if buy else stock
	if source.count_item(item) < amount:
		return _failure("insufficient_stock")
	if target.space_for(item) < amount:
		return _failure("inventory_full")
	if (candidate.life.wallet if buy else market.cash) < total:
		return _failure("insufficient_funds")
	if not buy and market.buy_quota[item] < amount:
		return _failure("quota_exceeded")
	if not source.remove_item(item, amount) or target.add(item, amount) != amount:
		return _failure("invalid_state")
	candidate.bag = bag.snapshot()
	market.slots = stock.snapshot()
	candidate.life.wallet += -total if buy else total
	market.cash += total if buy else -total
	if not buy:
		market.buy_quota[item] -= amount
	# source/target follow cash; goods in this transfer move in the opposite direction.
	var event := {"day_id":int(candidate.life.day_id), "kind":"transfer",
		"source":"player" if buy else "market", "target":"market" if buy else "player",
		"items":{item:amount}, "cash":total, "reason":"trade"}
	return _finish(candidate, kind, args, request_id, [event])

static func _collect(data: Dictionary, args: Dictionary, request_id: int) -> Dictionary:
	if not Schema._exact_keys(args, ["pickup_id"]) or not args.pickup_id is String:
		return _failure("invalid_request")
	var item := ""
	for pickup in Data.pickups():
		if pickup.id == args.pickup_id:
			item = pickup.kind
			break
	if item == "":
		return _failure("invalid_request")
	if data.collected.has(args.pickup_id):
		return _failure("not_allowed")
	var candidate := data.duplicate(true)
	var bag = Inventory.new(24)
	if not bag.restore_slots(candidate.bag):
		return _failure("invalid_state")
	if bag.add(item, 1) != 1:
		return _failure("inventory_full")
	candidate.bag = bag.snapshot()
	candidate.collected[args.pickup_id] = true
	candidate.discovered[item] = true
	candidate.total_collected += 1
	return _finish(candidate, "collect", args, request_id, [{"day_id":int(candidate.life.day_id), "kind":"collect", "source":"environment", "target":"player", "items":{item:1}, "cash":0, "reason":"collect"}])

static func _finish(candidate: Dictionary, kind: String, args: Dictionary, request_id: int, events: Array) -> Dictionary:
	candidate.life.action_seq = request_id
	candidate.life.last_receipt = {"request_id":request_id, "kind":kind, "args":args.duplicate(true)}
	var numbered := events.duplicate(true)
	for index in range(numbered.size()):
		numbered[index].event_id = "a:%d:%d" % [request_id, index]
		candidate.life.events.append(numbered[index].duplicate(true))
	if candidate.life.events.size() > 256:
		candidate.life.events = candidate.life.events.slice(candidate.life.events.size() - 256)
	if not Schema.validate_v4(candidate):
		return _failure("invalid_state")
	return {"ok":true, "code":"ok", "state":candidate, "events":numbered}
