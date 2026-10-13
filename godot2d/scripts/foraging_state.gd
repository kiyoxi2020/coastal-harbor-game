extends RefCounted

signal changed

var counts: Dictionary = {"clam":0, "snail":0, "kelp":0}
var collected: Dictionary = {}

func add_item(kind: String, amount: int) -> bool:
	if not counts.has(kind) or amount <= 0:
		return false
	counts[kind] += amount
	changed.emit()
	return true

func collect(id: String, kind: String) -> bool:
	if id.is_empty() or collected.has(id) or not counts.has(kind):
		return false
	# Mark before notifying observers so reentrant collection cannot duplicate loot.
	collected[id] = true
	add_item(kind, 1)
	return true
