extends SceneTree

var failures: Array[String] = []

func check(label: String, ok: bool) -> void:
	print(("PASS " if ok else "FAIL ") + label)
	if not ok: failures.append(label)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var path := "res://scenes/world/harbor_district.tscn"
	check("district_scene_exists", ResourceLoader.exists(path))
	if not ResourceLoader.exists(path):
		quit(1)
		return
	var scene = load(path).instantiate()
	root.add_child(scene)
	await physics_frame
	check("bounds_640_416", scene.world_bounds == Rect2(0,0,640,416))
	check("depth_layer", scene.get_node("DepthSortedObjects").y_sort_enabled)
	check("safe_spawn", scene.spawn_point() == Vector2(320,350) and scene.safe_position(scene.spawn_point()) == scene.spawn_point())
	check("no_storage", scene.storage_point() == Vector2.INF)
	check("bad_positions_recover", scene.safe_position(Vector2(-8,80)) == scene.spawn_point() and scene.safe_position(Vector2(NAN,30)) == scene.spawn_point())
	check("restaurant_marker", scene.get_node("InteractPoints/restaurant").position == Vector2(180,190))
	check("restaurant_blocked", scene.safe_position(Vector2(180,150)) == scene.spawn_point())
	check("workshop_blocked", scene.safe_position(Vector2(460,150)) == scene.spawn_point())
	check("closed_future_exits", scene.safe_position(Vector2(320,30)) == scene.spawn_point() and scene.safe_position(Vector2(30,240)) == scene.spawn_point() and scene.safe_position(Vector2(600,240)) == scene.spawn_point())
	check("south_exit_open", scene.safe_position(Vector2(320,380)) == Vector2(320,380))
	for y in range(190,391,10):
		check("main_lane_%d" % y, scene.safe_position(Vector2(320,y)) == Vector2(320,y))
	var restaurant_found := false
	for item in scene.locations():
		if item.id == "restaurant":
			restaurant_found = item.title != "" and item.body.contains("暂未营业")
	check("restaurant_information_only", restaurant_found)
	# Scale acceptance is relative to the actual existing cottage (168px wide).
	var house = load("res://scenes/world/house_exterior_art.tscn").instantiate()
	var cottage_top: Sprite2D = house.get_node("AtlasParts/Top")
	var cottage_width: float = cottage_top.texture.get_width() * cottage_top.scale.x * house.scale.x
	check("cottage_measurement_168", is_equal_approx(cottage_width, 168.0))
	for pair in [["Restaurant", 0.65, 0.75], ["Workshop", 0.60, 0.70]]:
		var building: Node2D = scene.get_node("DepthSortedObjects/" + pair[0])
		var art: Sprite2D = building.get_node("Sprite")
		var art_width: float = art.texture.get_width() * art.scale.x * building.scale.x
		var ratio: float = art_width / cottage_width
		check("scale_ratio_" + pair[0], ratio >= pair[1] and ratio <= pair[2])
		var base_y: float = art.position.y + art.texture.get_height() * art.scale.y / 2.0
		check("bottom_pivot_" + pair[0], is_zero_approx(base_y))
		var collider: CollisionShape2D = scene.get_node("Boundaries/" + pair[0])
		var footprint: Rect2 = Rect2(collider.position - collider.shape.size / 2.0, collider.shape.size)
		check("footprint_width_" + pair[0], footprint.size.x <= art_width and footprint.size.x >= art_width * 0.8)
		check("footprint_bottom_" + pair[0], is_equal_approx(footprint.end.y, building.position.y))
		var marker: Vector2 = scene.get_node("InteractPoints/" + pair[0].to_lower()).position
		check("service_position_" + pair[0], scene.safe_position(marker) == marker)
		# The label sits above the whole building, away from the service approach.
		var sign: Label = scene.get_node("Signs/" + pair[0])
		check("sign_clear_" + pair[0], sign.position.y + sign.size.y <= building.position.y - art.texture.get_height() * art.scale.y)
	var flowers: Array[Sprite2D] = []
	var flower_textures: Dictionary = {}
	for child in scene.get_node("DepthSortedObjects").get_children():
		if child is Sprite2D and String(child.name).begins_with("Flowers"):
			flowers.append(child)
			flower_textures[child.texture.resource_path] = true
	check("flowers_sparse_count", flowers.size() >= 3 and flowers.size() <= 4)
	check("flowers_varied", flower_textures.size() >= 2)
	for flower in flowers:
		var r: Rect2 = flower.transform * flower.get_rect()
		check("flower_low_" + flower.name, r.size.y <= 22)
		var on_road := false
		for road_name in ["Plaza", "NorthLane", "WestLane", "EastLane", "SouthLane"]:
			var road: Sprite2D = scene.get_node("Terrain/" + road_name)
			on_road = on_road or r.intersects(road.transform * road.get_rect())
		check("flower_off_paving_" + flower.name, not on_road)
		check("flower_off_queue_" + flower.name, not r.intersects(Rect2(118,178,124,42)))
	for tree_name in ["TreeWest", "TreeNorth", "TreeEast"]:
		var tree: Sprite2D = scene.get_node("DepthSortedObjects/" + tree_name)
		var tree_bounds: Rect2 = tree.transform * tree.get_rect()
		var overlaps := tree_bounds.intersects(Rect2(304,190,32,200))
		for building_name in ["Restaurant", "Workshop"]:
			var building: Node2D = scene.get_node("DepthSortedObjects/" + building_name)
			var art: Sprite2D = building.get_node("Sprite")
			var bounds: Rect2 = building.transform * art.transform * art.get_rect()
			overlaps = overlaps or tree_bounds.intersects(bounds)
		check("tree_clear_" + tree_name, not overlaps)
	check("paired_south_exit_preserved", scene.get_node("Exits/ToHarbor").position == Vector2(320,380))
	house.free()
	print("DISTRICT RESULT checks added for measured scale / flowers; failures=", failures.size())
	scene.queue_free()
	quit(0 if failures.is_empty() else 1)
