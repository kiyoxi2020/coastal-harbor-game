extends SceneTree

var checks: Dictionary = {}

func check(label: String, passed: bool) -> void:
	checks[label] = passed
	print(("PASS " if passed else "FAIL ")+label)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var scene = load("res://scenes/harbor.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	var camera = scene.get_node("WorldCamera")
	check("internal_720p",root.get_visible_rect().size == Vector2(1280,720))
	check("startup_windowed",ProjectSettings.get_setting("display/window/size/mode") == Window.MODE_WINDOWED)
	check("camera_zoom",camera.zoom == Vector2(2,2))
	var initial_position: Vector2 = camera.position
	scene.player.position = Vector2(294,353)
	camera.update_position()
	camera.force_update_scroll()
	await process_frame
	check("camera_follows",camera.position.y > initial_position.y)
	check("camera_stays_in_map",camera.position.y <= 236 and camera.position.x == 320)
	var screen_point: Vector2 = scene.get_canvas_transform() * scene.player.position
	check("beach_above_prompts",screen_point.y < scene.hud.prompt.position.y-20)
	scene.hud.show_location(scene.data.locations()[0])
	await process_frame
	check("panel_inside_screen",Rect2(Vector2.ZERO,Vector2(1280,720)).encloses(scene.hud.panel.get_rect()))
	check("footer_at_bottom",scene.hud.bottom.position.y == 686)
	check("header_full_width",scene.hud.top.size.x == 1280)
	check("inventory_on_screen",scene.hud.inventory.get_rect().end.x <= 1280)
	check("native_hud_font",scene.hud.description.get_theme_font_size("font_size") == 24)
	scene.player.position = Vector2(330,80)
	camera.update_position()
	check("north_edge_clamped",camera.position.y == 180)
	DirAccess.make_dir_recursive_absolute("res://verification-display")
	var report = FileAccess.open("res://verification-display/tests.json",FileAccess.WRITE)
	var passed := not checks.values().has(false)
	report.store_string(JSON.stringify({"passed":passed,"checks":checks},"\t"))
	quit(0 if passed else 1)
