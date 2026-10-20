extends RefCounted
const Recipes=preload("res://scripts/simulation/recipe_catalog.gd")
const Schema=preload("res://scripts/simulation/state_schema.gd")
const Inventory=preload("res://scripts/inventory/inventory_container.gd")
static func failure(code: String) -> Dictionary:
	return {"ok":false,"code":code,"state":{},"events":[]}
static func craft(data: Dictionary, recipe_id: String, batches: int) -> Dictionary:
	if not Schema.validate_current(data):return failure("invalid_state")
	if batches<1 or batches>20:return failure("invalid_amount")
	var recipe:=Recipes.get_recipe(recipe_id)
	if recipe.is_empty():return failure("unknown_recipe")
	var bag=Inventory.new(24)
	if not bag.restore_slots(data.bag):return failure("invalid_state")
	var inputs:Dictionary={}
	var outputs:Dictionary={}
	for id in recipe.inputs:
		inputs[id]=int(recipe.inputs[id])*batches
		if bag.count_item(id)<inputs[id]:return failure("insufficient_stock")
	for id in inputs:
		if not bag.remove_item(id,inputs[id]):return failure("invalid_state")
	for id in recipe.outputs:
		outputs[id]=int(recipe.outputs[id])*batches
		if bag.add(id,outputs[id])!=outputs[id]:return failure("inventory_full")
	var candidate:=data.duplicate(true)
	candidate.bag=bag.snapshot()
	return {"ok":true,"code":"ok","state":candidate,"events":[{"day_id":int(data.life.day_id),"kind":"craft","source":"player","target":"player","items":outputs.duplicate(true),"inputs":inputs,"outputs":outputs,"cash":0,"reason":recipe_id}]}
