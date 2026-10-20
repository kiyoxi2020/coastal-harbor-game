extends SceneTree
const State = preload("res://scripts/player_state.gd")
const Service = preload("res://scripts/simulation/action_service.gd")
const Rules = preload("res://scripts/simulation/life_rules.gd")
const Save = preload("res://scripts/save_service.gd")
const Support = preload("res://tests/life_test_support.gd")
var World = load("res://scripts/harbor.gd")
const POINT := Vector2(330, 250)
var support = Support.new()
var Day

class FakeSave extends RefCounted:
	var fail := false
	var calls := 0
	var captured: Dictionary = {}
	func write_save(value: Dictionary) -> bool:
		calls += 1
		captured = value.duplicate(true)
		return not fail

func check(id: String, passed: bool) -> void:
	support.check(id, passed)

func execute(state, kind: String, args: Dictionary, id: int, save = null) -> Dictionary:
	return Service.new(FakeSave.new() if save == null else save).execute(state, POINT, kind, args, id)

func reject(id: String, state, kind: String, args: Dictionary, code: String) -> void:
	var before: Dictionary = state.to_data(POINT)
	var save := FakeSave.new()
	var r: Dictionary = execute(state, kind, args, int(state.life.action_seq) + 1, save)
	check(id, not r.ok and r.code == code and r.next_state == null and r.events == [] and not r.duplicate and save.calls == 0 and state.to_data(POINT) == before)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var s = State.new()
	var before: Dictionary = s.to_data(POINT)
	check("unknown_pickup_memory", not s.collect("a", "clam") and s.to_data(POINT) == before)
	check("mismatched_pickup_memory", not s.collect("clam_a", "kelp") and s.to_data(POINT) == before)
	check("day_rules_available", ResourceLoader.exists("res://scripts/simulation/day_rules.gd"))
	check("path_resolver_available", World.has_method("resolve_save_options"))
	if support.checks.values().has(false):
		finish()
		return
	Day = load("res://scripts/simulation/day_rules.gd")
	s = State.new()
	s.collect("clam_a", "clam")
	s.collect("snail_a", "snail")
	s.life.accounts.market.slots[0].amount = 18
	s.life.accounts.market.cash = 1010
	s.life.accounts.market.buy_quota.clam = 1
	before = s.to_data(POINT)
	var save := FakeSave.new()
	var r: Dictionary = execute(s, "sleep", {"expected_day":1}, 1, save)
	check("next_day_refresh", r.ok)
	if not r.ok:
		finish()
		return
	var next = r.next_state
	check("day_fields", next.life.day_id == 2 and next.life.last_settled_day == 1 and next.life.action_seq == 1)
	check("history_kept", next.collected == {} and next.total_collected == 2 and next.discovered == {"clam":true, "snail":true} and next.bag.snapshot() == s.bag.snapshot())
	check("market_refresh", next.life.accounts.market.cash == 1010 and next.life.accounts.market.slots[0].amount == 20 and next.life.accounts.market.slots[1].amount == 20 and next.life.accounts.market.buy_quota.clam == 12)
	var restocks: Array = r.events.filter(func(e): return e.kind == "external_restock")
	check("actual_restock_only", restocks.size() == 1 and restocks[0].items == {"lettuce_seed":2} and restocks[0].cash == 0 and restocks[0].source == "external" and restocks[0].target == "market")
	check("source_day_events", r.events.all(func(e): return e.day_id == 1) and r.events[0].event_id == "a:1:0" and r.events[-1].kind == "sleep")
	check("source_day_report", next.life.daily_reports.size() == 1 and next.life.daily_reports[0].day_id == 1 and next.life.daily_reports[0].pickups == 2 and next.life.daily_reports[0].cash_in == 0 and next.life.daily_reports[0].cash_out == 0 and next.life.daily_reports[0].mature_plots == [])
	check("sleep_original_unchanged", s.to_data(POINT) == before and save.calls == 1)
	var dup: Dictionary = execute(next, "sleep", {"expected_day":1}, 1, save)
	check("duplicate_sleep", dup.ok and dup.duplicate and save.calls == 1 and next.life.day_id == 2 and next.life.daily_reports.size() == 1)
	reject("stale_day", next, "sleep", {"expected_day":1}, "invalid_day")
	reject("future_day", next, "sleep", {"expected_day":3}, "invalid_day")
	for invalid in [{}, {"expected_day":"2"}, {"expected_day":true}, {"expected_day":2, "extra":1}]:
		reject("sleep_args_" + str(invalid), next, "sleep", invalid, "invalid_request")
	for invalid in [0, 2.5, NAN, INF]:
		reject("sleep_day_" + str(invalid), next, "sleep", {"expected_day":invalid}, "invalid_day")
	r = execute(next, "collect", {"pickup_id":"clam_a"}, 2)
	check("new_pickup", r.ok and r.next_state.total_collected == 3 and r.next_state.bag.count_item("clam") == 2 and r.next_state.collected == {"clam_a":true})
	check("collect_event", r.events.size() == 1 and r.events[0].items == {"clam":1} and r.events[0].cash == 0 and r.events[0].day_id == 2)
	var collected = r.next_state
	reject("already_collected", collected, "collect", {"pickup_id":"clam_a"}, "not_allowed")
	for invalid in [{}, {"pickup_id":1}, {"pickup_id":"clam_a", "kind":"kelp"}]:
		reject("collect_args_" + str(invalid), next, "collect", invalid, "invalid_request")
	reject("unknown_pickup", next, "collect", {"pickup_id":"a"}, "invalid_request")
	var full = State.new()
	full.bag.add("kelp", 24 * 99)
	reject("collect_full", full, "collect", {"pickup_id":"clam_a"}, "inventory_full")
	for kind in ["sleep", "collect"]:
		save = FakeSave.new()
		save.fail = true
		var payload := {"expected_day":1} if kind == "sleep" else {"pickup_id":"kelp_a"}
		before = s.to_data(POINT)
		r = execute(s, kind, payload, 1, save)
		check(kind + "_save_failure", not r.ok and r.code == "save_failed" and r.next_state == null and r.events == [] and s.to_data(POINT) == before and save.calls == 1)
		save.fail = false
		r = execute(s, kind, payload, 1, save)
		check(kind + "_same_id_retry", r.ok and r.next_state.life.action_seq == 1 and save.calls == 2)

	# Real transaction events determine the source day's cash totals exactly once.
	var trades = State.new()
	r = execute(trades, "trade", {"direction":"buy", "account_id":"market", "item_id":"lettuce_seed", "amount":2}, 1)
	trades = r.next_state
	r = execute(trades, "collect", {"pickup_id":"clam_a"}, 2)
	trades = r.next_state
	r = execute(trades, "trade", {"direction":"sell", "account_id":"market", "item_id":"clam", "amount":1}, 3)
	trades = r.next_state
	r = execute(trades, "sleep", {"expected_day":1}, 4)
	check("report_cash", r.ok and r.next_state.life.wallet == 98 and r.next_state.life.daily_reports[0].cash_in == 8 and r.next_state.life.daily_reports[0].cash_out == 10 and r.next_state.life.daily_reports[0].pickups == 1)
	r = execute(r.next_state, "sleep", {"expected_day":2}, 5)
	check("report_not_recounted", r.ok and r.next_state.life.wallet == 98 and r.next_state.life.daily_reports[1].cash_in == 0 and r.next_state.life.daily_reports[1].cash_out == 0)
	var untouched: Dictionary = s.to_data(POINT)
	var planned: Dictionary = Day.advance(untouched, 1)
	check("day_rule_pure", planned.ok and untouched == s.to_data(POINT))
	planned.state.life.accounts.market.slots[0].amount = 1
	check("day_rule_no_alias", untouched == s.to_data(POINT))
	check("no_restock_at_target", execute(State.new(), "sleep", {"expected_day":1}, 1).events.filter(func(e): return e.kind == "external_restock").is_empty())
	var stocked = State.new()
	stocked.life.accounts.market.slots[0].amount = 25
	r = execute(stocked, "sleep", {"expected_day":1}, 1)
	check("no_seed_removal", r.ok and r.next_state.life.accounts.market.slots[0].amount == 25)
	stocked = State.new()
	for slot in stocked.life.accounts.market.slots:
		slot.id = "kelp"
		slot.amount = 99
	reject("restock_capacity_atomic", stocked, "sleep", {"expected_day":1}, "inventory_full")
	var days = State.new()
	for d in range(1, 33):
		r = execute(days, "sleep", {"expected_day":d}, d)
		if not r.ok:
			check("daily_step_" + str(d), false)
			break
		days = r.next_state
	check("reports_retained_30", days.life.day_id == 33 and days.life.daily_reports.size() == 30 and days.life.daily_reports[0].day_id == 3 and days.life.daily_reports[-1].day_id == 32)
	var real_save = Save.new(support.temporary_directory("P04-real"))
	r = execute(s, "sleep", {"expected_day":1}, 1, real_save)
	var restored = State.new()
	check("real_reload", r.ok and restored.restore(real_save.read_save().data) and restored.life.day_id == 2)
	var data_before: Dictionary = restored.to_data(POINT)
	await create_timer(0.05).timeout
	check("no_offline_progress", restored.to_data(POINT) == data_before)
	dup = execute(restored, "sleep", {"expected_day":1}, 1, real_save)
	check("reload_duplicate_sleep", dup.ok and dup.duplicate and restored.life.day_id == 2)
	path_checks()
	await scene_checks()
	finish()

