extends RefCounted
const Farming = preload("res://scripts/simulation/farming_rules.gd")
const Schema = preload("res://scripts/simulation/state_schema.gd")
const Inventory = preload("res://scripts/inventory/inventory_container.gd")

static func _failure(code: String) -> Dictionary:
	return {"ok":false, "code":code, "state":{}, "events":[]}

static func advance(data: Dictionary, expected_day: int) -> Dictionary:
	if not Schema.validate_v4(data):
		return _failure("invalid_state")
	if expected_day != data.life.day_id:
		return _failure("invalid_day")
	var grown: Dictionary = Farming.grow(data)
	if not grown.ok:
		return grown
	var candidate: Dictionary = grown.state
	var life: Dictionary = candidate.life
	var market: Dictionary = life.accounts.market
	var stock = Inventory.new(48)
	if not stock.restore_slots(market.slots):
		return _failure("invalid_state")
	var events: Array = grown.events.duplicate(true)
	var mature_plots: Array[String] = []
	for event in grown.events:
		if event.reason == "mature":
			mature_plots.append(event.target)
	var added := 0
	for item in ["lettuce_seed", "tomato_seed"]:
		var amount: int = maxi(0, 20 - stock.count_item(item))
		if amount == 0:
			continue
		if stock.add(item, amount) != amount:
			return _failure("inventory_full")
		added += amount
		events.append({"day_id":expected_day, "kind":"external_restock", "source":"external", "target":"market", "items":{item:amount}, "cash":0, "reason":"daily_seed_restock"})
	market.slots = stock.snapshot()
	for item in market.buy_quota:
		market.buy_quota[item] = 12
	var cash_in := 0
	var cash_out := 0
	for event in life.events:
		if event.day_id != expected_day or event.kind != "transfer":
			continue
		if event.target == "player":
			cash_in += int(event.cash)
		if event.source == "player":
			cash_out += int(event.cash)
	var pickups: int = candidate.collected.size()
	life.daily_reports.append({"day_id":expected_day, "cash_in":cash_in, "cash_out":cash_out,
		"pickups":pickups, "mature_plots":mature_plots, "summary":["今日采集%d个；明日六处采点已刷新。" % pickups, "市场补充种子%d颗，收购额度已恢复。" % added, "新成熟作物%d格。" % mature_plots.size()]})
	if life.daily_reports.size() > 30:
		life.daily_reports = life.daily_reports.slice(life.daily_reports.size() - 30)
	candidate.collected.clear()
	life.day_id = expected_day + 1
	life.last_settled_day = expected_day
	events.append({"day_id":expected_day, "kind":"sleep", "source":"player", "target":"player", "items":{}, "cash":0, "reason":"sleep"})
	if not Schema.validate_v4(candidate):
		return _failure("invalid_state")
	return {"ok":true, "code":"ok", "state":candidate, "events":events}
