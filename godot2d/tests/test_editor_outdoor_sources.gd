extends SceneTree

var failures := 0
var count := 0
func _initialize() -> void:
	call_deferred("run")
func check(label: String, passed: bool) -> void:
	count += 1
	if not passed: failures += 1
	print(("PASS " if passed else "FAIL ") + label)
func has_property(object: Object, key: String) -> bool:
	for entry in object.get_property_list():
		if entry.name == key: return true
	return false
func run() -> void:
	var world = load("res://scenes/harbor.tscn").instantiate()
	world.set_meta("save_directory", "/private/tmp/coastal-editor-i2/save-" + str(Time.get_ticks_usec()))
	world.set_meta("journal_test", true)
	var exterior = world.get_node("HarborExterior")
	var bounds_present := has_property(exterior, "world_bounds")
	var area_present := has_property(exterior, "foraging_area")
	check("scene_bounds_exported", bounds_present)
	check("scene_foraging_area_exported", area_present)
	if bounds_present: check("default_bounds", exterior.world_bounds == Rect2(0,0,640,416))
	if area_present: check("default_area", exterior.foraging_area == Rect2(224,317,144,51))
	root.add_child(world)
	await process_frame
	world.start_new_game("来源测试")
	world.release_input = false
	world.set_process(false)
	world.player.set_physics_process(false)
	check("default_storage", world.home.storage_point() == Vector2(274,194))
	check("default_pickup", world.nearest_pickup(Vector2(244,330)).get("id", "") == "clam_a")
	check("default_beach_gate", world.nearest_pickup(Vector2(244,310)).is_empty())
	var crates = exterior.get_node("DepthSortedObjects/StorageCrates")
	crates.position = Vector2(350,250)
	world.player.position = crates.position
	world._process(0.0)
	check("moved_storage_point", world.home.storage_point() == crates.position)
	check("moved_storage_prompt", world.hud.prompt.text == "[ E ] 打开旧屋储物箱")
	Input.action_press("inspect")
	world._process(0.0)
	Input.action_release("inspect")
	check("moved_storage_E_opens", world.journal.mode == "storage")
	world.journal.dismiss()
	world.release_input = false
	await process_frame
	world.player.position = Vector2(274,194)
	world.hud.prompt.text = ""
	world._process(0.0)
	check("old_storage_prompt_removed", world.hud.prompt.text != "[ E ] 打开旧屋储物箱")
	var pickup = exterior.get_node("DepthSortedObjects/ForagePickups/clam_a")
	pickup.position = Vector2(340,250)
	if area_present: exterior.foraging_area = Rect2(320,230,50,40)
	check("moved_pickup_query", world.nearest_pickup(Vector2(340,250)).get("id", "") == "clam_a")
	check("old_region_rejected", world.nearest_pickup(Vector2(294,330)).is_empty())
	if bounds_present: exterior.world_bounds = Rect2(280,230,320,160)
	check("new_bounds_reject_old_point", exterior.safe_position(Vector2(300,80)) == exterior.spawn_point())
	check("new_bounds_allow_safe_point", exterior.safe_position(Vector2(340,250)) == Vector2(340,250))
	world.get_node("WorldCamera").update_position()
	check("camera_reads_scene_bounds", world.get_node("WorldCamera").position == Vector2(440,310))
	if DisplayServer.get_name() != "headless":
		await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/private/tmp/coastal-editor-i2/moved.png")
	world.free()
	print("I2 RESULT %d/%d" % [count-failures,count])
	quit(0 if failures == 0 else 1)
