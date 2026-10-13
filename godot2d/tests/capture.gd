extends SceneTree

var scene: Node2D
var output_dir := "res://verification"
var route_results: Array = []

func _initialize() -> void:
	call_deferred("run")

func shot(file_name: String) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	var error := image.save_png(output_dir.path_join(file_name + ".png"))
	assert(error == OK,"Screenshot save failed")

func release() -> void:
	for action in ["left","right","up","down"]:
		Input.action_release(action)

func walk_to(destination: Vector2) -> void:
	var reached := false
	for tick in range(240):
		release()
		var delta: Vector2 = destination - scene.player.position
		if delta.length() < 2:
			reached = true
			break
		if abs(delta.x) > 1.2:
			Input.action_press("right" if delta.x > 0 else "left")
		if abs(delta.y) > 1.2:
			Input.action_press("down" if delta.y > 0 else "up")
		await physics_frame
	release()
	await physics_frame
	route_results.append({"destination":[destination.x,destination.y],"reached":reached})
	print("Route ",destination," reached=",reached)

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):
			output_dir = arg.trim_prefix("--output=")
	DirAccess.make_dir_recursive_absolute(output_dir)
	scene = load("res://scenes/harbor.tscn").instantiate()
	root.add_child(scene)
	for i in range(8):
		await process_frame
	await shot("01-overview")
	await walk_to(Vector2(440,250))
	await walk_to(Vector2(442,236))
	Input.action_press("inspect")
	await process_frame
	Input.action_release("inspect")
	await shot("02-market-interaction")
	scene.hud.dismiss()
	await walk_to(Vector2(440,250))
	await walk_to(Vector2(440,364))
	await shot("03-pier")
	await walk_to(Vector2(440,250))
	await walk_to(Vector2(296,250))
	await walk_to(Vector2(296,302))
	await shot("04-tidal-steps")
	await walk_to(Vector2(296,330))
	await walk_to(Vector2(244,330))
	await shot("09-foraging-before")
	for entry in scene.data.pickups():
		await walk_to(entry.point)
		Input.action_press("inspect")
		for i in range(3):
			await physics_frame
		Input.action_release("inspect")
		for i in range(3):
			await physics_frame
	await shot("10-foraging-complete")
	await walk_to(Vector2(296,330))
	await walk_to(Vector2(296,250))
	await walk_to(Vector2(296,194))
	await walk_to(Vector2(226,194))
	await shot("05-old-house")
	await walk_to(Vector2(296,194))
	await walk_to(Vector2(296,250))
	await walk_to(Vector2(168,250))
	await walk_to(Vector2(168,234))
	await shot("06-garden")
	# These two controlled positions verify occlusion, not navigation.
	scene.player.position = Vector2(568,171)
	await physics_frame
	await shot("07-tree-behind")
	scene.player.position = Vector2(568,198)
	await physics_frame
	await shot("08-tree-front")
	var passed := true
	for result in route_results:
		passed = passed and result.reached
	var report = FileAccess.open(output_dir.path_join("render-route.json"),FileAccess.WRITE)
	report.store_string(JSON.stringify({"passed":passed,"route":route_results,"screenshots":10,"occlusion_positions":"controlled teleport for visual review","renderer":RenderingServer.get_current_rendering_method()},"\t"))
	quit(0 if passed else 1)