func path_checks() -> void:
	var injected := "/private/tmp/coastal-P04-meta"
	var valid := "/private/tmp/coastal-P04-cli"
	var opts: Dictionary = World.resolve_save_options(PackedStringArray(["--test-save-directory=" + valid]))
	check("path_cli", opts.error == "" and opts.directory == valid)
	opts = World.resolve_save_options(PackedStringArray([]), injected)
	check("path_metadata", opts.directory == injected and opts.error == "")
	opts = World.resolve_save_options(PackedStringArray(["--test-save-directory=" + valid]), injected)
	check("path_meta_priority", opts.directory == injected and opts.error == "")
	check("path_default", World.resolve_save_options(PackedStringArray([])).directory == "user://coastal-progress")
	check("path_old_verify", World.resolve_save_options(PackedStringArray([]), "", true).directory.begins_with("/private/tmp/coastal-"))
	for path in ["", "user://coastal-progress", "/tmp/wrong", "/private/tmp/coastal-x/../../outside", "/private/tmp/coastal-"]:
		opts = World.resolve_save_options(PackedStringArray(["--test-save-directory=" + path]), injected)
		check("path_reject_" + path, opts.error != "" and opts.directory.begins_with("/private/tmp/coastal-invalid-"))
	opts = World.resolve_save_options(PackedStringArray(["--test-save-directory"]))
	check("path_missing_value", opts.error != "")

