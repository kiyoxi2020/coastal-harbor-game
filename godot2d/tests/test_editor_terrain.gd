extends SceneTree

const TERRAIN_SCENE := preload("res://scenes/world/terrain.tscn")
const EXTERIOR_SCENE := preload("res://scenes/world/harbor_exterior.tscn")
const WATER_SCRIPT := preload("res://scripts/water_detail.gd")

var checks: Dictionary = {}

func _initialize() -> void:
	call_deferred("run")

func check(label: String, passed: bool) -> void:
	checks[label] = passed
	print(("PASS " if passed else "FAIL ") + label)

func source_text(path: String) -> String:
	var file := FileAccess.open(path, FileAccess.READ)
	return file.get_as_text() if file != null else ""

func property_value(object: Object, property: StringName):
	for entry in object.get_property_list():
		if entry.name == property:
			return object.get(property)
	return null

func script_argument_count(script: Script, method_name: StringName) -> int:
	for method in script.get_script_method_list():
		if method.name == method_name:
			return method.args.size()
	return -1

func settle() -> void:
	await process_frame
	await RenderingServer.frame_post_draw

func capture_terrain(configure: Callable = Callable()) -> Image:
	var terrain := TERRAIN_SCENE.instantiate()
	var water := terrain.get_node_or_null("WaterDetail")
	if water != null:
		water.set_process(false)
		water.elapsed = 0.0
	if configure.is_valid():
		configure.call(terrain)
	root.add_child(terrain)
	await settle()
	var image := root.get_texture().get_image()
	root.remove_child(terrain)
	terrain.free()
	await process_frame
	return image

func capture_fixed_main(path: String) -> void:
	var world: Node2D = load("res://scenes/harbor.tscn").instantiate()
	world.set_meta("save_directory", "/private/tmp/coastal-editor-terrain-fixed-save")
	root.add_child(world)
	await process_frame
	await process_frame
	world.start_new_game("海风")
	await process_frame
	world.set_process(false)
	world.hud.set_process(false)
	world.player.set_physics_process(false)
	world.player.position = world.data.SPAWN
	world.player.sprite.stop()
	world.player.sprite.frame = 0
	var camera := world.get_node("WorldCamera") as Camera2D
	camera.set_process(false)
	camera.update_position()
	camera.reset_smoothing()
	camera.force_update_scroll()
	var water: Node = world.get_node("HarborExterior/Terrain/WaterDetail")
	water.set_process(false)
	water.elapsed = 0.0
	water.queue_redraw()
	await process_frame
	await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var error := root.get_texture().get_image().save_png(path)
	print("FIXED TERRAIN CAPTURE path=", path, " error=", error)
	quit(0 if error == OK else 1)

