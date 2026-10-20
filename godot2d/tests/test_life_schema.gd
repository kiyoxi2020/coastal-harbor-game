extends SceneTree

const State = preload("res://scripts/player_state.gd")
const Save = preload("res://scripts/save_service.gd")
const Inventory = preload("res://scripts/inventory/inventory_container.gd")
const Support = preload("res://tests/life_test_support.gd")

var support := Support.new()

func fixture(path: String) -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string(path))

func write_json(path: String, value: Dictionary) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	file.store_string(JSON.stringify(value))
	file.close()

func _initialize() -> void:
	var state = State.new()
	support.check("save_version_current", State.SAVE_VERSION == 5)
	var all_new_items := true
	for id in ["lettuce_seed", "tomato_seed", "lettuce", "tomato"]:
		all_new_items = all_new_items and state.bag.add(id, 2) == 2
	support.check("new_item_add", all_new_items)
	var raw := state.to_data(Vector2(330, 250))
	support.check("new_item_roundtrip_valid", State.valid_data(raw))
	var restored = State.new()
	var roundtrip_ok: bool = restored.restore(raw) and restored.bag.count_item("lettuce_seed") == 2
	var restored_life = restored.get("life")
	var all_roundtrip := true
	for id in ["lettuce_seed", "tomato_seed", "lettuce", "tomato"]:
		all_roundtrip = all_roundtrip and restored.bag.count_item(id) == 2
	support.check("new_item_roundtrip", roundtrip_ok and all_roundtrip and restored_life is Dictionary and restored_life.get("wallet") == 100 and restored_life.get("day_id") == 1)
	var parsed: Dictionary = JSON.parse_string(JSON.stringify(raw))
	var parsed_state = State.new()
	support.check("json_roundtrip", parsed_state.restore(parsed) and parsed_state.bag.count_item("tomato") == 2)
	var restore_notifications := [0]
	parsed_state.changed.connect(func(): restore_notifications[0] += 1)
	support.check("restore_single_notification", parsed_state.restore(parsed) and restore_notifications[0] == 1)

	var v1 := fixture("res://tests/fixtures/life_save_v1.json")
	var migrated_v1 := State.migrate_data(v1)
	support.check("migration_v1", migrated_v1.get("version") == State.SAVE_VERSION and migrated_v1.get("location") == "harbor" and migrated_v1.bag == v1.bag and migrated_v1.total_collected == 1 and migrated_v1.has("life"))
	var v2 := fixture("res://tests/fixtures/life_save_v2.json")
	var migrated_v2 := State.migrate_data(v2)
	support.check("migration_v2", migrated_v2.get("version") == State.SAVE_VERSION and migrated_v2.get("location") == "house" and Vector2(migrated_v2.position[0], migrated_v2.position[1]) == Vector2(320, 328) and migrated_v2.chest == v2.chest and migrated_v2.collected == v2.collected)
	var tampered := v2.duplicate(true)
	tampered.chest[1] = {"id":"clam", "amount":1}
	support.check("legacy_tamper", State.migrate_data(tampered).is_empty())
	var legacy_bool := v2.duplicate(true)
	legacy_bool.collected.snail_a = 1
	support.check("legacy_collected_bool", State.migrate_data(legacy_bool).is_empty())
	legacy_bool = v2.duplicate(true)
	legacy_bool.discovered.snail = 1
	support.check("legacy_discovered_bool", State.migrate_data(legacy_bool).is_empty())

	var daily := support.make_state()
	daily.total_collected = 12
	daily.collected = {"clam_a":true, "snail_a":true}
	daily.discovered = {"clam":true, "snail":true, "kelp":true}
	daily.bag[0] = {"id":"clam", "amount":30}
	support.check("daily_history", State.valid_data(daily))
	var before := restored.to_data(Vector2(330, 250))
	var unknown := daily.duplicate(true)
	unknown.bag[0] = {"id":"wood", "amount":1}
	support.check("unknown_item", not restored.restore(unknown) and restored.to_data(Vector2(330, 250)) == before)

	if daily.has("life"):
		for field in ["wallet", "day_id"]:
			var invalid := daily.duplicate(true)
			if field == "wallet": invalid.life.wallet = -1
			else: invalid.life.day_id = 0
			support.check("invalid_" + field, not State.valid_data(invalid))
		var fractional := daily.duplicate(true)
		fractional.life.wallet = 0.5
		support.check("non_integer", not State.valid_data(fractional))
		var nan_value := daily.duplicate(true)
		nan_value.life.wallet = NAN
		support.check("nan", not State.valid_data(nan_value))
		var wrong_slots := daily.duplicate(true)
		wrong_slots.life.accounts.market.slots.pop_back()
		support.check("wrong_market_slots", not State.valid_data(wrong_slots))
	else:
		for id in ["invalid_wallet", "invalid_day_id", "non_integer", "nan", "wrong_market_slots"]:
			support.check(id, false)
	var Schema = load("res://scripts/simulation/state_schema.gd")
	var bool_collected := daily.duplicate(true)
	bool_collected.collected.clam_a = 1
	support.check("collected_bool", not Schema.validate_v4(bool_collected))
	var bool_discovered := daily.duplicate(true)
	bool_discovered.discovered.clam = 1
	support.check("discovered_bool", not Schema.validate_v4(bool_discovered))
	var bool_settled := daily.duplicate(true)
	bool_settled.life.last_settled_day = false
	support.check("settled_integer", not Schema.validate_v4(bool_settled))
	var bad_name := daily.duplicate(true)
	bad_name.player_name = "  海风  "
	support.check("schema_clean_name", not Schema.validate_v4(bad_name))
	var report_state := daily.duplicate(true)
	report_state.life.day_id = 2
	report_state.life.last_settled_day = 1
	report_state.life.daily_reports = [{"day_id":1,"cash_in":0,"cash_out":0,"pickups":7,"mature_plots":[],"summary":[]}]
	support.check("report_pickups_limit", not Schema.validate_v4(report_state))
	report_state.life.daily_reports[0].pickups = 1
	report_state.life.daily_reports[0].mature_plots = ["garden_a:0:0", "garden_a:0:0"]
	support.check("report_unique_plots", not Schema.validate_v4(report_state))
	var bad_event := daily.duplicate(true)
	bad_event.life.events = [{"event_id":"a:1:0", "day_id":1, "kind":"transfer", "source":"player", "target":"market", "items":{"wood":1}, "cash":8, "reason":"trade"}]
	support.check("event_unknown_item", not Schema.validate_v4(bad_event))

	var schema_exists := ResourceLoader.exists("res://scripts/simulation/state_schema.gd")
	support.check("schema_exists", schema_exists)
	if schema_exists:
		var schema = load("res://scripts/simulation/state_schema.gd")
		var life_a: Dictionary = schema.default_life()
		var life_b: Dictionary = schema.default_life()
		life_a.accounts.market.slots[0].amount = 1
		support.check("aliasing", life_b.accounts.market.slots[0].amount == 20)
	else:
		support.check("aliasing", false)

	var bag := Inventory.new(3)
	bag.add("clam", 2)
	before = {"slots":bag.snapshot()}
	support.check("remove_item_api", bag.has_method("remove_item"))
	support.check("atomic_remove_reject", bag.has_method("remove_item") and not bag.remove_item("clam", 3) and bag.snapshot() == before.slots)
	var signals := [0]
	bag.changed.connect(func(): signals[0] += 1)
	support.check("atomic_remove_success", bag.has_method("remove_item") and bag.remove_item("clam", 2) and bag.count_item("clam") == 0 and bag.snapshot()[0] == {"id":"", "amount":0} and signals[0] == 1)
	var slots := bag.snapshot()
	slots[0] = {"id":"tomato", "amount":2}
	support.check("restore_slots_api", bag.has_method("restore_slots"))
	var restore_slot_signals := [0]
	bag.changed.connect(func(): restore_slot_signals[0] += 1)
	support.check("restore_slots", bag.has_method("restore_slots") and bag.restore_slots(slots) and bag.count_item("tomato") == 2 and restore_slot_signals[0] == 1)
	slots[0].amount = 1
	support.check("restore_slots_deep_copy", bag.count_item("tomato") == 2)
	before = {"slots":bag.snapshot()}
	slots[1] = {"id":"wood", "amount":1}
	support.check("restore_slots_atomic", bag.has_method("restore_slots") and not bag.restore_slots(slots) and bag.snapshot() == before.slots)
	var multi := Inventory.new(3)
	multi.restore_slots([{"id":"clam","amount":1},{"id":"clam","amount":2},{"id":"","amount":0}])
	support.check("remove_slot_order", multi.remove_item("clam", 2) and multi.snapshot()[0] == {"id":"","amount":0} and multi.snapshot()[1] == {"id":"clam","amount":1})

	var path := support.temporary_directory("P02-future")
	DirAccess.make_dir_recursive_absolute(path)
	var future := daily.duplicate(true)
	future.version = 999
	write_json(path.path_join("progress.json"), future)
	write_json(path.path_join("progress.backup.json"), v2)
	var original := FileAccess.get_file_as_bytes(path.path_join("progress.json"))
	var service := Save.new(path)
	support.check("future_guard_read", service.read_save().get("future", false))
	support.check("future_guard_write", not service.write_save(daily) and FileAccess.get_file_as_bytes(path.path_join("progress.json")) == original)

	print("LIFE_SCHEMA checks=", support.checks.size(), " passed=", support.passed())
	quit(0 if support.passed() else 1)
