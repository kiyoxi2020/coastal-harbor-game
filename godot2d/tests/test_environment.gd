extends SceneTree

var checks: Dictionary = {}

func check(label: String, passed: bool) -> void:
	checks[label] = passed
	print(("PASS " if passed else "FAIL ") + label)

func _initialize() -> void:
	call_deferred("run")

func finish() -> void:
	var passed := not checks.values().has(false)
	DirAccess.make_dir_recursive_absolute("res://verification-v2")
	var out := FileAccess.open("res://verification-v2/environment-tests.json", FileAccess.WRITE)
	out.store_string(JSON.stringify({"passed":passed,"checks":checks}, "\t"))
	print("ENVIRONMENT RESULT ",checks.size()," passed=",passed)
	quit(0 if passed else 1)

func run() -> void:
	var ready := true
	for name in ["grass","shallow","deep","stone","tree-0","tree-1","tree-2","tree-3"]:
		var folder := "tree-set-v4" if name.begins_with("tree-") else "environment-v2"
		var path: String = "res://assets/" + folder + "/" + name + ".png"
		var found := FileAccess.file_exists(path)
		check("asset_" + name,found)
		ready = ready and found
	if not ready:
		finish()
		return
	for name in ["grass","shallow","deep","stone"]:
		var material: Image = load("res://assets/environment-v2/" + name + ".png").get_image()
		check("grid_64_" + name,material.get_size() == Vector2i(64,64))
		if name != "stone":
			var delta := 0.0
			for i in range(64):
				var a := material.get_pixel(0,i)
				var b := material.get_pixel(63,i)
				var c := material.get_pixel(i,0)
				var d := material.get_pixel(i,63)
				delta = maxf(delta,absf(a.r-b.r)+absf(a.g-b.g)+absf(a.b-b.b))
				delta = maxf(delta,absf(c.r-d.r)+absf(c.g-d.g)+absf(c.b-d.b))
			check("seam_" + name,delta < 0.025)
	var signatures: Array = []
	for i in range(4):
		var tree: Image = load("res://assets/tree-set-v4/tree-%d.png" % i).get_image()
		check("tree_grid_%d" % i,tree.get_size() == Vector2i(96,96))
		check("tree_alpha_%d" % i,tree.detect_alpha() != Image.ALPHA_NONE)
		var binary_alpha := true
		for y in range(96):
			for x in range(96):
				var alpha := tree.get_pixel(x,y).a
				binary_alpha = binary_alpha and (alpha == 0.0 or alpha == 1.0)
		check("tree_crisp_alpha_%d" % i,binary_alpha)
		check("tree_nonempty_%d" % i,not tree.is_invisible())
		var used := tree.get_used_rect()
		check("tree_padding_%d" % i,used.position.x >= 1 and used.end.x <= 95 and used.position.y >= 1 and used.end.y <= 95)
		signatures.append(hash(tree.get_data()))
	check("four_unique_sprites",signatures.size() == 4 and signatures[0] != signatures[1] and signatures[1] != signatures[2] and signatures[2] != signatures[3] and signatures[0] != signatures[2] and signatures[0] != signatures[3] and signatures[1] != signatures[3])
	var scene = load("res://scenes/harbor.tscn").instantiate()
	scene.set_meta("save_directory", "/private/tmp/coastal-environment-" + str(Time.get_ticks_usec()))
	root.add_child(scene)
	await process_frame
	var trees: Array = []
	var variants: Dictionary = {}
	for child in scene.sort_layer.get_children():
		if child.has_meta("tree_variant"):
			trees.append(child)
			variants[child.get_meta("tree_variant")] = true
	check("five_trees",trees.size() == 5)
	check("four_tree_variants_in_scene",variants.size() == 4)
	for i in range(trees.size()):
		check("root_position_%d" % i,trees[i].position == scene.data.TREES[i])
		check("integer_tree_scale_%d" % i,trees[i].get_child(0).scale == Vector2.ONE)
		check("tree_sorted_%d" % i,trees[i].get_parent() == scene.sort_layer)
	var terrain: Node = scene.get_node_or_null("HarborExterior/Terrain")
	check("named_terrain",terrain != null)
	var water: Node = scene.get_node_or_null("HarborExterior/Terrain/WaterDetail")
	check("water_layer",water != null)
	if water != null:
		check("frame_four_steps",water.frame_at(0.0,0) == 0 and water.frame_at(0.25,0) == 1 and water.frame_at(0.5,0) == 2 and water.frame_at(0.75,0) == 3)
		check("frame_wrap",water.frame_at(1.0,0) == 0)
		check("frame_phase",water.frame_at(0.0,1) == 1)
		check("water_visible",water.is_open_water(Vector2(30,320)))
		check("no_foam_on_land",not water.is_open_water(Vector2(30,240)))
		check("no_foam_on_pier",not water.is_open_water(Vector2(440,340)))
		check("no_foam_on_steps",not water.is_open_water(Vector2(296,302)))
		check("sand_below_steps",not water.is_open_water(Vector2(296,325)))
		check("water_beyond_beach",water.is_open_water(Vector2(296,375)))
		check("no_foam_outside_canvas",not water.is_open_water(Vector2(640,340)) and not water.is_open_water(Vector2(-1,340)))
	var before: Array = scene.data.blockers()
	# The house rectangle is now split in three around a separately colliding door.
	check("beach_blocker_count",before.size() == 22)
	check("unchanged_spawn",scene.data.SPAWN == Vector2(330,250))
	finish()
