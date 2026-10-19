extends SceneTree

const State = preload("res://scripts/player_state.gd")
const Save = preload("res://scripts/save_service.gd")
const Support = preload("res://tests/life_test_support.gd")
const POINT := Vector2(330, 250)
var support = Support.new()
var Service
var Rules

class FakeSave extends RefCounted:
	var calls := 0
	var fail := false
	var captured: Dictionary = {}
	var observed_current
	var original: Dictionary = {}
	var saw_original := true
	func write_save(value: Dictionary) -> bool:
		calls += 1
		captured = value.duplicate(true)
		if observed_current != null:
			saw_original = observed_current.to_data(Vector2(330, 250)) == original
		return not fail

func check(id: String, passed: bool) -> void:
	support.check(id, passed)

func args(direction: String = "buy", item: String = "lettuce_seed", amount = 2) -> Dictionary:
	return {"direction":direction, "account_id":"market", "item_id":item, "amount":amount}

func attempt(state, save, payload: Dictionary, request: int = 1, kind: String = "trade") -> Dictionary:
	return Service.new(save).execute(state, POINT, kind, payload, request)

func reject(id: String, state, payload: Dictionary, code: String, request: int = 1, kind: String = "trade") -> void:
	var before: Dictionary = state.to_data(POINT)
	var save := FakeSave.new()
	var result: Dictionary = attempt(state, save, payload, request, kind)
	check(id, not result.ok and result.code == code and result.next_state == null and result.events == [] and not result.duplicate)
	check(id + "_atomic", state.to_data(POINT) == before and save.calls == 0)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var exists := ResourceLoader.exists("res://scripts/simulation/action_service.gd") and ResourceLoader.exists("res://scripts/simulation/life_rules.gd")
	check("transaction_modules_available", exists)
	if not exists:
		finish()
		return
	Service = load("res://scripts/simulation/action_service.gd")
	Rules = load("res://scripts/simulation/life_rules.gd")
	var state = State.new()
	var before: Dictionary = state.to_data(POINT)
	var save := FakeSave.new()
	save.observed_current = state
	save.original = before.duplicate(true)
	var payload := args()
	var result: Dictionary = attempt(state, save, payload)
	check("buy_two", result.ok and not result.duplicate and result.code == "ok" and result.next_state != null)
	if not result.ok:
		finish()
		return
	var next = result.next_state
	check("buy_balances", next.life.wallet == 90 and next.life.accounts.market.cash == 1010 and next.bag.count_item("lettuce_seed") == 2 and next.life.accounts.market.slots[0].amount == 18 and next.life.action_seq == 1)
	check("buy_conservation", next.life.wallet + next.life.accounts.market.cash == 1100 and next.bag.count_item("lettuce_seed") + next.life.accounts.market.slots[0].amount == 20 and next.chest.snapshot() == state.chest.snapshot())
	check("original_untouched_during_save", state.to_data(POINT) == before and save.saw_original)
	check("saved_candidate_valid", save.calls == 1 and save.captured == next.to_data(POINT) and State.valid_data(save.captured))
	check("single_transfer", result.events == [{"event_id":"a:1:0", "day_id":1, "kind":"transfer", "source":"player", "target":"market", "items":{"lettuce_seed":2}, "cash":10, "reason":"trade"}] and next.life.events == result.events)
	var dup: Dictionary = attempt(next, save, args())
	check("duplicate", dup.ok and dup.duplicate and dup.events == [] and save.calls == 1 and next.bag.count_item("lettuce_seed") == 2)
	var reordered := {"amount":2, "item_id":"lettuce_seed", "account_id":"market", "direction":"buy"}
	check("duplicate_key_order", attempt(next, save, reordered).duplicate and save.calls == 1)
	check("duplicate_numeric_json", attempt(next, save, args("buy", "lettuce_seed", 2.0)).duplicate and save.calls == 1)
	reject("id_collision", next, args("buy", "tomato_seed"), "stale_request")
	reject("skipped_id", state, args(), "invalid_request", 2)
	reject("zero_id", state, args(), "stale_request", 0)
	reject("negative_id", state, args(), "stale_request", -1)
	var second: Dictionary = attempt(next, save, args("buy", "tomato_seed", 1), 2)
	check("next_request", second.ok and second.next_state.life.action_seq == 2 and second.next_state.life.wallet == 82 and second.next_state.life.events.size() == 2)
	reject("old_request", second.next_state, args(), "stale_request")
	payload.amount = 9
	result.events[0].items.lettuce_seed = 9
	check("receipt_events_no_alias", next.life.last_receipt.args.amount == 2 and next.life.events[0].items.lettuce_seed == 2 and save.captured.life.last_receipt.args.amount == 1)
	next.bag.remove_item("lettuce_seed", 1)
	check("next_container_independent", state.to_data(POINT) == before)

	state = State.new()
	state.bag.add("clam", 2)
	result = attempt(state, FakeSave.new(), args("sell", "clam", 2))
	check("sell_clam", result.ok and result.next_state.life.wallet == 116 and result.next_state.life.accounts.market.cash == 984 and result.next_state.life.accounts.market.buy_quota.clam == 10 and result.next_state.bag.count_item("clam") == 0)
	check("sell_conservation", result.next_state.life.wallet + result.next_state.life.accounts.market.cash == 1100 and result.next_state.life.accounts.market.slots[2] == {"id":"clam", "amount":2} and result.events[0].source == "market" and result.events[0].target == "player" and result.events[0].cash == 16)
	for item in {"snail":10, "kelp":6, "lettuce":12, "tomato":20}:
		state = State.new()
		state.bag.add(item, 1)
		result = attempt(state, FakeSave.new(), args("sell", item, 1))
		check("sell_price_" + item, result.ok and result.next_state.life.wallet == 100 + {"snail":10, "kelp":6, "lettuce":12, "tomato":20}[item])
	state = State.new()
	state.life.wallet = 4
	reject("no_money", state, args("buy", "lettuce_seed", 1), "insufficient_funds")
	state = State.new()
	reject("no_stock", state, args("buy", "lettuce_seed", 21), "insufficient_stock")
	state.bag.add("kelp", 24 * 99)
	reject("full_bag", state, args("buy", "lettuce_seed", 1), "inventory_full")
	reject("stock_before_capacity", state, args("buy", "lettuce_seed", 21), "insufficient_stock")
	state.life.wallet = 0
	reject("capacity_before_funds", state, args(), "inventory_full")
	state = State.new()
	state.bag.add("clam", 1)
	state.life.accounts.market.cash = 7
	reject("market_poor", state, args("sell", "clam", 1), "insufficient_funds")
	state.life.accounts.market.buy_quota.clam = 0
	reject("funds_before_quota", state, args("sell", "clam", 1), "insufficient_funds")
	state.life.accounts.market.cash = 1000
	reject("quota", state, args("sell", "clam", 1), "quota_exceeded")
	for slot in state.life.accounts.market.slots:
		slot.id = "kelp"
		slot.amount = 99
	reject("full_market", state, args("sell", "clam", 1), "inventory_full")
	state = State.new()
	state.bag.add("clam", 13)
	reject("quota_no_partial", state, args("sell", "clam", 13), "quota_exceeded")
	state = State.new()
	state.chest.add("clam", 2)
	reject("chest_excluded", state, args("sell", "clam", 1), "insufficient_stock")
	for amount in [0, -1, 0.5, 100, NAN, INF]:
		reject("bad_amount_" + str(amount), state, args("buy", "lettuce_seed", amount), "invalid_amount")
	for amount in [true, "2", null]:
		reject("amount_type_" + str(amount), state, args("buy", "lettuce_seed", amount), "invalid_request")
	check("integer_float_amount", attempt(state, FakeSave.new(), args("buy", "lettuce_seed", 2.0)).ok)
	var bad := args()
	bad.price = 0
	reject("ui_price_rejected", state, bad, "invalid_request")
	bad = args()
	bad.erase("amount")
	reject("missing_arg", state, bad, "invalid_request")
	bad = args()
	bad.account_id = "other"
	bad.item_id = "wood"
	reject("account_priority", state, bad, "unknown_account")
	reject("unknown_item", state, args("buy", "wood", 1), "unknown_item")
	reject("buy_seafood", state, args("buy", "clam", 1), "not_allowed")
	reject("sell_seed", state, args("sell", "lettuce_seed", 1), "not_allowed")
	reject("invalid_direction", state, args("gift"), "not_allowed")
	reject("unknown_action", state, {}, "unknown_action", 1, "sleep")
	state.life.wallet = -1
	reject("invalid_current", state, args(), "invalid_state")
	state = State.new()
	state.life.wallet = 1000000000
	state.bag.add("clam", 1)
	reject("overflow_candidate", state, args("sell", "clam", 1), "invalid_state")

	state = State.new()
	before = state.to_data(POINT)
	save = FakeSave.new()
	save.fail = true
	result = attempt(state, save, args())
	check("save_failure", not result.ok and result.code == "save_failed" and result.next_state == null and result.events == [] and not result.duplicate and save.calls == 1 and state.to_data(POINT) == before)
	save.fail = false
	result = attempt(state, save, args())
	check("save_retry", result.ok and save.calls == 2 and result.next_state.life.wallet == 90 and result.next_state.life.action_seq == 1)

	var raw: Dictionary = state.to_data(POINT)
	var raw_before := raw.duplicate(true)
	var plan: Dictionary = Rules.plan(raw, "trade", args(), 1)
	check("pure_rule", plan.ok and plan.state.life.wallet == 90 and raw == raw_before)
	plan.state.bag[0].amount = 9
	plan.events[0].items.lettuce_seed = 9
	check("pure_rule_deep_copy", raw == raw_before and plan.state.life.events[0].items.lettuce_seed == 2)
	var failed: Dictionary = Rules.plan(raw, "trade", args("buy", "lettuce_seed", 21), 1)
	check("pure_failure", not failed.ok and failed.state == {} and failed.events == [] and raw == raw_before)
	var rolling = state
	for request in range(1, 261):
		rolling.life.wallet = 100 # Synthetic restock fixture, not an economic simulation.
		var buy := request % 2 == 1
		if not buy:
			# Seed sales are forbidden; alternate a legal raw sale with seed purchases.
			rolling.bag.add("kelp", 1)
		var p := args() if buy else args("sell", "kelp", 1)
		if buy:
			rolling.life.accounts.market.slots[0] = {"id":"lettuce_seed", "amount":20}
		else:
			rolling.life.accounts.market.buy_quota.kelp = 12
		var step: Dictionary = attempt(rolling, FakeSave.new(), p, request)
		if not step.ok:
			check("event_roll_step_" + str(request), false)
			break
		rolling = step.next_state
	check("event_retention", rolling.life.action_seq == 260 and rolling.life.events.size() == 256 and rolling.life.events[0].event_id == "a:5:0" and rolling.life.last_receipt.request_id == 260)

	var real_save = Save.new(support.temporary_directory("P03-real"))
	state = State.new()
	result = attempt(state, real_save, args())
	var loaded: Dictionary = real_save.read_save()
	var restored = State.new()
	check("disk_roundtrip", result.ok and loaded.ok and restored.restore(loaded.data) and JSON.parse_string(JSON.stringify(restored.to_data(POINT))) == JSON.parse_string(JSON.stringify(result.next_state.to_data(POINT))))
	var main: String = real_save.directory.path_join("progress.json")
	var disk_before := FileAccess.get_file_as_bytes(main)
	var mtime := FileAccess.get_modified_time(main)
	dup = attempt(restored, real_save, args())
	check("disk_duplicate", dup.ok and dup.duplicate and dup.events == [] and FileAccess.get_file_as_bytes(main) == disk_before and FileAccess.get_modified_time(main) == mtime and not FileAccess.file_exists(real_save.directory.path_join("progress.backup.json")))
	var continued: Dictionary = attempt(restored, real_save, args("buy", "tomato_seed", 1), 2)
	var reloaded: Dictionary = real_save.read_save()
	check("disk_continue_next_id", continued.ok and reloaded.ok and reloaded.data.life.action_seq == 2 and reloaded.data.life.wallet == 82 and reloaded.data.life.events.size() == 2 and FileAccess.file_exists(real_save.directory.path_join("progress.backup.json")))
	var future_dir: String = support.temporary_directory("P03-future")
	DirAccess.make_dir_recursive_absolute(future_dir)
	var future: Dictionary = state.to_data(POINT)
	future.version = 999
	var future_file := FileAccess.open(future_dir.path_join("progress.json"), FileAccess.WRITE)
	future_file.store_string(JSON.stringify(future))
	future_file.close()
	var future_bytes := FileAccess.get_file_as_bytes(future_dir.path_join("progress.json"))
	result = attempt(state, Save.new(future_dir), args())
	check("transaction_future_guard", not result.ok and result.code == "save_failed" and state.to_data(POINT) == before and FileAccess.get_file_as_bytes(future_dir.path_join("progress.json")) == future_bytes)
	var blocked_dir := support.temporary_directory("P03-blocked")
	var f := FileAccess.open(blocked_dir, FileAccess.WRITE)
	f.store_string("blocking file")
	f.close()
	result = attempt(state, Save.new(blocked_dir), args())
	check("real_save_failure", not result.ok and result.code == "save_failed" and state.to_data(POINT) == before)
	await world_checks()
	finish()

