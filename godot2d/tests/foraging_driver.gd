extends Node

var results: Dictionary = {}
var output_dir := "res://verification-foraging"
var window_measurement: Dictionary = {}

func check(label: String, value: bool) -> void:
	results[label] = value
	print(("PASS " if value else "FAIL ") + label)

func _ready() -> void:
	call_deferred("run")

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):
			output_dir = arg.trim_prefix("--output=")
	check("state_module_exists", ResourceLoader.exists("res://scripts/foraging_state.gd"))
	if not results.state_module_exists:
		get_tree().quit(1)
		return
	var state = load("res://scripts/foraging_state.gd").new()
	check("initial_empty", state.counts == {"clam":0,"snail":0,"kelp":0})
	check("invalid_type", not state.add_item("unknown",1))
	check("invalid_zero", not state.add_item("clam",0))
	check("invalid_negative", not state.add_item("clam",-1))
	check("collect_once", state.collect("a","clam") and state.counts.clam == 1)
	check("no_duplicate", not state.collect("a","clam") and state.counts.clam == 1)
	check("invalid_keeps_node", not state.collect("b","unknown") and not state.collected.has("b"))
	check("empty_id_rejected", not state.collect("","clam"))
	var data = load("res://scripts/harbor_data.gd")
	check("pickup_data_exists", data.has_method("pickups"))
	if results.pickup_data_exists:
		var ids := {}
		var fresh = load("res://scripts/foraging_state.gd").new()
		for entry in data.pickups():
			check("unique_"+entry.id, not ids.has(entry.id))
			ids[entry.id] = true
			check("inside_"+entry.id, data.BEACH.has_point(entry.point))
			fresh.collect(entry.id,entry.kind)
		check("six_points", ids.size() == 6)
		check("two_each", fresh.counts == {"clam":2,"snail":2,"kelp":2})
	await integration()
	finish()

func press(action: String, frames: int = 3) -> void:
	# Screenshots resume after draw; inject before the next scene input poll.
	await get_tree().process_frame
	Input.action_press(action)
	for i in range(frames):
		await get_tree().physics_frame
	Input.action_release(action)
	for i in range(3):
		await get_tree().physics_frame

func integration() -> void:
	var scene = get_parent()
	for i in range(5):
		await get_tree().physics_frame
	check("scene_pickup_api", scene.has_method("nearest_pickup"))
	if DisplayServer.get_name() != "headless":
		var window := get_window()
		var available := DisplayServer.screen_get_usable_rect(window.current_screen)
		var actual_size := DisplayServer.window_get_size(window.get_window_id())
		window_measurement = {"mode":window.mode,"window_size":[actual_size.x,actual_size.y],"desktop_usable_size":[available.size.x,available.size.y]}
		var area_ratio := float(actual_size.x)*actual_size.y/(float(available.size.x)*available.size.y)
		window_measurement["desktop_area_ratio"] = area_ratio
		check("startup_windowed",window.mode == Window.MODE_WINDOWED)
		check("half_desktop_area",area_ratio >= 0.45 and area_ratio <= 0.55)
		check("window_centered",Vector2(window.position+actual_size/2-available.get_center()).length() < 80)
		print("WINDOW ",window_measurement)
	if not results.scene_pickup_api:
		return
	check("six_visuals", scene.pickup_nodes.size() == 6)
	check("outside_no_pickup", scene.nearest_pickup(Vector2(244,316)).is_empty())
	check("within_24", scene.nearest_pickup(Vector2(268,330)).get("id","") == "clam_a")
	check("outside_24", scene.nearest_pickup(Vector2(269,330)).is_empty())
	check("stable_tie", scene.nearest_pickup(Vector2(244,341.5)).get("id","") == "clam_a")
	var water = load("res://scripts/water_detail.gd")
	check("no_water_on_sand", not water.is_open_water(Vector2(244,330)))
	check("sea_still_water", water.is_open_water(Vector2(200,340)))
	# Real movement through stairs and beach, with no teleport across the shore.
	await press("left",28)
	await press("down",67)
	check("stairs_to_sand", scene.data.BEACH.has_point(scene.player.position))
	await press("left",43)
	check("west_pickup_reachable", scene.player.position.distance_to(Vector2(244,330)) < 8)
	await press("left",50)
	check("west_sea_blocked", scene.player.position.x >= 228)
	await press("right",97)
	check("east_pickup_reachable", scene.player.position.distance_to(Vector2(344,330)) < 8)
	await press("right",50)
	check("east_sea_blocked", scene.player.position.x <= 364)
	await press("down",70)
	check("south_sea_blocked", scene.player.position.y <= 366)
	await press("left",56)
	await press("up",95)
	check("beach_exit", scene.player.position.y < 270)
	await shot("11-export-before")
	# Test actual input priority, not direct inventory mutations.
	scene.player.position = Vector2(244,330)
	scene.hud.show_location(scene.data.locations()[0])
	await press("inspect")
	check("close_does_not_collect", not scene.hud.panel.visible and scene.foraging.counts.clam == 0)
	await press("inspect",40)
	check("hold_collects_once", scene.foraging.counts.clam == 1 and scene.foraging.collected.size() == 1)
	check("collected_hidden", not scene.pickup_nodes.clam_a.visible)
	check("pickup_feedback", "蛤蜊 +1" in scene.hud.toast.text and scene.hud.bag_button != null)
	await press("reset")
	check("reset_keeps_loot", scene.foraging.counts.clam == 1 and scene.player.position.distance_to(scene.data.SPAWN) < 1)
	for entry in scene.data.pickups():
		if scene.foraging.collected.has(entry.id):
			continue
		scene.player.position = entry.point
		await get_tree().physics_frame
		await press("inspect")
	check("collected_all", scene.foraging.counts == {"clam":2,"snail":2,"kelp":2})
	check("completion_prompt", "已集齐" in scene.hud.prompt.text)
	check("empty_after_all", scene.nearest_pickup(Vector2(294,330)).is_empty())
	await shot("12-export-complete")
	var fresh_scene = load("res://scenes/harbor.tscn").instantiate()
	fresh_scene.set_meta("skip_verification",true)
	fresh_scene.set_meta("save_directory", "/private/tmp/coastal-foraging-restart-" + str(Time.get_ticks_usec()))
	get_tree().root.add_child(fresh_scene)
	await get_tree().process_frame
	check("restart_empty", fresh_scene.foraging.counts == {"clam":0,"snail":0,"kelp":0})
	check("no_save_notice", "暂不保存" in fresh_scene.hud.toast.text)
	fresh_scene.queue_free()

func shot(name: String) -> void:
	if DisplayServer.get_name() == "headless":
		return
	DirAccess.make_dir_recursive_absolute(output_dir)
	await RenderingServer.frame_post_draw
	var error := get_viewport().get_texture().get_image().save_png(output_dir.path_join(name+".png"))
	check("saved_"+name,error == OK)

func finish() -> void:
	var passed := not results.values().has(false)
	DirAccess.make_dir_recursive_absolute(output_dir)
	var report = FileAccess.open(output_dir.path_join("tests.json"), FileAccess.WRITE)
	report.store_string(JSON.stringify({"passed":passed,"checks":results,"window":window_measurement},"\t"))
	print("RESULT ",results.size()," checks, passed=",passed)
	get_tree().quit(0 if passed else 1)
