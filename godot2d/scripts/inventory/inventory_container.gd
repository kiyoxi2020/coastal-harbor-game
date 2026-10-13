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
	changed.emit()
	return accepted
