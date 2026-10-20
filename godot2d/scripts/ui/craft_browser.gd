extends RefCounted
const Rules=preload("res://scripts/simulation/life_rules.gd")
const Catalog=preload("res://scripts/inventory/item_catalog.gd")
static func max_batches(data:Dictionary,recipe_id:String) -> int:
	# Capacity can increase when all of an ingredient stack is consumed.
	for batches in range(20,0,-1):
		if Rules.plan(data,"craft",{"recipe_id":recipe_id,"batches":batches},int(data.life.action_seq)+1).ok:return batches
	return 0
static func filtered_ids(data:Dictionary,definitions:Dictionary,category:String,query:String,only_available:bool) -> Array[String]:
	var result:Array[String]=[]
	var needle:=query.strip_edges().to_lower()
	for id in definitions:
		var definition:Dictionary=definitions[id]
		if definition.category!=category:continue
		var searchable:String=definition.name
		for item in definition.inputs:searchable+=" "+str(Catalog.ITEMS.get(item,{}).get("name",item))
		if needle!="" and not searchable.to_lower().contains(needle):continue
		if only_available and max_batches(data,id)==0:continue
		result.append(id)
	return result
