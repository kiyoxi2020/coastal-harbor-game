extends RefCounted
const CROPS := {
	"lettuce":{"seed_id":"lettuce_seed", "growth_days":2, "yield_item_id":"lettuce", "yield_amount":3},
	"tomato":{"seed_id":"tomato_seed", "growth_days":4, "yield_item_id":"tomato", "yield_amount":3}
}

static func get_crop(id: String) -> Dictionary:
	return CROPS.get(id, {}).duplicate(true)
