extends RefCounted

const Schema = preload("res://scripts/simulation/state_schema.gd")
const Inventory = preload("res://scripts/inventory/inventory_container.gd")
const Farming = preload("res://scripts/simulation/farming_rules.gd")
const Crafting = preload("res://scripts/simulation/crafting_rules.gd")
const Recipes = preload("res://scripts/simulation/recipe_catalog.gd")
const Transactions = preload("res://scripts/simulation/account_transactions.gd")
const Day = preload("res://scripts/simulation/day_rules.gd")
const Data = preload("res://scripts/harbor_data.gd")
const Catalog = preload("res://scripts/inventory/item_catalog.gd")
# Shared contract E: fixed prototype prices, never supplied by the caller.
const BUY_PRICES := {"lettuce_seed":5, "tomato_seed":8}
const SUPPLY_PRICES := {"clam":8,"snail":10,"lettuce":12,"tomato":20,"clam_salad":24,"snail_stew":36}
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
	if not Schema.validate_current(data):
		return _failure("invalid_state")
	var sequence: int = data.life.action_seq
	if request_id <= sequence:
		var receipt: Dictionary = data.life.last_receipt
		if request_id == sequence and not receipt.is_empty() and receipt.kind == kind and _same_payload(receipt.args, args):
			return {"ok":true, "code":"ok", "state":data.duplicate(true), "events":[]}
		return _failure("stale_request")
	if request_id != sequence + 1:
		return _failure("invalid_request")
	if kind == "supply":
		return _supply(data,args,request_id)
	if kind == "fund_restaurant":
		return _fund(data,args,request_id)
	if kind == "open_restaurant":
		return _open_restaurant(data,args,request_id)
	if kind == "sleep":
		if not Schema._exact_keys(args, ["expected_day"]) or not (args.expected_day is int or args.expected_day is float) or args.expected_day is bool:
			return _failure("invalid_request")
		if not Schema._bounded_integer(args.expected_day, 1, 1000000):
			return _failure("invalid_day")
		var advanced: Dictionary = Day.advance(data, int(args.expected_day))
		if not advanced.ok:
			return advanced
		return _finish(advanced.state, kind, args, request_id, advanced.events)
	if kind == "craft":
		if not Schema._exact_keys(args,["recipe_id","batches"]) or not args.recipe_id is String or not (args.batches is int or args.batches is float) or args.batches is bool:
			return _failure("invalid_request")
		if not Schema._bounded_integer(args.batches,1,20):return _failure("invalid_amount")
		var crafted:Dictionary=Crafting.craft(data,args.recipe_id,int(args.batches))
		if not crafted.ok:return crafted
		return _finish(crafted.state,kind,args,request_id,crafted.events)
	if kind in ["hoe", "plant", "water", "harvest", "fertilize"]:
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
	var code:=Transactions.exchange(candidate,"player" if buy else "market","market" if buy else "player",item,amount,total,{} if buy else market.buy_quota)
	if code!="ok":return _failure(code)
	# source/target follow cash; goods in this transfer move in the opposite direction.
	var event := {"day_id":int(candidate.life.day_id), "kind":"transfer",
		"source":"player" if buy else "market", "target":"market" if buy else "player",
		"items":{item:amount}, "cash":total, "reason":"trade"}
	return _finish(candidate, kind, args, request_id, [event])

static func _supply(data:Dictionary,args:Dictionary,request_id:int) -> Dictionary:
	if not Schema._exact_keys(args,["account_id","item_id","amount"]):return _failure("invalid_request")
	if not args.account_id is String or not args.item_id is String or not (args.amount is int or args.amount is float) or args.amount is bool:return _failure("invalid_request")
	if args.account_id!="restaurant" or not data.life.has("town"):return _failure("unknown_account")
	if not Catalog.ITEMS.has(args.item_id):return _failure("unknown_item")
	if not SUPPLY_PRICES.has(args.item_id):return _failure("not_allowed")
	if not Schema._bounded_integer(args.amount,1,99):return _failure("invalid_amount")
	var candidate=data.duplicate(true)
	var amount=int(args.amount)
	var total=int(SUPPLY_PRICES[args.item_id])*amount
	var code:=Transactions.exchange(candidate,"restaurant","player",args.item_id,amount,total,candidate.life.town.restaurant.supply_quota)
	if code!="ok":return _failure(code)
	return _finish(candidate,"supply",args,request_id,[{"day_id":int(data.life.day_id),"kind":"transfer","source":"restaurant","target":"player","items":{args.item_id:amount},"cash":total,"reason":"restaurant_supply"}])

