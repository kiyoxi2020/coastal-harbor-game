extends RefCounted

signal changed
const Catalog = preload("res://scripts/inventory/item_catalog.gd")
var _catalog: RefCounted
var _slots: Array = []

func _init(capacity: int = 24, catalog: RefCounted = null) -> void:
	assert(capacity > 0)
	_catalog = Catalog.new() if catalog == null else catalog
	for i in range(capacity):
		_slots.append({"id":"", "amount":0})

func snapshot() -> Array:
	return _slots.duplicate(true)

func count_item(id: String) -> int:
	var result := 0
	for slot in _slots:
		if slot.id == id:
			result += slot.amount
	return result

func space_for(id: String) -> int:
	var limit: int = _catalog.stack_limit(id)
	if limit <= 0:
		return 0
	var result := 0
	for slot in _slots:
		if slot.id == "":
			result += limit
		elif slot.id == id:
			result += limit-int(slot.amount)
	return result

func add(id: String, amount: int, require_all: bool = true) -> int:
	if amount <= 0:
		return 0
	var available := space_for(id)
	if available == 0 or (require_all and available < amount):
		return 0
	var accepted := mini(amount, available)
	_insert(id, accepted)
	changed.emit()
	return accepted

func _insert(id: String, accepted: int) -> void:
	var remaining := accepted
	var limit: int = _catalog.stack_limit(id)
	# Complete the mutation before notifying observers.
	for slot in _slots:
		if slot.id == id:
			var moved := mini(remaining, limit-int(slot.amount))
			slot.amount += moved
			remaining -= moved
	for slot in _slots:
		if remaining == 0:
			break
		if slot.id == "":
			var moved := mini(remaining, limit)
			slot.id = id
			slot.amount = moved
			remaining -= moved

func _valid(index: int) -> bool:
	return index >= 0 and index < _slots.size()

func _remove(index: int, amount: int) -> void:
	_slots[index].amount -= amount
	if _slots[index].amount == 0:
		_slots[index] = {"id":"", "amount":0}

func move_slot(source: int, destination: int) -> bool:
	if not _valid(source) or not _valid(destination) or source == destination or _slots[source].id == "":
		return false
	var from: Dictionary = _slots[source]
	var to: Dictionary = _slots[destination]
	if from.id == to.id:
		var moved := mini(int(from.amount), int(_catalog.stack_limit(from.id))-int(to.amount))
		if moved <= 0:
			return false
		to.amount += moved
		_remove(source, moved)
	else:
		_slots[source] = to
		_slots[destination] = from
	changed.emit()
	return true

func split_stack(source: int, destination: int, amount: int) -> bool:
	if not _valid(source) or not _valid(destination) or source == destination:
		return false
	if amount <= 0 or amount >= int(_slots[source].amount) or _slots[destination].id != "":
		return false
	_slots[destination] = {"id":_slots[source].id, "amount":amount}
	_remove(source, amount)
	changed.emit()
	return true

func _sort_key(id: String) -> String:
	var categories := ["seafood", "ingredients", "materials", "tools"]
	var category: String = _catalog.get_item(id).get("category", "")
	var rank := categories.find(category)
	return "%02d:%s" % [rank if rank >= 0 else categories.size(), id]

func organize() -> bool:
	var totals: Dictionary = {}
	for slot in _slots:
		if slot.id != "":
			totals[slot.id] = int(totals.get(slot.id, 0))+int(slot.amount)
	var ids := totals.keys()
	ids.sort_custom(func(a, b): return _sort_key(a) < _sort_key(b))
	var sorted: Array = []
	for id in ids:
		var remaining: int = totals[id]
		while remaining > 0:
			var amount := mini(remaining, int(_catalog.stack_limit(id)))
			sorted.append({"id":id, "amount":amount})
			remaining -= amount
	while sorted.size() < _slots.size():
		sorted.append({"id":"", "amount":0})
	if sorted == _slots:
		return false
	_slots = sorted
	changed.emit()
	return true

# Confirmation is supplied by the UI only after the explicit confirmation step.
func discard(index: int, amount: int, confirmed: bool = false) -> int:
	if not confirmed or not _valid(index) or amount <= 0 or amount > int(_slots[index].amount):
		return 0
	var item: Dictionary = _catalog.get_item(_slots[index].id)
	if not item.get("discardable", false) or item.get("category", "") in ["tools", "quest"]:
		return 0
	_remove(index, amount)
	changed.emit()
	return amount

func _target_valid(target) -> bool:
	return is_instance_valid(target) and target != self and target.get_script() == get_script()

# Silent transfer lets batch operations notify only after both containers settle.
func _transfer(target, index: int, amount: int) -> int:
	var id: String = _slots[index].id
	var accepted := mini(amount, int(target.space_for(id)))
	if accepted <= 0:
		return 0
	target._insert(id, accepted)
	_remove(index, accepted)
	return accepted

func transfer_to(target, index: int, amount: int) -> int:
	if not _target_valid(target) or not _valid(index) or amount <= 0 or amount > int(_slots[index].amount):
		return 0
	var accepted := _transfer(target, index, amount)
	if accepted > 0:
		changed.emit()
		target.changed.emit()
	return accepted

func deposit_matching(target) -> int:
	if not _target_valid(target):
		return 0
	var kinds: Dictionary = {}
	for slot in target.snapshot():
		if slot.id != "":
			kinds[slot.id] = true
	var total := 0
	for index in range(_slots.size()):
		if kinds.has(_slots[index].id):
			total += _transfer(target, index, int(_slots[index].amount))
	if total > 0:
		changed.emit()
		target.changed.emit()
	return total
