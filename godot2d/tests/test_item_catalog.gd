extends SceneTree

func _initialize() -> void:
	var script = load("res://scripts/inventory/item_catalog.gd")
	if script == null:
		push_error("Missing item catalog")
		quit(1)
		return
	var catalog = script.new()
	var checks := [
		catalog.stack_limit("clam") == 99,
		catalog.stack_limit("snail") == 99,
		catalog.stack_limit("kelp") == 99,
		catalog.stack_limit("unknown") == 0,
		catalog.get_item("unknown").is_empty()
	]
	var item: Dictionary = catalog.get_item("clam")
	checks.append(item.name == "蛤蜊" and item.category == "seafood")
	checks.append(item.discardable and item.use_action == "")
	item["max_stack"] = 1
	checks.append(catalog.stack_limit("clam") == 99)
	var expected_icons := {"lettuce_seed":"生种", "tomato_seed":"番种", "lettuce":"生菜", "tomato":"番茄"}
	for id in expected_icons:
		item = catalog.get_item(id)
		checks.append(catalog.stack_limit(id) == 99 and item.icon_key == expected_icons[id] and not item.name.is_empty())
	print("CATALOG checks=", checks.size(), " passed=", not checks.has(false))
	quit(1 if checks.has(false) else 0)
