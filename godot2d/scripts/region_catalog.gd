extends RefCounted
# Stable IDs shared by scene exits and the overview. Return copies to callers.
static func open_regions()->Array[String]:return ["harbor","harbor_district"]
static func regions()->Array[Dictionary]:
	return [
		{"id":"harbor","name":"旧屋海港","open":true,"map":Vector2(215,360),"description":"旧屋、菜地与鱼摊相邻，沿海小路通往潮汐台阶和码头。","route":"北侧出口 → 港口街区"},
		{"id":"harbor_district","name":"港口街区","open":true,"map":Vector2(330,220),"description":"石板主巷连接小食铺与海堤。小食铺待复业，加工铺仅作预留。","route":"南侧出口 → 旧屋海港"},
		{"id":"residential_lane","name":"住宅坡巷","open":false,"map":Vector2(390,85),"description":"沿坡向上的邻里住宅区，未来将从港口街区北侧连接。","route":"规划连接：街区北侧 · 暂不可通行"},
		{"id":"hillside","name":"山坡林地","open":false,"map":Vector2(130,130),"description":"海湾西北的树木与自然步道。区域与资源内容仍待规划。","route":"规划连接：街区西侧 · 暂不可通行"},
		{"id":"cape_coast","name":"岬角海岸","open":false,"map":Vector2(535,295),"description":"海湾东侧的岬角与潮池，尚未开放探索。","route":"规划连接：街区沿海道路 · 暂不可通行"}]
static func region(id:String)->Dictionary:
	for entry in regions():
		if entry.id==id:return entry
	return {}
static func exit_for(region:String,world:Node=null)->Dictionary:
	if world!=null:
		var result:=exit_for(region)
		if result.is_empty():return result
		var source:Node2D=world.exterior if region=="harbor" else world.get_node("HarborDistrict")
		var target:Node2D=world.get_node("HarborDistrict") if region=="harbor" else world.exterior
		result.point=source.to_local(world.get_node("HarborExterior/Exits/ToDistrict" if region=="harbor" else "HarborDistrict/Exits/ToHarbor").global_position)
		result.spawn=target.to_local(world.get_node("HarborDistrict/Spawn" if region=="harbor" else "HarborExterior/Exits/DistrictArrival").global_position)
		return result
	if region=="harbor":return {"id":"harbor_north","point":Vector2(320,64),"target":"harbor_district","spawn":Vector2(320,350),"name":"前往港口街区"}
	if region=="harbor_district":return {"id":"district_south","point":Vector2(320,380),"target":"harbor","spawn":Vector2(320,94),"name":"返回旧屋海港"}
	return {}
# Detail coordinates are local to the preview, independent of the town schematic.
const DETAIL_SCALE:=0.6
const OVERVIEW_SCALE:=DETAIL_SCALE
static func frame_origin(_region:String)->Vector2:return Vector2.ZERO
static func project(region:String,point:Vector2,world:Node=null)->Vector2:
	var base:=Vector2.ZERO
	if world!=null:
		var scene:Node2D=world.exterior if region in ["harbor","house"] else world.get_node("HarborDistrict")
		base=scene.world_bounds.position
	return (point-base)*DETAIL_SCALE
static func points(world:Node=null)->Array[Dictionary]:
	var result:Array[Dictionary]=[
		{"id":"house","region":"harbor","point":Vector2(209,165),"name":"旧屋 · 床 / 厨房 / 储物","kind":"building"},
		{"id":"garden_a","region":"harbor","point":Vector2(84,224),"name":"菜地A · 8格","kind":"farm"},
		{"id":"garden_b","region":"harbor","point":Vector2(164,224),"name":"菜地B · 8格","kind":"farm"},
		{"id":"market","region":"harbor","point":Vector2(442,218),"name":"鱼摊 · 买种 / 售货","kind":"building"},
		{"id":"pier","region":"harbor","point":Vector2(440,364),"name":"码头","kind":"building"},
		{"id":"restaurant","region":"harbor_district","point":Vector2(180,170),"name":"港口小食铺 · 待复业","kind":"building"},
		{"id":"workshop","region":"harbor_district","point":Vector2(455,170),"name":"加工铺 · 预留","kind":"reserved"}]
	for pickup in preload("res://scripts/harbor_data.gd").pickups():
		result.append({"id":pickup.id,"region":"harbor","point":pickup.point,"name":preload("res://scripts/harbor_data.gd").ITEM_NAMES[pickup.kind],"kind":"resource"})
	for region in open_regions():
		var e:=exit_for(region)
		result.append({"id":e.id,"region":region,"point":e.point,"name":e.name,"kind":"exit"})
	if world!=null:
		var sources={"house":"HarborExterior/InteractPoints/house","garden_a":"HarborExterior/DepthSortedObjects/GardenA","garden_b":"HarborExterior/DepthSortedObjects/GardenB","market":"HarborExterior/InteractPoints/market","pier":"HarborExterior/InteractPoints/pier","restaurant":"HarborDistrict/InteractPoints/restaurant","workshop":"HarborDistrict/InteractPoints/workshop","harbor_north":"HarborExterior/Exits/ToDistrict","district_south":"HarborDistrict/Exits/ToHarbor"}
		for mark in result:
			var source:Node2D=world.get_node("HarborExterior/DepthSortedObjects/ForagePickups/"+mark.id) if mark.kind=="resource" else world.get_node(sources[mark.id])
			var scene:Node2D=world.exterior if mark.region=="harbor" else world.get_node("HarborDistrict")
			mark.point=scene.to_local(source.global_position)
	return result
