extends SceneTree

class ToolCatalog:
	extends RefCounted
	func stack_limit(id: String) -> int:
		return 1 if id == "tool" else 0

var checks: Dictionary = {}
var notifications := 0

func check(label: String, passed: bool) -> void:
	checks[label] = passed
	print(("PASS " if passed else "FAIL ")+label)

func _initialize() -> void:
	var script = load("res://scripts/inventory/inventory_container.gd")
	if script == null:
		push_error("Missing inventory container")
		quit(1)
		return
	var bag = script.new(2)
	bag.changed.connect(func(): notifications += 1)
	check("initial_add", bag.add("clam", 98) == 98)
	check("overflow_to_empty_slot", bag.add("clam", 2) == 2)
	check("fill_existing_first", bag.snapshot() == [{"id":"clam", "amount":99}, {"id":"clam", "amount":1}])
	var before: Array = bag.snapshot()
	check("no_slot_for_other_kind", bag.add("snail", 1) == 0)
	check("atomic_reject", bag.add("clam", 99) == 0)
	check("rejection_preserves_state", bag.snapshot() == before)
	check("partial_accept", bag.add("clam", 99, false) == 98)
	check("full_capacity", bag.count_item("clam") == 198 and bag.space_for("clam") == 0)
	check("unknown_rejected", bag.add("unknown", 1) == 0)
	check("invalid_amount_rejected", bag.add("clam", 0) == 0 and bag.add("clam", -1) == 0)
	check("one_signal_per_success", notifications == 3)
	before[0]["amount"] = 0
	check("snapshot_isolated", bag.count_item("clam") == 198)
	var fresh = script.new()
	check("default_24_empty", fresh.snapshot().size() == 24 and fresh.count_item("clam") == 0)
	var chest = script.new(48)
	check("chest_capacity", chest.space_for("clam") == 4752)
	check("containers_isolated", chest.add("kelp", 100) == 100 and fresh.count_item("kelp") == 0)
	var tool_bag = script.new(2, ToolCatalog.new())
	check("tools_accepted", tool_bag.add("tool", 2) == 2)
	check("tools_unstacked", tool_bag.snapshot()[0].amount == 1 and tool_bag.snapshot()[1].amount == 1)
	print("INVENTORY checks=", checks.size(), " passed=", not checks.values().has(false))
	quit(1 if checks.values().has(false) else 0)
