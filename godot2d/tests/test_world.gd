extends SceneTree

var results: Dictionary = {}

func check(label: String, value: bool) -> void:
	results[label] = value
	print(("PASS " if value else "FAIL ") + label)

func _initialize() -> void:
	call_deferred("run")

func drive(action: String, ticks: int) -> void:
	Input.action_press(action)
	for i in range(ticks):
		await physics_frame
	Input.action_release(action)
	await physics_frame
	await physics_frame

func run() -> void:
	check("scene_exists", FileAccess.file_exists("res://scenes/harbor.tscn"))
	if not results.scene_exists:
		quit(1)
		return
	var scene = load("res://scenes/harbor.tscn").instantiate()
	root.add_child(scene)
	for i in range(5):
		await physics_frame
	var player = scene.player
	check("safe_spawn", player.position.distance_to(Vector2(330,250)) < 1)
	var start: Vector2 = player.position
	await drive("right", 30)
	var straight: float = player.position.distance_to(start)
	check("walk_distance", straight > 33 and straight < 40)
	player.position = Vector2(330,190)
	await physics_frame
	start = player.position
	Input.action_press("right")
	await drive("down", 30)
	Input.action_release("right")
	check("diagonal_normalized", abs(player.position.distance_to(start) - straight) < 3)
	player.position = Vector2(180,195)
	await physics_frame
	await drive("up", 45)
	check("house_blocks", player.position.y > 182 and player.position.y < 195)
	check("blocked_walk_idle", not player.walking)
	player.position = Vector2(360,250)
	await physics_frame
	await drive("down", 60)
	check("water_blocks", player.position.y < 271)
	player.position = Vector2(440,250)
	await physics_frame
	await drive("down", 90)
	check("pier_walkable", player.position.y > 350 and player.position.y < 370)
	await drive("down", 60)
	check("pier_end_blocks", player.position.y < 394)
	for entry in scene.data.locations():
		check("prompt_" + entry.id, scene.nearest_location(entry.point).get("id", "") == entry.id)
	check("prompt_range", scene.nearest_location(Vector2(20,40)).is_empty())
	check("y_sorted", scene.sort_layer.y_sort_enabled and player.get_parent() == scene.sort_layer)
	check("nearest_filter", scene.texture_filter == CanvasItem.TEXTURE_FILTER_NEAREST)
	check("viewport_1280", ProjectSettings.get_setting("display/window/size/viewport_width") == 1280)
	check("viewport_720", ProjectSettings.get_setting("display/window/size/viewport_height") == 720)
	check("fit_window_scaling", ProjectSettings.get_setting("display/window/stretch/scale_mode") == "fractional")
	check("independent_props", scene.sort_layer.get_child_count() >= 9)
	var house = scene.sort_layer.get_node("House")
	var house_sprite = house.get_child(0)
	var house_top: float = house.position.y - house_sprite.texture.get_height() * house_sprite.scale.y
	check("house_clear_of_header", house_top >= 32)
	check("player_readable_scale", player.sprite.sprite_frames.get_frame_texture("south",0).get_width() * player.sprite.scale.x >= 47.5)
	player.position = Vector2(442,236)
	await process_frame
	Input.action_press("inspect")
	await process_frame
	await process_frame
	Input.action_release("inspect")
	check("inspect_opens_panel", scene.hud.panel.visible and "补帆" in scene.hud.description.text)
	await process_frame
	await process_frame
	Input.action_press("inspect")
	await process_frame
	await process_frame
	Input.action_release("inspect")
	check("e_closes_panel", not scene.hud.panel.visible)
	Input.action_press("reset")
	await process_frame
	await process_frame
	Input.action_release("reset")
	check("reset_to_spawn", player.position.distance_to(Vector2(330,250)) < 1)
	check("four_directions", player.sprite.sprite_frames.get_animation_names().size() == 4)
	for name in ["south", "west", "east", "north"]:
		check("frames_" + name, player.sprite.sprite_frames.get_frame_count(name) == 4)
	for asset in ["environment.png", "player.png"]:
		var image = load("res://assets/" + asset).get_image()
		check("alpha_" + asset, image != null and image.detect_alpha() != Image.ALPHA_NONE)
	var atlas_image = load("res://assets/environment.png").get_image()
	var regions: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/regions.json"))
	for name in regions:
		var r: Array = regions[name]
		var bounds := Rect2i(r[0],r[1],r[2],r[3])
		check("atlas_bounds_" + name, Rect2i(Vector2i.ZERO,atlas_image.get_size()).encloses(bounds))
		check("atlas_nonempty_" + name, not atlas_image.get_region(bounds).is_invisible())
	var passed: bool = not results.values().has(false)
	DirAccess.make_dir_recursive_absolute("res://verification")
	var report = FileAccess.open("res://verification/tests.json", FileAccess.WRITE)
	report.store_string(JSON.stringify({"passed":passed,"checks":results,"engine":Engine.get_version_info().string,"scope":"Real input actions and physics, not visual approval"}, "\t"))
	print("RESULT ", results.size(), " checks, passed=", passed)
	quit(0 if passed else 1)
