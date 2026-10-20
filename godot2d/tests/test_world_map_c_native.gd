extends "res://tests/test_life_farming_native.gd"

func tap(code: int) -> void:
	await key(code, true)
	await key(code, false)

func tab_back() -> void:
	for pressed in [true, false]:
		var event := InputEventKey.new()
		event.physical_keycode = KEY_TAB
		event.shift_pressed = true
		event.pressed = pressed
		Input.parse_input_event(event)
		await process_frame
		await process_frame

func settle() -> void:
	for i in range(4):
		await process_frame

func repeat_key(code: int) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.keycode = code
	event.pressed = true
	event.echo = true
	Input.parse_input_event(event)
	await settle()
	event = event.duplicate()
	event.echo = false
	event.pressed = false
	Input.parse_input_event(event)
	await settle()

func run() -> void:
	evidence = "/private/tmp/coastal-map-single-native"
	DirAccess.make_dir_recursive_absolute(evidence)
	w = load("res://scenes/harbor.tscn").instantiate()
	w.set_meta("save_directory", "/private/tmp/coastal-map-single-native-save")
	root.add_child(w)
	check("native_renderer", DisplayServer.get_name() != "headless")
	check("isolated_save", w.save_service.directory == "/private/tmp/coastal-map-single-native-save")
	if w.save_service.directory != "/private/tmp/coastal-map-single-native-save":
		finish()
		return
	check("new_game", w.start_new_game("海湾导览"))
	await settle()
	var map = w.world_map
	check("C_region_selection_available", map.has_method("select_region"))
	if not map.has_method("select_region"):
		finish()
		return
	await tap(KEY_M)
	check("M_opens_paused", map.visible and paused)
	check("default_player_region", map.selected_region == "harbor")
	check("right_details_removed", not map.has_node("Root/Panel/Detail") and not map.has_node("Root/Panel/Resources"))
	await capture("01-harbor-default")

	var before: Dictionary = w.foraging.to_data(w.player.position)
	var initial_focus: Control = root.gui_get_focus_owner()
	check("overview_initial_focus", initial_focus == map.region_buttons.harbor)
	await repeat_key(KEY_UP)
	check("held_arrow_stays_in_navigation_contract", root.gui_get_focus_owner() == map.region_buttons[map.selected_region])
	await repeat_key(KEY_TAB)
	check("held_tab_does_not_bypass_group_navigation", root.gui_get_focus_owner() == initial_focus)
	# Restore the initial selection so a failed echo assertion cannot cascade.
	map.select_region("harbor")
	await tap(KEY_W)
	check("direction_selects_district", map.selected_region == "harbor_district")
	await capture("02-district-keyboard")
	check("selected_not_player_region", w.foraging.location == "harbor" and map.selected_region == "harbor_district")
	await tap(KEY_E)
	check("E_does_not_open_detail", map.visible and not map.has_node("Root/Panel/Detail"))
	await tap(KEY_ESCAPE)
	check("Esc_closes_directly", not map.visible and not paused)
	await settle()
	await tap(KEY_M)
	check("reopen_resets_current_region", map.selected_region == "harbor")

	# Tab groups must form a finite cycle and Shift+Tab must reverse it.
	initial_focus = root.gui_get_focus_owner()
	var visited: Array[Control] = []
	for i in range(2):
		await tap(KEY_TAB)
		visited.append(root.gui_get_focus_owner())
	check("tab_two_group_cycle", root.gui_get_focus_owner() == initial_focus)
	check("tab_visits_close", visited.has(map.get_node("Root/Panel/Close")))
	await tab_back()
	check("reverse_tab_close", root.gui_get_focus_owner() == map.get_node("Root/Panel/Close"))
	await tap(KEY_TAB)
	check("forward_tab_overview", root.gui_get_focus_owner() == initial_focus)

	for id in ["hillside", "residential_lane", "cape_coast"]:
		await click(map.region_buttons[id])
		check(id + "_mouse_selected", map.selected_region == id)
		check(id + "_no_fake_scene", map.find_children("*", "SubViewport", true, false).is_empty())
	await capture("04-future-region")
	await click(map.region_buttons.harbor)
	check("mouse_returns_harbor", map.selected_region == "harbor")
	# Tool keys, movement and mouse map selection must not mutate the world.
	await tap(KEY_1)
	await tap(KEY_2)
	check("map_state_unchanged", w.foraging.to_data(w.player.position) == before and w.journal.mode == "")
	await capture("05-harbor-return")
	await tap(KEY_ESCAPE)
	check("Esc_browser_closes", not map.visible and not paused)
	await settle()

	# Reach the real old-house entrance and verify the indoor default mapping.
	if not await walk_to(Vector2(270,244), "house_approach"):
		finish()
		return
	if not await walk_to(Vector2(270,194), "house_row"):
		finish()
		return
	if not await walk_to(w.home.exterior_door.approach, "house_door"):
		finish()
		return
	if not await pass_door("house", "inside_house"):
		finish()
		return
	await tap(KEY_M)
	check("house_defaults_harbor", map.visible and map.selected_region == "harbor")
	await capture("06-house-map")
	check("indoor_status_on_overview", map.region_buttons.harbor.text.contains("屋内"))
	await click(map.get_node("Root/Panel/Close"))
	check("mouse_close", not map.visible and not paused)
	await settle()

	for i in range(3):
		await tap(KEY_M)
		await click(map.region_buttons.harbor_district)
		await click(map.region_buttons.hillside)
		await click(map.region_buttons.harbor)
		await settle()
		check("reopen_no_snapshots_" + str(i), map.find_children("*", "SubViewport", true, false).is_empty())
		await tap(KEY_M)
	await settle()
	check("save_location_remains_house", w.foraging.location == "house")
	finish()
