extends "res://tests/test_life_farming_native.gd"
func run() -> void:
	evidence="/private/tmp/coastal-flowers-v7"
	DirAccess.make_dir_recursive_absolute(evidence)
	w=load("res://scenes/harbor.tscn").instantiate()
	w.set_meta("save_directory","/private/tmp/coastal-flowers-v7-save")
	root.add_child(w)
	check("isolated",w.save_service.directory=="/private/tmp/coastal-flowers-v7-save")
	check("native_renderer",DisplayServer.get_name()!="headless")
	if w.save_service.directory!="/private/tmp/coastal-flowers-v7-save":finish();return
	check("new_game",w.start_new_game("花丛对比"))
	if not await walk_to(Vector2(270,244),"viewpoint"):finish();return
	w.hud.get_node("Root/Toast").hide()
	var flowers:Dictionary={}
	for node in w.sort_layer.get_children():
		if node is Sprite2D and node.texture!=null and node.texture.resource_path.get_file() in ["flowers_white.png","flowers_yellow.png","flowers_pink.png","flower_edge.png"]:
			flowers[node]=node.texture.resource_path.get_file()
	check("all_flower_instances",flowers.size()==7)
	for node in flowers:
		check("production_48_"+node.name,node.texture.resource_path.begins_with("res://assets/flowers-v7/48/"))
	await capture("flowers-production")
	for width in [32,48]:
		for node in flowers:
			node.texture=load("res://assets/flowers-v7/%d/"%width+flowers[node])
			node.scale=Vector2.ONE*(16.0/width)
			node.offset=Vector2(0,-node.texture.get_height()/2.0)
			check("same_footprint_%d_"%width+node.name,node.texture.get_size()*node.scale==Vector2(16,14))
		await capture("flowers-%d"%width)
	finish()
