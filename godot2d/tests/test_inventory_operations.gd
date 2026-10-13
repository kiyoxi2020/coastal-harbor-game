extends SceneTree

const Bag = preload("res://scripts/inventory/inventory_container.gd")
class ProtectedCatalog:
	extends RefCounted
	func stack_limit(id: String) -> int:
		return 1 if id == "tool" else 0
	func get_item(_id: String) -> Dictionary:
		return {"category":"tools", "discardable":false}

var checks: Dictionary = {}
var observed: Array = []
func check(label: String, passed: bool) -> void:
	checks[label] = passed
	print(("PASS " if passed else "FAIL ")+label)

func _initialize() -> void:
	var b = Bag.new(4)
	for method in ["move_slot", "split_stack", "organize", "discard", "transfer_to", "deposit_matching"]:
		check("api_"+method, b.has_method(method))
	if checks.values().has(false):
		quit(1)
		return
	b.add("clam", 100)
	check("move_empty", b.move_slot(1, 3) and b.snapshot()[1].id == "")
	check("split", b.split_stack(0, 1, 40) and b.snapshot()[0].amount == 59)
	check("split_occupied_rejected", not b.split_stack(0, 1, 2))
	check("split_whole_rejected", not b.split_stack(0, 2, 59))
	check("split_zero_rejected", not b.split_stack(0, 2, 0))
	check("merge", b.move_slot(1, 0) and b.snapshot()[0].amount == 99)
	b.add("snail", 2)
	check("swap", b.move_slot(0, 1) and b.snapshot()[0].id == "snail")
	var before: Array = b.snapshot()
	check("invalid_indices", not b.move_slot(-1, 0) and not b.move_slot(0, 4))
	check("same_slot", not b.move_slot(0, 0))
	check("invalid_unchanged", before == b.snapshot())
	check("organize", b.organize())
	check("sort_and_conserve", b.snapshot()[0] == {"id":"clam", "amount":99} and b.count_item("clam") == 100 and b.count_item("snail") == 2)
	check("organize_noop", not b.organize())
	check("discard_requires_confirmation", b.discard(0, 2) == 0)
	check("discard_confirmed", b.discard(0, 2, true) == 2 and b.count_item("clam") == 98)
	check("over_discard_rejected", b.discard(0, 100, true) == 0)
	var protected_bag = Bag.new(1, ProtectedCatalog.new())
	protected_bag.add("tool", 1)
	check("protected", protected_bag.discard(0, 1, true) == 0)
	var source = Bag.new(3)
	var target = Bag.new(1)
	source.add("clam", 20)
	target.add("clam", 95)
	target.changed.connect(func(): observed.append(source.count_item("clam")+target.count_item("clam")))
	check("partial_transfer", source.transfer_to(target, 0, 10) == 4)
	check("transfer_conserved", source.count_item("clam") == 16 and target.count_item("clam") == 99)
	check("observer_sees_consistent_total", observed == [115])
	check("full_transfer_rejected", source.transfer_to(target, 0, 1) == 0)
	check("self_transfer_rejected", source.transfer_to(source, 0, 1) == 0)
	check("invalid_transfer", source.transfer_to(target, 0, 17) == 0 and source.transfer_to(target, -1, 1) == 0)
	check("transfer_back", target.transfer_to(source, 0, 5) == 5 and source.count_item("clam") == 21)
	var chest = Bag.new(3)
	chest.add("clam", 1)
	source.add("kelp", 5)
	check("deposit_matching", source.deposit_matching(chest) == 21)
	check("only_existing_kinds", source.count_item("kelp") == 5 and chest.count_item("kelp") == 0 and chest.count_item("clam") == 22)
	check("empty_source_clean", source.snapshot()[0] == {"id":"", "amount":0})
	check("self_deposit", source.deposit_matching(source) == 0)
	var split_bag = Bag.new(3)
	split_bag.add("clam", 150)
	split_bag.split_stack(0, 2, 30)
	check("merge_remainder", split_bag.move_slot(1, 0) and split_bag.snapshot()[1].amount == 21 and split_bag.count_item("clam") == 150)
	check("full_merge_noop", not split_bag.move_slot(2, 0))
	var empty = Bag.new(2)
	check("empty_ops", not empty.move_slot(0, 1) and not empty.organize() and empty.discard(0, 1, true) == 0)
	check("null_target", source.transfer_to(null, 0, 1) == 0 and source.deposit_matching(null) == 0)
	# Fixed-seed mixed operations check conservation and slot invariants together.
	var left = Bag.new(6)
	var right = Bag.new(6)
	left.add("clam", 180)
	left.add("snail", 90)
	right.add("kelp", 140)
	var rng := RandomNumberGenerator.new()
	rng.seed = 20261013
	var conserved := true
	var valid_slots := true
	for iteration in range(1000):
		var a = left if rng.randi_range(0, 1) == 0 else right
		var z = right if a == left else left
		var i := rng.randi_range(0, 5)
		var j := rng.randi_range(0, 5)
		var n := rng.randi_range(1, 99)
		match rng.randi_range(0, 4):
			0: a.move_slot(i, j)
			1: a.split_stack(i, j, n)
			2: a.organize()
			3: a.transfer_to(z, i, n)
			4: a.deposit_matching(z)
		conserved = conserved and left.count_item("clam")+right.count_item("clam") == 180
		conserved = conserved and left.count_item("snail")+right.count_item("snail") == 90
		conserved = conserved and left.count_item("kelp")+right.count_item("kelp") == 140
		for slot in left.snapshot()+right.snapshot():
			valid_slots = valid_slots and ((slot.id == "" and slot.amount == 0) or (slot.id in ["clam", "snail", "kelp"] and slot.amount > 0 and slot.amount <= 99))
	check("1000_operations_conserve_each_kind", conserved)
	check("1000_operations_valid_slots", valid_slots)
	print("OPERATIONS checks=", checks.size(), " passed=", not checks.values().has(false))
	quit(1 if checks.values().has(false) else 0)
