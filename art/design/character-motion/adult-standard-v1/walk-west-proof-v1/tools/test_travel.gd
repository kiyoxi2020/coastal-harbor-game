extends SceneTree

func fail(message: String) -> void:
	printerr("FAIL travel: ", message)
	quit(1)

func _initialize() -> void:
	if not FileAccess.file_exists("res://travel_clock.gd") or not FileAccess.file_exists("res://travel_review.tscn"):
		fail("moving review must exist independently of stationary review")
		return
	call_deferred("exercise")

func exercise() -> void:
	var clock = load("res://travel_clock.gd").new()
	clock.configure([80, 80, 80, 80])
	if clock.frame_at(160.0) != 2 or clock.frame_at(319.9) != 3 or clock.frame_at(320.0) != 0:
		fail("80ms timeline")
		return
	if not is_equal_approx(clock.root_x_at(1000.0), 812.0):
		fail("production 72 world/s at camera4 must move exactly 288 screen pixels per second")
		return
	if clock.loops_per_pass != 10 or not is_equal_approx(clock.root_x_at(3199.0), 178.688) or not is_equal_approx(clock.root_x_at(3200.0), 1100.0):
		fail("reset only at whole loop boundary")
		return
	var resets: Array = clock.resets_between(3190.0, 3210.0)
	if resets.size() != 1 or resets[0]["at_elapsed_ms"] != 3200.0 or resets[0]["loop"] != 10:
		fail("explicit reset log")
		return
	clock.configure([140, 180, 140, 180])
	if not is_equal_approx(clock.root_x_at(1000.0), 812.0) or clock.loops_per_pass != 5 or clock.frame_at(140.0) != 1:
		fail("duration affects pose and reset boundary, not travel speed")
		return
	clock.configure([1000, 1000, 1000, 1000])
	if clock.root_x_at(3900.0) >= 0 or clock.root_x_at(4000.0) != 1100.0:
		fail("long cycle must not teleport before a complete loop even when offscreen")
		return
	var scene = load("res://travel_review.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	if not scene.loaded:
		fail("fixture manifest load")
		return
	scene.auto_capture = false
	scene.apply_time(1000.0)
	if scene.get_node("A").position.x != 812.0 or scene.get_node("B").position.x != 812.0:
		fail("A/B roots physically translate together")
		return
	var a_frame: int = scene.data.textures["A"].find(scene.get_node("A").texture)
	var b_frame: int = scene.data.textures["B"].find(scene.get_node("B").texture)
	if a_frame != b_frame or a_frame != scene.clock.frame_at(1000.0):
		fail("A/B same phase")
		return
	var original_x: float = scene.get_node("A").position.x
	scene.data.manifest["display_scale"] = 0.4
	scene.configure_display()
	scene.apply_time(1000.0)
	if scene.get_node("A").scale != Vector2(0.4, 0.4) or scene.get_node("A").position.x != original_x:
		fail("manifest scale must not affect root speed or be multiplied again by camera zoom")
		return
	print("PASS travel: actual screen translation, shared phase, parameter isolation, uneven/80ms timeline and explicit boundary reset")
	quit(0)
