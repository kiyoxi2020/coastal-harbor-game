extends SceneTree

const State = preload("res://scripts/player_state.gd")
const Schema = preload("res://scripts/simulation/state_schema.gd")
const Save = preload("res://scripts/save_service.gd")
const Support = preload("res://tests/life_test_support.gd")
var support := Support.new()

func fixture(version: int) -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string("res://tests/fixtures/life_save_v%d.json" % version))

func check_invalid(id: String, data: Dictionary) -> void:
	var state = State.new()
	var before: Dictionary = state.to_data(Vector2.ZERO)
	var notifications := [0]
	state.changed.connect(func(): notifications[0] += 1)
	support.check(id, not State.valid_data(data) and not state.restore(data) and state.to_data(Vector2.ZERO) == before and notifications[0] == 0)

func metric(day: int) -> Dictionary:
	return {"day_id":day,"paid_staff":2,"batches":4,"produced":{"clam_salad":4},"sold":{"clam_salad":4},"sales_cash":120,"purchase_cash":40,"wage_cash":8,"cash_profit":72,"households_served":4,"households_total":5,"unmet_households":["hh_05"],"reasons":[]}

func _initialize() -> void:
	support.check("v6_public_api", Schema.new().has_method("validate_v6") and Schema.new().has_method("migrate_v5"))
	support.check("latest_save_version", State.SAVE_VERSION == 6 and State.SUPPORTED_VERSIONS == [1,2,3,4,5,6])
	var raw: Dictionary = State.new().to_data(Vector2(330,250))
	support.check("new_game_town", raw.version == 6 and raw.life.has("town"))
	if not raw.life.has("town"):
		print("TOWN_SCHEMA checks=", support.checks.size(), " passed=", support.passed())
		quit(1)
		return
	var town: Dictionary = raw.life.town
	support.check("new_game_exact_endowment", town.restaurant.cash == 300 and town.households.size() == 5 and town.external_fund == 10000 and town.supply_depot.stock == {"clam":60,"snail":60,"lettuce":60,"tomato":60} and town.initial_endowment.day_id == 1)
	support.check("restaurant_empty_48_slots", town.restaurant.slots.size() == 48 and town.restaurant.slots.all(func(s): return s == {"id":"","amount":0}))
	support.check("new_game_closed", town.restaurant.status == "closed" and town.restaurant.enabled == false and town.restaurant.employee_households == ["hh_01","hh_02"] and town.restaurant.last_metrics == {})
	support.check("new_game_valid", State.valid_data(raw) and Schema.validate_current(raw))
	var other: Dictionary = State.new().to_data(Vector2.ZERO)
	raw.life.town.households.hh_01.cash = 123
	raw.life.town.restaurant.slots[0] = {"id":"clam_salad","amount":2}
	support.check("new_game_deep_independent", other.life.town.households.hh_01.cash == 200 and other.life.town.restaurant.slots[0].id == "")
	var json: Dictionary = JSON.parse_string(JSON.stringify(raw))
	var restored = State.new()
	support.check("v6_json_roundtrip", restored.restore(json) and restored.life == json.life and restored.life.town.restaurant.slots[0].amount == 2 and restored.location == json.location)
	for version in [1,2,4]:
		var old := fixture(version)
		var old_before := old.duplicate(true)
		var migrated := State.migrate_data(old)
		support.check("migrate_v%d_latest" % version, migrated.get("version") == 6 and migrated.life.town.restaurant.cash == 300 and old == old_before)
	var v5 := fixture(4)
	v5.version = 5
	v5.location = "harbor_district"
	v5.life.day_id = 17
	v5.life.last_settled_day = 16
	v5.life.wallet = 519
	v5.bag[0] = {"id":"clam_salad","amount":3}
	support.check("v5_crafting_region_still_valid", Schema.validate_v5(v5))
	var before := v5.duplicate(true)
	var migrated: Dictionary = Schema.new().call("migrate_v5", v5)
	support.check("migration_actual_day", migrated.life.town.initial_endowment.day_id == 17)
	var projected := migrated.duplicate(true)
	projected.version = 5
	projected.life.erase("town")
	support.check("migration_preserves_all_v5", projected == before and v5 == before)
	migrated.life.town.restaurant.cash = 2
	migrated.life.town.households.hh_01.cash = 9
	migrated.life.town.supply_depot.stock.clam = 1
	var twice := State.migrate_data(migrated)
	support.check("migration_once_no_endowment_reset", twice == migrated and twice.life.town.restaurant.cash == 2)
	var path := support.temporary_directory("P10-schema")
	var service = Save.new(path)
	support.check("save_migrate_v5", service.write_save(v5) and service.read_save().data.version == 6)
	var saved: Dictionary = service.read_save().data
	support.check("save_restore_no_duplicate", service.write_save(saved) and service.read_save().data == saved)
	var valid := other.duplicate(true)
	valid.life.day_id = 2
	valid.life.last_settled_day = 1
	valid.life.town.restaurant.last_metrics = metric(1)
	valid.life.town.daily_metrics = [metric(1)]
	valid.life.town.food_history = [{"day_id":1,"served":4,"total":5}]
	support.check("valid_metrics_and_history", State.valid_data(valid))
	var transient := valid.duplicate(true)
	transient.life.day_id = 1
	transient.life.last_settled_day = 0
	support.check("source_day_transient_metrics", State.valid_data(transient))
	var loss := valid.duplicate(true)
	loss.life.town.restaurant.last_metrics.merge({"sold":{}, "sales_cash":0, "purchase_cash":0, "cash_profit":-8, "households_served":0, "unmet_households":["hh_01","hh_02","hh_03","hh_04","hh_05"]}, true)
	loss.life.town.daily_metrics[0] = loss.life.town.restaurant.last_metrics.duplicate(true)
	loss.life.town.food_history[0].served = 0
	support.check("cash_profit_can_be_negative", State.valid_data(loss))
	var funding := other.duplicate(true)
	funding.life.action_seq = 1
	funding.life.last_receipt = {"request_id":1,"kind":"fund_restaurant","args":{"amount":28}}
	support.check("v6_funding_receipt", State.valid_data(funding))
	var wrong_old := v5.duplicate(true)
	wrong_old.life.action_seq = 1
	wrong_old.life.last_receipt = funding.life.last_receipt.duplicate(true)
	support.check("v5_rejects_v6_receipt", not Schema.validate_v5(wrong_old))
	wrong_old = v5.duplicate(true)
	wrong_old.life.town = town.duplicate(true)
	check_invalid("v5_rejects_town", wrong_old)
	for field in ["restaurant","households","supply_depot","external_fund","initial_endowment","consumption_cursor","food_history","daily_metrics"]:
		var bad := other.duplicate(true)
		bad.life.town.erase(field)
		check_invalid("missing_town_" + field, bad)
	for value in [-1,1000000001,0.5,true,NAN]:
		var bad := other.duplicate(true)
		bad.life.town.restaurant.cash = value
		check_invalid("restaurant_cash_" + str(value), bad)
	var mutations := {
		"restaurant_slots_47":func(d): d.life.town.restaurant.slots.pop_back(),
		"restaurant_stock_second_truth":func(d): d.life.town.restaurant["stock"] = {},
		"unknown_status":func(d): d.life.town.restaurant.status = "bankrupt",
		"enabled_numeric":func(d): d.life.town.restaurant.enabled = 1,
		"quota_above_four":func(d): d.life.town.restaurant.supply_quota.clam = 5,
		"quota_missing":func(d): d.life.town.restaurant.supply_quota.erase("snail_stew"),
		"employee_unknown":func(d): d.life.town.restaurant.employee_households[0] = "hh_unknown",
		"employee_duplicate":func(d): d.life.town.restaurant.employee_households[1] = "hh_01",
		"employee_more_than_two":func(d): d.life.town.restaurant.employee_households.append("hh_03"),
		"household_workers_gt_members":func(d): d.life.town.households.hh_01.workers = 5,
		"household_negative_cash":func(d): d.life.town.households.hh_01.cash = -1,
		"household_fractional_members":func(d): d.life.town.households.hh_01.members = 1.5,
		"household_unbounded_members":func(d): d.life.town.households.hh_01.members = 1000001,
		"household_unknown_key":func(d): d.life.town.households.hh_01["stock"] = {},
		"depot_negative_stock":func(d): d.life.town.supply_depot.stock.clam = -1,
		"depot_unknown_stock":func(d): d.life.town.supply_depot.stock["wood"] = 1,
		"fund_negative":func(d): d.life.town.external_fund = -1,
		"cursor_out_of_bounds":func(d): d.life.town.consumption_cursor = 5,
		"endowment_future":func(d): d.life.town.initial_endowment.day_id = 2,
		"endowment_wrong_source":func(d): d.life.town.initial_endowment.cash.restaurant = 600
	}
	for id in mutations:
		var bad := other.duplicate(true)
		mutations[id].call(bad)
		check_invalid(id, bad)
	var metric_mutations := {
		"metrics_future":func(d): d.life.town.restaurant.last_metrics.day_id = 3,
		"metrics_negative_sales":func(d): d.life.town.restaurant.last_metrics.sales_cash = -1,
		"metrics_missing_field":func(d): d.life.town.restaurant.last_metrics.erase("paid_staff"),
		"metrics_unknown_output":func(d): d.life.town.restaurant.last_metrics.produced["wood"] = 1,
		"metrics_served_gt_total":func(d): d.life.town.restaurant.last_metrics.households_served = 6,
		"metrics_unknown_unmet":func(d): d.life.town.restaurant.last_metrics.unmet_households = ["hh_unknown"],
		"metrics_duplicate_unmet":func(d): d.life.town.restaurant.last_metrics.unmet_households = ["hh_05","hh_05"],
		"history_duplicate_day":func(d): d.life.town.food_history.append(d.life.town.food_history[0].duplicate(true)),
		"history_served_gt_total":func(d): d.life.town.food_history[0].served = 6,
		"daily_metrics_duplicate_day":func(d): d.life.town.daily_metrics.append(d.life.town.daily_metrics[0].duplicate(true)),
		"last_metrics_missing":func(d): d.life.town.restaurant.last_metrics = {}
	}
	for id in metric_mutations:
		var bad := valid.duplicate(true)
		metric_mutations[id].call(bad)
		check_invalid(id, bad)
	for reserved in ["player", "market", "restaurant", "supply_depot", "external_fund"]:
		var bad := other.duplicate(true)
		bad.life.town.households[reserved] = bad.life.town.households.hh_05
		bad.life.town.households.erase("hh_05")
		check_invalid("reserved_household_" + reserved, bad)
	var derived_mutations := {
		"produced_matches_batches":func(m): m.produced.clam_salad = 3,
		"wages_match_paid_staff":func(m): m.wage_cash = 7,
		"sold_matches_served":func(m): m.sold.clam_salad = 3,
		"sales_match_meal_prices":func(m): m.sales_cash = 121,
		"profit_matches_cash_flows":func(m): m.cash_profit = 71
	}
	for id in derived_mutations:
		var bad := valid.duplicate(true)
		derived_mutations[id].call(bad.life.town.restaurant.last_metrics)
		bad.life.town.daily_metrics[0] = bad.life.town.restaurant.last_metrics.duplicate(true)
		check_invalid(id, bad)
	var history_mutations := {
		"food_history_required":func(h): h.clear(),
		"food_history_matches_served":func(h): h[0].served = 3,
		"food_history_matches_total":func(h): h[0].total = 4,
		"food_history_matches_day":func(h): h[0].day_id = 2
	}
	for id in history_mutations:
		var bad := valid.duplicate(true)
		history_mutations[id].call(bad.life.town.food_history)
		check_invalid(id, bad)
	var rolling := valid.duplicate(true)
	rolling.life.day_id = 9
	rolling.life.last_settled_day = 8
	rolling.life.town.daily_metrics = []
	rolling.life.town.food_history = []
	for day in range(1,9):
		rolling.life.town.daily_metrics.append(metric(day))
		if day > 1: rolling.life.town.food_history.append({"day_id":day, "served":4, "total":5})
	rolling.life.town.restaurant.last_metrics = metric(8)
	support.check("food_history_exact_latest_seven", State.valid_data(rolling))
	var skipped := rolling.duplicate(true)
	skipped.life.town.food_history.pop_front()
	check_invalid("food_history_missing_recent_entry", skipped)
	var mixed := rolling.duplicate(true)
	mixed.life.town.food_history[0].day_id = 1
	check_invalid("food_history_keeps_latest_days", mixed)
	var corrupt := saved.duplicate(true)
	corrupt.life.town.restaurant.cash = -1
	var file_before := FileAccess.get_file_as_bytes(path.path_join("progress.json"))
	support.check("invalid_save_keeps_file", not service.write_save(corrupt) and FileAccess.get_file_as_bytes(path.path_join("progress.json")) == file_before)
	print("TOWN_SCHEMA checks=", support.checks.size(), " passed=", support.passed())
	quit(0 if support.passed() else 1)
