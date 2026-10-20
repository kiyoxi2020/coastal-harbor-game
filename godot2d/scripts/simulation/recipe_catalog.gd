extends RefCounted
const RECIPES := {
	"clam_salad":{"category":"cooking","name":"蛤蜊蔬菜盘","inputs":{"clam":1,"lettuce":1},"outputs":{"clam_salad":1}},
	"snail_stew":{"category":"cooking","name":"海螺番茄煮","inputs":{"snail":1,"tomato":1},"outputs":{"snail_stew":1}},
	"marine_fertilizer":{"category":"processing","name":"处理海藻肥","inputs":{"kelp":2},"outputs":{"marine_fertilizer":1}}
}
static func get_recipe(id: String) -> Dictionary:
	return RECIPES.get(id,{}).duplicate(true)
static func all_ids() -> Array[String]:
	var ids:Array[String]=[]
	ids.assign(RECIPES.keys())
	return ids

static func all() -> Dictionary:
	return RECIPES.duplicate(true)