func world_checks() -> void:
	var world = load("res://scenes/harbor.tscn").instantiate()
	world.set_meta("save_directory", support.temporary_directory("P03-world"))
	world.set_meta("journal_test", true)
	world.set_meta("skip_verification", true)
	root.add_child(world)
	check("world_action_entry", world.has_method("perform_action") and world.has_method("refresh_life_views"))
	if world.has_method("perform_action"):
		var before: Dictionary = world.foraging.to_data(world.player.position)
		var result: Dictionary = world.perform_action("trade", args(), 1)
		check("world_session_guard", not result.ok and result.code == "not_allowed" and world.foraging.to_data(world.player.position) == before)
		check("world_start", world.start_new_game("事务测试"))
		world.release_input = false
		before = world.foraging.to_data(world.player.position)
		result = world.perform_action("trade", args(), 1)
		check("world_missing_market_guard", not result.ok and result.code == "not_allowed" and world.foraging.to_data(world.player.position) == before)
		# A synthetic page enables command-boundary checks only; this is not P06 UI acceptance.
		var page := Control.new()
		page.name = "TradePage"
		world.journal.get_node("Root").add_child(page)
		world.journal.mode = "trade"
		world.journal.root.show()
		page.show()
		var target: Node2D = world.exterior.get_node("InteractPoints/market")
		world.player.position = world.player.get_parent().to_local(target.global_position) + Vector2(28, 0)
		var fake := FakeSave.new()
		world.action_service = Service.new(fake)
		var old_state = world.foraging
		before = old_state.to_data(world.player.position)
		result = world.perform_action("trade", args(), 1)
		check("world_publish_after_save", result.ok and world.foraging == result.next_state and world.foraging != old_state and old_state.to_data(world.player.position) == before and fake.calls == 1 and world.foraging.life.wallet == 90)
		var active = world.foraging
		result = world.perform_action("trade", args(), 1)
		check("world_duplicate_no_replace", result.ok and result.duplicate and world.foraging == active and fake.calls == 1)
		var saved: Dictionary = active.to_data(world.player.position)
		fake.fail = true
		result = world.perform_action("trade", args(), 2)
		check("world_save_failure_atomic", not result.ok and result.code == "save_failed" and world.foraging == active and active.to_data(world.player.position) == saved and fake.calls == 2)
		check("world_failure_message", world.journal.note == "尚未保存，请重试；本次操作未生效。")
		fake.fail = false
		world.player.position += Vector2(1, 0)
		result = world.perform_action("trade", args(), 2)
		check("world_distance_guard", not result.ok and result.code == "not_allowed" and fake.calls == 2)
		world.player.position -= Vector2(1, 0)
		for gate in ["release", "transition", "panel", "modal", "page_hidden", "wrong_page", "indoor"]:
			world.release_input = gate == "release"
			world.home.transition.busy = gate == "transition"
			world.hud.panel.visible = gate == "panel"
			world.journal.pending = "quantity" if gate == "modal" else ""
			page.visible = gate != "page_hidden"
			world.journal.mode = "bag" if gate == "wrong_page" else "trade"
			world.foraging.location = "house" if gate == "indoor" else "harbor"
			var guarded: Dictionary = world.foraging.to_data(world.player.position)
			result = world.perform_action("trade", args(), 2)
			check("world_guard_" + gate, not result.ok and result.code == "not_allowed" and world.foraging.to_data(world.player.position) == guarded and fake.calls == 2)
		world.release_input = false
		world.home.transition.busy = false
		world.hud.panel.hide()
		world.journal.pending = ""
		world.journal.mode = "trade"
		world.foraging.location = "harbor"
		page.show()
		# Deleting the production target must revoke an already-open page's permission.
		var target_parent := target.get_parent()
		target_parent.remove_child(target)
		result = world.perform_action("trade", args(), 2)
		check("world_deleted_target_guard", not result.ok and result.code == "not_allowed" and fake.calls == 2)
		target_parent.add_child(target)
		result = world.perform_action("trade", args(), 2)
		check("world_retry_after_failure", result.ok and world.foraging.life.action_seq == 2 and world.foraging.life.wallet == 80 and fake.calls == 3)
		world.persistence_enabled = false
		result = world.perform_action("trade", args(), 1)
		check("world_nonpersistent_guard", not result.ok and result.code == "not_allowed")
		var replacement = State.new()
		replacement.bag.add("lettuce_seed", 3)
		world._set_state(replacement)
		world.journal.show_page("bag")
		check("world_replaced_state_ui", world.journal.container("bag") == replacement.bag and world.journal.bag_page.get_node("BagGrid/bag_0/Amount").text == "3")
	world.journal.dismiss()
	paused = false
	world.queue_free()
	await process_frame

func finish() -> void:
	var count: int = support.checks.size()
	var failures: int = support.checks.values().count(false)
	print("LIFE_TRANSACTIONS ", count - failures, "/", count, " failures=", failures)
	quit(0 if failures == 0 else 1)