func scene_checks() -> void:
	var world = load("res://scenes/harbor.tscn").instantiate()
	world.set_meta("save_directory", support.temporary_directory("P04-world"))
	world.set_meta("journal_test", true)
	world.set_meta("skip_verification", true)
	world.get_node("Journal/Root/SleepPage/Surface/Body").text = "自定义床边说明"
	world.get_node("Journal/Root/SleepPage/Surface/Title").text = "休息 · 第{day}日"
	root.add_child(world)
	check("sleep_page_exists", world.journal.has_node("Root/SleepPage/Surface/Confirm"))
	check("start", world.start_new_game("换日测试"))
	world.release_input = false
	world.player.position = Vector2(244, 330)
	var save := FakeSave.new()
	save.fail = true
	world.action_service = Service.new(save)
	var before: Dictionary = world.foraging.to_data(world.player.position)
	var r: Dictionary = world.perform_action("collect", {"pickup_id":"clam_a"}, 1)
	check("scene_collect_failure_visible", not r.ok and r.code == "save_failed" and world.pickup_nodes.clam_a.visible and world.foraging.to_data(world.player.position) == before)
	save.fail = false
	world.pickup_nodes.clam_a.kind = "kelp"
	r = world.perform_action("collect", {"pickup_id":"clam_a"}, 1)
	check("scene_kind_mismatch_rejected", not r.ok and r.code == "not_allowed" and world.pickup_nodes.clam_a.visible and world.foraging.to_data(world.player.position) == before)
	world.pickup_nodes.clam_a.kind = "clam"
	world.player.position = Vector2(269, 330)
	r = world.perform_action("collect", {"pickup_id":"clam_a"}, 1)
	check("scene_collect_distance", not r.ok and r.code == "not_allowed")
	world.player.position = Vector2(244, 330)
	r = world.perform_action("sleep", {"expected_day":1}, 1)
	check("scene_outdoor_sleep_denied", not r.ok and r.code == "not_allowed")
	r = world.perform_action("collect", {"pickup_id":"clam_a"}, 1)
	check("scene_collect_success_hidden", r.ok and not world.pickup_nodes.clam_a.visible and world.foraging.total_collected == 1)
	world.journal.show_page("bag")
	r = world.perform_action("collect", {"pickup_id":"snail_a"}, 2)
	check("scene_panel_blocks_collect", not r.ok and r.code == "not_allowed")
	world.journal.dismiss()
	world.release_input = false
	world.home.switch_room("house", Vector2(244, 240))
	var bed_position: Vector2 = world.player.position
	check("bedside_safe_excludes_player", world.home.safe_position("house", bed_position) == bed_position)
	world.journal.show_page("sleep")
	check("sleep_inspector_template", world.journal.get_node("Root/SleepPage/Surface/Body").text == "自定义床边说明" and world.journal.get_node("Root/SleepPage/Surface/Title").text == "休息 · 第1日")
	var snapshot: Dictionary = world.foraging.to_data(bed_position)
	world.player.position += Vector2(1, 0)
	r = world.perform_action("sleep", {"expected_day":1}, 2)
	check("scene_sleep_distance", not r.ok and r.code == "not_allowed")
	world.player.position = bed_position
	var bed: Node2D = world.home.interior.get_node("InteractPoints/bed")
	var bed_parent := bed.get_parent()
	bed_parent.remove_child(bed)
	r = world.perform_action("sleep", {"expected_day":1}, 2)
	check("scene_sleep_missing_target", not r.ok and r.code == "not_allowed")
	bed_parent.add_child(bed)
	world.journal.close_menu()
	check("cancel_sleep_no_effect", world.foraging.to_data(bed_position) == snapshot and world.journal.mode == "" and world.release_input and not paused)
	world.release_input = false
	world.journal.show_page("sleep")
	save.fail = true
	world.journal.confirm_sleep()
	check("scene_sleep_failure_stays", world.journal.mode == "sleep" and paused and world.foraging.to_data(bed_position) == snapshot and world.journal.get_node("Root/SleepPage/Surface/Body").text.contains("尚未保存"))
	var retry_id: int = world.journal.sleep_request_id
	save.fail = false
	world.journal.confirm_sleep()
	check("scene_sleep_success", world.journal.mode == "daily" and paused and world.foraging.life.day_id == 2 and world.foraging.life.action_seq == retry_id and world.foraging.location == "house" and world.player.position == bed_position and world.pickup_nodes.clam_a.visible and not world.home.transition.busy)
	check("bedside_saved_position", save.captured.position == [bed_position.x, bed_position.y])
	check("scene_report_visible", world.journal.get_node("Root/DailyPage/Surface/Title").text.contains("第1日") and world.journal.get_node("Root/DailyPage/Surface/Title").text.contains("第2日"))
	world.journal.confirm_sleep()
	check("double_confirm_once", world.foraging.life.day_id == 2)
	world.hud.dismiss()
	world.journal.dismiss()
	paused = false
	world.queue_free()
	await process_frame

func finish() -> void:
	var count: int = support.checks.size()
	var failures: int = support.checks.values().count(false)
	print("LIFE_DAY ", count - failures, "/", count, " failures=", failures)
	quit(0 if failures == 0 else 1)