static func _fund(data:Dictionary,args:Dictionary,request_id:int) -> Dictionary:
	if not Schema._exact_keys(args,["amount"]) or not (args.amount is int or args.amount is float) or args.amount is bool:return _failure("invalid_request")
	if not Schema._bounded_integer(args.amount,1,1000):return _failure("invalid_amount")
	if not data.life.has("town"):return _failure("unknown_account")
	var candidate=data.duplicate(true)
	var code:=Transactions.move_cash(candidate,"player","restaurant",int(args.amount))
	if code!="ok":return _failure(code)
	return _finish(candidate,"fund_restaurant",args,request_id,[{"day_id":int(data.life.day_id),"kind":"transfer","source":"player","target":"restaurant","items":{},"cash":int(args.amount),"reason":"restaurant_funding"}])

static func _open_restaurant(data:Dictionary,args:Dictionary,request_id:int) -> Dictionary:
	if not args.is_empty():return _failure("invalid_request")
	if not data.life.has("town"):return _failure("not_allowed")
	var restaurant:Dictionary=data.life.town.restaurant
	if restaurant.enabled or restaurant.status!="closed":return _failure("not_allowed")
	var inventory=Inventory.new(48)
	if not inventory.restore_slots(restaurant.slots):return _failure("invalid_state")
	var can_open=false
	for recipe_id in ["clam_salad","snail_stew"]:
		var recipe:Dictionary=Recipes.get_recipe(recipe_id)
		var enough=true
		for item in recipe.inputs:
			if inventory.count_item(item)<int(recipe.inputs[item]):enough=false;break
		if enough:can_open=true;break
	if not can_open:return _failure("insufficient_stock")
	var candidate=data.duplicate(true)
	restaurant=candidate.life.town.restaurant
	restaurant.enabled=true;restaurant.status="trial";restaurant.good_days=0;restaurant.bad_days=0
	return _finish(candidate,"open_restaurant",args,request_id,[{"day_id":int(data.life.day_id),"kind":"restaurant_status","source":"closed","target":"trial","items":{},"cash":0,"reason":"open_restaurant"}])

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
	if not _trim_events(candidate.life.events,int(candidate.life.day_id)):
		return _failure("invalid_state")
	if not Schema.validate_current(candidate):
		return _failure("invalid_state")
	return {"ok":true, "code":"ok", "state":candidate, "events":numbered}

# Current-day money must survive the bounded audit log until reports are settled.
# On overflow, evict old/nonfinancial entries first; if all entries are financial,
# compact equivalent transfers into an explicit summary without losing totals.
static func _trim_events(events:Array,current_day:int) -> bool:
	while events.size()>256:
		var removable=-1
		for i in range(events.size()):
			if events[i].day_id!=current_day or events[i].kind not in ["transfer","transfer_summary"]:
				removable=i;break
		if removable>=0:
			events.remove_at(removable);continue
		var grouped:Dictionary={}
		var merged=false
		for i in range(events.size()):
			var event:Dictionary=events[i]
			var key="summary:%d:%s:%s:%s"%[current_day,event.source,event.target,event.reason]
			if not grouped.has(key):
				grouped[key]=i;continue
			var first:Dictionary=events[grouped[key]]
			first.kind="transfer_summary";first.event_id=key
			first.cash+=event.cash
			for item in event.items:first.items[item]=int(first.items.get(item,0))+int(event.items[item])
			events.remove_at(i);merged=true;break
		if not merged:return false
	return true
