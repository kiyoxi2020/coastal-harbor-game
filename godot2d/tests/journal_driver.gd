extends Node
var results: Dictionary = {}
var output_dir := "res://verification-journal"
func check(id: String, ok: bool) -> void:
	results[id] = ok
	print(("PASS " if ok else "FAIL ")+id)
func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	call_deferred("run")
func key(code: int) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.keycode = code
	event.pressed = true
	Input.parse_input_event(event)
	await get_tree().process_frame
	event = event.duplicate()
	event.pressed = false
	Input.parse_input_event(event)
	for i in range(3):
		await get_tree().process_frame
func shot(id: String) -> void:
	if DisplayServer.get_name() == "headless":
		return
	await RenderingServer.frame_post_draw
	check("screenshot_"+id, get_viewport().get_texture().get_image().save_png(output_dir.path_join(id+".png")) == OK)
func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):
			output_dir = arg.trim_prefix("--output=")
	DirAccess.make_dir_recursive_absolute(output_dir)
	var scene = get_parent()
	await get_tree().process_frame
	var ui = scene.journal
	check("title_on_start", ui.mode == "title" and get_tree().paused)
	if OS.get_cmdline_user_args().has("--resume-check"):
		check("restart_continue", scene.continue_game())
		check("restart_chest", scene.foraging.chest.count_item("clam") == 2)
		check("restart_backpack", scene.foraging.counts.snail == 2 and scene.foraging.counts.kelp == 2)
		check("restart_world", scene.foraging.collected.size() == 6 and not scene.pickup_nodes.clam_a.visible)
		check("restart_profile", scene.foraging.player_name == "海风" and scene.foraging.total_collected == 6)
		check("restart_settings", is_equal_approx(scene.settings.volumes.Music,0.35))
		await shot("10-restarted")
		finish({})
		return
	await shot("01-title")
	ui.new_game_dialog()
	await shot("07-name")
	await key(KEY_B)
	check("cancel_new_keeps_title", ui.mode == "title" and ui.modal == null)
	check("new_game", scene.start_new_game("海风"))
	await get_tree().process_frame
	check("world_resumes", not get_tree().paused)
	check("pixel_skin", ResourceLoader.exists("res://scripts/ui/pixel_style.gd"))
	check("bag_icon_exists", scene.hud.get("bag_button") is Button)
	if not results.bag_icon_exists:
		finish({})
		return
	scene.hud.bag_button.pressed.emit()
	check("icon_opens_bag", ui.mode == "bag" and get_tree().paused)
	check("empty_bag_reuses_hidden_icons", not ui.root.get_node("PauseMenu/Surface/BagPage/BagGrid/bag_0/Icon").visible)
	ui.close_menu()
	for entry in scene.data.pickups():
		check("collect_"+entry.id, scene.foraging.collect(entry.id, entry.kind))
	scene.refresh_pickups()
	check("save_progress", scene.save_progress())
	await key(KEY_B)
	check("bag_opens", ui.mode == "bag" and get_tree().paused)
	check("24_slots", ui.slots_count == 24)
	var persistent_root_id: int = ui.root.get_instance_id()
	var persistent_slot_ids: Array[int] = []
	for slot in ui.root.get_node("PauseMenu/Surface/BagPage/BagGrid").find_children("bag_*","Button",false,false):
		persistent_slot_ids.append(slot.get_instance_id())
	for iteration in range(20):
		ui.select_slot("bag",iteration%24)
		ui.show_page("profile")
		ui.show_page("settings")
		ui.show_page("bag")
	var current_slot_ids: Array[int] = []
	for slot in ui.root.get_node("PauseMenu/Surface/BagPage/BagGrid").find_children("bag_*","Button",false,false):
		current_slot_ids.append(slot.get_instance_id())
	check("persistent_pages_20_switches", ui.root.get_instance_id() == persistent_root_id and current_slot_ids == persistent_slot_ids)
	var press_count := [0]
	var sort_button := ui.root.get_node("PauseMenu/Surface/BagPage/sort") as Button
	sort_button.pressed.connect(func(): press_count[0] += 1)
	sort_button.grab_focus()
	await key(KEY_E)
	check("one_key_one_operation", press_count[0] == 1)
	var position: Vector2 = scene.player.position
	await key(KEY_R)
	check("menu_blocks_world", scene.player.position == position)
	await shot("02-bag")
	ui.select_slot("bag", 0)
	ui.action_split()
	check("split_dialog", is_instance_valid(ui.modal))
	await shot("08-quantity")
	await key(KEY_B)
	check("cancel_child_keeps_menu", ui.modal == null and ui.mode == "bag")
	ui.action_discard()
	check("discard_quantity", is_instance_valid(ui.modal))
	ui.accept_quantity()
	check("discard_confirmation", is_instance_valid(ui.modal) and ui.modal_kind == "confirm")
	await shot("09-confirm")
	await key(KEY_E)
	check("default_cancel_safe", scene.foraging.counts.clam == 2 and ui.modal == null)
	# Keyboard focus activates a real slot and quantity controls without mouse-only paths.
	ui.root.find_child("bag_0",true,false).grab_focus()
	await key(KEY_E)
	ui.root.find_child("split",true,false).grab_focus()
	await key(KEY_E)
	ui.modal.find_child("quantity_ok",true,false).grab_focus()
	await key(KEY_E)
	check("keyboard_split_pending", ui.pending == "split")
	ui.root.find_child("bag_3",true,false).grab_focus()
	await key(KEY_E)
	check("keyboard_split_applied", scene.foraging.bag.snapshot()[3].amount == 1 and scene.foraging.counts.clam == 2)
	scene.foraging.bag.organize()
	ui.show_page("profile")
	check("profile_real_data", ui.profile_text.contains("海风") and ui.profile_text.contains("6"))
	await shot("03-profile")
	await key(KEY_TAB)
	check("tab_keeps_menu", ui.mode == "profile" and get_tree().paused)
	await key(KEY_ESCAPE)
	scene.home.switch_room("house",scene.home.interior.spawn_point())
	scene.player.position = scene.home.storage_point()+Vector2(0,18)
	await key(KEY_E)
	check("storage_interaction", ui.mode == "storage" and get_tree().paused)
	var chest_scroll := ui.root.get_node("StoragePage/Surface/ChestScroll") as ScrollContainer
	ui.root.get_node("StoragePage/Surface/ChestScroll/ChestGrid/chest_47").grab_focus()
	await get_tree().process_frame
	await get_tree().process_frame
	check("storage_focus_scrolls", chest_scroll.scroll_vertical > 0)
	ui.select_slot("bag",0)
	ui.action_transfer()
	ui.accept_quantity()
	check("storage_transfer", scene.foraging.chest.count_item("clam") == 2 and scene.foraging.counts.clam == 0)
	check("stored_stats_unchanged", scene.foraging.total_collected == 6)
	check("storage_empty_and_occupied_icons", not ui.root.get_node("StoragePage/Surface/BagGrid/bag_0/Icon").visible and ui.root.get_node("StoragePage/Surface/ChestScroll/ChestGrid/chest_0/Icon").visible)
	await shot("04-storage")
	await key(KEY_B)
	check("storage_closes", ui.mode == "")
	ui.show_page("settings")
	await shot("05-settings")
	scene.return_to_title()
	check("title_return", ui.mode == "title")
	check("continue", scene.continue_game())
	check("restored_storage", scene.foraging.chest.count_item("clam") == 2)
	check("restored_world", scene.foraging.collected.size() == 6 and not scene.pickup_nodes.clam_a.visible)
	check("restored_stats", scene.foraging.total_collected == 6)
	# An actual fresh state is reconstructed by continue; settings persist separately.
	check("settings_write", scene.settings.set_volume("Music",0.35))
	var Settings = load("res://scripts/settings_service.gd")
	var reloaded = Settings.new(scene.save_service.directory)
	check("settings_persist", is_equal_approx(reloaded.volumes.Music,0.35))
	var gameplay_state = scene.foraging
	var State = load("res://scripts/player_state.gd")
	var full_state = State.new()
	full_state.bag.add("snail",24*99)
	scene.foraging = full_state
	ui.show_page("bag")
	var visible_icons := 0
	for slot in ui.root.get_node("PauseMenu/Surface/BagPage/BagGrid").find_children("bag_*","Button",false,false):
		if slot.get_node("Icon").visible:
			visible_icons += 1
	check("full_bag_renders_24_occupied", visible_icons == 24)
	await shot("13-full-bag")
	scene.foraging = gameplay_state
	var original_save = scene.save_service
	var blocked_root := "/private/tmp/coastal-journal-failure-"+str(Time.get_ticks_usec())
	DirAccess.make_dir_recursive_absolute(blocked_root)
	var blocker := FileAccess.open(blocked_root+"/blocker",FileAccess.WRITE)
	blocker.store_string("not a directory")
	blocker.close()
	var Save = load("res://scripts/save_service.gd")
	scene.save_service = Save.new(blocked_root+"/blocker/child")
	check("save_failure_detected", not scene.save_progress())
	scene.show_save_error(false)
	check("save_error_dialog", ui.modal_kind == "save_error" and is_instance_valid(ui.modal))
	await shot("14-save-error")
	await key(KEY_B)
	check("save_error_cancel_keeps_menu", ui.modal == null and ui.mode == "bag")
	scene.save_service = original_save
	ui.dismiss()
	await get_tree().process_frame
	check("world_visible_after_dialogs", ui.mode == "" and not get_tree().paused)
	await shot("06-world")
	var window_info: Dictionary = {}
	if DisplayServer.get_name() != "headless":
		var usable := DisplayServer.screen_get_usable_rect(get_window().current_screen)
		var size := get_window().size
		var ratio := float(size.x)*size.y/(float(usable.size.x)*usable.size.y)
		window_info = {"size":[size.x,size.y],"area_ratio":ratio,"mode":get_window().mode}
		check("half_desktop_window", ratio > 0.45 and ratio < 0.55 and get_window().mode == Window.MODE_WINDOWED)
		ui.show_page("bag")
		get_window().size = Vector2i(1600,1000)
		await get_tree().create_timer(0.3,true).timeout
		check("resize_internal_resolution", get_viewport().get_visible_rect().size == Vector2(1280,720))
		await shot("11-resized")
		get_window().size = size
		get_window().mode = Window.MODE_FULLSCREEN
		await get_tree().create_timer(0.6,true).timeout
		check("fullscreen", get_window().mode == Window.MODE_FULLSCREEN)
		await shot("12-fullscreen")
		get_window().mode = Window.MODE_WINDOWED
		await get_tree().create_timer(0.6,true).timeout
		check("back_to_window", get_window().mode == Window.MODE_WINDOWED)
		ui.dismiss()
	finish(window_info)

func finish(window_info: Dictionary) -> void:
	var passed := not results.values().has(false)
	var file := FileAccess.open(output_dir.path_join("tests.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify({"passed":passed,"checks":results,"window":window_info},"\t"))
	print("JOURNAL ", results.size(), " passed=", passed)
	get_tree().paused = false
	get_tree().quit(0 if passed else 1)
