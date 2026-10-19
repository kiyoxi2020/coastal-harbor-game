extends RefCounted

const ITEMS := {
	"clam": {"name":"蛤蜊", "icon_key":"clam", "category":"seafood", "description":"赶海拾得的蛤蜊。", "max_stack":99, "discardable":true, "use_action":""},
	"snail": {"name":"海螺", "icon_key":"snail", "category":"seafood", "description":"赶海拾得的海螺。", "max_stack":99, "discardable":true, "use_action":""},
	"kelp": {"name":"海带", "icon_key":"kelp", "category":"seafood", "description":"赶海拾得的海带。", "max_stack":99, "discardable":true, "use_action":""},
	"lettuce_seed": {"name":"生菜种子", "icon_key":"生种", "category":"ingredients", "description":"可种出生菜的种子。", "max_stack":99, "discardable":true, "use_action":""},
	"tomato_seed": {"name":"番茄种子", "icon_key":"番种", "category":"ingredients", "description":"可种出番茄的种子。", "max_stack":99, "discardable":true, "use_action":""},
	"lettuce": {"name":"生菜", "icon_key":"生菜", "category":"ingredients", "description":"清脆的新鲜生菜。", "max_stack":99, "discardable":true, "use_action":""},
	"tomato": {"name":"番茄", "icon_key":"番茄", "category":"ingredients", "description":"成熟的新鲜番茄。", "max_stack":99, "discardable":true, "use_action":""}
}

func get_item(id: String) -> Dictionary:
	return ITEMS.get(id, {}).duplicate(true)

func stack_limit(id: String) -> int:
	return int(ITEMS.get(id, {}).get("max_stack", 0))