func run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--capture="):
			await capture_fixed_main(argument.trim_prefix("--capture="))
			return
		if argument == "--isolated-water-verify":
			var world: Node2D = load("res://scenes/harbor.tscn").instantiate()
			world.set_meta("save_directory", "/private/tmp/coastal-editor-terrain-water-save")
			root.add_child(world)
			return
	var terrain_source := source_text("res://scripts/terrain.gd")
	check("terrain_has_no_fixed_draw", not terrain_source.contains("func _draw"))
	check("terrain_has_no_ready_override", not terrain_source.contains("func _ready"))

	var terrain := TERRAIN_SCENE.instantiate()
	var layer_names := [
		"DeepWater", "ShallowBands", "WaterTint", "SubmergedRocks",
		"GrassField", "GrassTint", "StonePaths", "Verge", "TreeShadows",
		"Seawall", "Beach", "Steps", "Pier", "Flowers", "WaterDetail",
	]
	for layer_name in layer_names:
		check("visible_layer_" + layer_name, terrain.has_node(layer_name) and terrain.get_node(layer_name).visible)
	var deep := terrain.get_node_or_null("DeepWater") as Sprite2D
	var grass := terrain.get_node_or_null("GrassField") as Sprite2D
	var bands := terrain.get_node_or_null("ShallowBands")
	check("deep_is_editable_repeating_sprite", deep != null and deep.texture != null and not deep.centered and deep.region_enabled and deep.region_rect == Rect2(0, 0, 640, 144) and deep.position == Vector2(0, 272))
	check("grass_is_editable_repeating_sprite", grass != null and grass.texture != null and not grass.centered and grass.region_enabled and grass.region_rect == Rect2(0, 0, 640, 272))
	check("eighteen_shallow_band_sprites", bands != null and bands.get_child_count() == 18)
	if bands != null and bands.get_child_count() == 18:
		var bands_ok := true
		for row in range(18):
			var band := bands.get_child(row) as Sprite2D
			bands_ok = bands_ok and band != null and band.region_rect == Rect2(0, row * 8, 640, 8)
			bands_ok = bands_ok and band.position == Vector2(0, 272 + row * 8)
			bands_ok = bands_ok and not band.region_filter_clip_enabled
		check("shallow_band_sampling_contract", bands_ok)
	terrain.free()

	if DisplayServer.get_name() == "headless":
		check("native_render_deferred", not OS.get_cmdline_user_args().has("--require-render"))
	else:
		var original := await capture_terrain()
		var sprite_changed := await capture_terrain(func(node):
			var sprite := node.get_node_or_null("GrassField") as Sprite2D
			if sprite != null:
				sprite.self_modulate = Color(1, 0, 1, 1))
		var polygon_changed := await capture_terrain(func(node):
			var polygon: Node = node.get_node_or_null("GrassTint")
			if polygon != null:
				polygon.visible = false)
		check("inspector_sprite_change_persists_in_render", original.get_pixel(40, 40) != sprite_changed.get_pixel(40, 40))
		check("inspector_polygon_visibility_changes_render", original.get_pixel(40, 40) != polygon_changed.get_pixel(40, 40))

	var exterior := EXTERIOR_SCENE.instantiate()
	root.add_child(exterior)
	await process_frame
	var tree := exterior.get_node_or_null("DepthSortedObjects/CoastalTree0") as Node2D
	var follower := exterior.get_node_or_null("DepthSortedObjects/CoastalTree0/TerrainShadowFollower") as RemoteTransform2D
	var shadow := exterior.get_node_or_null("Terrain/TreeShadows/CoastalTree0Shadow") as Node2D
	check("tree_shadow_remote_transform", tree != null and follower != null and shadow != null)
	if tree != null and follower != null and shadow != null:
		var old_shadow_position := shadow.global_position
		var old_shadow_rotation := shadow.global_rotation
		var old_shadow_scale := shadow.global_scale
		tree.position += Vector2(9, 7)
		tree.rotation = 0.25
		tree.scale = Vector2(2, 2)
		await process_frame
		await process_frame
		check("tree_shadow_follows_position", shadow.global_position == old_shadow_position + Vector2(9, 7))
		check("tree_shadow_position_only", is_equal_approx(shadow.global_rotation, old_shadow_rotation) and shadow.global_scale.is_equal_approx(old_shadow_scale))
	root.remove_child(exterior)
	exterior.free()

	var terrain_a := TERRAIN_SCENE.instantiate()
	var terrain_b := TERRAIN_SCENE.instantiate()
	var water_a := terrain_a.get_node("WaterDetail")
	var water_b := terrain_b.get_node("WaterDetail")
	var config_a = property_value(water_a, "clip_config")
	var config_b = property_value(water_b, "clip_config")
	check("clip_config_exported", config_a != null and config_b != null)
	check("clip_config_local_to_scene", config_a != null and config_b != null and config_a != config_b)
	check("clip_instance_wrapper", water_a.has_method("contains_open_water") and water_b.has_method("contains_open_water"))
	check("clip_static_override_api", script_argument_count(WATER_SCRIPT, "is_open_water") == 2)
	if config_a != null and config_b != null and water_a.has_method("contains_open_water") and water_b.has_method("contains_open_water"):
		config_a.open_water_rect = Rect2(10, 300, 5, 5)
		config_a.excluded_rects.clear()
		check("clip_override_changes_only_instance", not water_a.contains_open_water(Vector2(30, 320)) and water_b.contains_open_water(Vector2(30, 320)))
		check("clip_default_not_polluted", WATER_SCRIPT.is_open_water(Vector2(30, 320)))
	terrain_a.free()
	terrain_b.free()

	var verifier_source := source_text("res://tests/verify_environment_render.gd")
	check("validator_uses_instance_clip", verifier_source.contains("water.contains_open_water(") and not verifier_source.contains("water.is_open_water("))

	var passed := not checks.values().has(false)
	print("EDITOR TERRAIN RESULT ", checks.size(), " passed=", passed)
	quit(0 if passed else 1)
