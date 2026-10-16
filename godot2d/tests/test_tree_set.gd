extends SceneTree
var checks: Dictionary = {}
func check(label: String, passed: bool) -> void:
	checks[label] = passed
	print(("PASS " if passed else "FAIL ")+label)
func _initialize() -> void:
	call_deferred("run")
func run() -> void:
	var signatures: Dictionary = {}
	for i in range(4):
		var path := "res://assets/tree-set-v4/tree-%d.png" % i
		check("exists_%d"%i,FileAccess.file_exists(path))
		if not FileAccess.file_exists(path):
			continue
		var pic: Image = load(path).get_image()
		check("canvas_%d"%i,pic.get_size()==Vector2i(96,96))
		var colors: Dictionary = {}
		var hard := true
		for y in range(96):
			for x in range(96):
				var c := pic.get_pixel(x,y)
				hard = hard and (c.a==0 or c.a==1)
				if c.a==1:
					colors[c.to_html()] = true
		check("hard_alpha_%d"%i,hard)
		check("palette_%d"%i,colors.size()>=5 and colors.size()<=(14 if i==3 else 11))
		var bounds := pic.get_used_rect()
		var limits := [Vector2i(64,84),Vector2i(62,82),Vector2i(72,78),Vector2i(60,72)]
		check("size_%d"%i,bounds.size.x<=limits[i].x and bounds.size.y<=limits[i].y)
		check("padding_%d"%i,bounds.position.x>=1 and bounds.end.x<=95 and bounds.position.y>=1 and bounds.end.y==94)
		check("anchor_%d"%i,pic.get_pixel(48,92).a==1)
		signatures[hash(pic.get_data())] = true
	check("four_distinct_assets",signatures.size()==4)
	var scene = load("res://scenes/harbor.tscn").instantiate()
	scene.set_meta("save_directory", "/private/tmp/coastal-tree-set-" + str(Time.get_ticks_usec()))
	root.add_child(scene)
	await process_frame
	var variants := [0,1,0,2,3]
	for i in range(5):
		var node = scene.sort_layer.get_node("CoastalTree%d"%i)
		var sprite: Sprite2D = node.get_child(0)
		check("reference_%d"%i,sprite.texture.resource_path=="res://assets/tree-set-v4/tree-%d.png"%variants[i])
		check("root_%d"%i,node.position==scene.data.TREES[i])
		check("native_%d"%i,sprite.scale==Vector2.ONE and sprite.position==Vector2(0,-46))
	check("y_sort",scene.sort_layer.y_sort_enabled)
	# Tree blockers stay present even though the beach adds two water segments.
	for at in scene.data.TREES:
		check("tree_collision_"+str(at),scene.data.blockers().has(Rect2(at-Vector2(5,5),Vector2(10,8))))
	check("spawn",scene.data.SPAWN==Vector2(330,250))
	DirAccess.make_dir_recursive_absolute("res://verification-tree-v4")
	var f := FileAccess.open("res://verification-tree-v4/tests.json",FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":not checks.values().has(false),"checks":checks},"\t"))
	print("TREE SET RESULT ",checks.size()," passed=",not checks.values().has(false))
	quit(1 if checks.values().has(false) else 0)
