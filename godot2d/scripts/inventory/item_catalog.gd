extends RefCounted

const ITEMS := {
	"clam": {"name":"蛤蜊", "icon_key":"clam", "category":"seafood", "description":"赶海拾得的蛤蜊。", "max_stack":99, "discardable":true, "use_action":""},
	"snail": {"name":"海螺", "icon_key":"snail", "category":"seafood", "description":"赶海拾得的海螺。", "max_stack":99, "discardable":true, "use_action":""},
	"kelp": {"name":"海带", "icon_key":"kelp", "category":"seafood", "description":"赶海拾得的海带。", "max_stack":99, "discardable":true, "use_action":""}
}

func get_item(id: String) -> Dictionary:
	return ITEMS.get(id, {}).duplicate(true)

func stack_limit(id: String) -> int:
	return int(ITEMS.get(id, {}).get("max_stack", 0))
