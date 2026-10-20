extends SceneTree
# Native acceptance uses engine keyboard input and viewport mouse hit testing.
const Support = preload("res://tests/life_test_support.gd")
var support = Support.new()
var world
var evidence := "/private/tmp/coastal-P04-native"

func check(id: String, passed: bool) -> void:
	support.check(id, passed)

func _initialize() -> void:
	call_deferred("run")

func make_world():
	var scene = load("res://scenes/harbor.tscn").instantiate()
	# Native run follows normal startup; headless subprocess only probes CLI paths.
	if DisplayServer.get_name() == "headless":
		scene.set_meta("journal_test", true)
	root.add_child(scene)
	return scene

func key(code: int, pressed: bool) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.pressed = pressed
	Input.parse_input_event(event)
	await process_frame
	await process_frame

func click(button: Button) -> void:
	var point := button.get_global_transform_with_canvas() * (button.size / 2)
	var motion := InputEventMouseMotion.new()
	motion.position = point
	root.push_input(motion, true)
	for pressed in [true, false]:
		var event := InputEventMouseButton.new()
		event.position = point
		event.button_index = MOUSE_BUTTON_LEFT
		event.pressed = pressed
		root.push_input(event, true)
		await process_frame

func capture(name: String) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	var picture := root.get_texture().get_image()
	check("capture_" + name, picture.get_width() == 2560 and picture.get_height() == 1440 and picture.save_png(evidence.path_join(name + ".png")) == OK)

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--evidence-dir=/private/tmp/coastal-"):
			evidence = arg.trim_prefix("--evidence-dir=")
	DirAccess.make_dir_recursive_absolute(evidence)
	world = make_world()
	if OS.get_cmdline_user_args().has("--expect-path-refusal"):
		check("invalid_cli_refuses_new", world.startup_error != "" and not world.start_new_game("隔离测试") and not world.session_started)
		check("invalid_cli_refuses_continue", not world.continue_game() and world.save_service.directory.begins_with("/private/tmp/coastal-invalid-"))
		check("invalid_cli_buttons_disabled", world.journal.get_node("Root/MainMenu/Surface/new_game").disabled and world.journal.get_node("Root/MainMenu/Surface/continue").disabled)
		check("invalid_cli_reported", world.journal.get_node("Root/MainMenu/Surface/Status").text.contains("测试存档目录无效"))
		finish()
		return
	check("native_renderer", DisplayServer.get_name() != "headless")
	var directory: String = world.save_service.directory
	check("ordinary_cli_save_settings", directory.begins_with("/private/tmp/coastal-") and world.settings.path == directory.path_join("settings.cfg") and world.startup_error == "")
	if not directory.begins_with("/private/tmp/coastal-"):
		finish()
		return
	check("new_game", world.start_new_game("换日验收"))
	check("settings_written_to_cli", world.settings.set_volume("Music", 0.65) and FileAccess.file_exists(directory.path_join("settings.cfg")))
	# Set up a safe bedside start; all acceptance actions below use UI input.
	world.home.switch_room("house", Vector2(244, 240))
	check("bedside_safe", world.player.position == Vector2(244, 240) and world.home.safe_position("house", world.player.position) == world.player.position)
	check("fixture_saved", world.save_progress())
	await process_frame
	await process_frame
	var initial: Dictionary = world.foraging.to_data(world.player.position)
	var bed_position: Vector2 = world.player.position
	await key(KEY_E, true)
	check("e_opens_sleep", world.journal.mode == "sleep" and paused and world.journal.get_node("Root/SleepPage/Surface/Title").text.contains("第1日"))
	await capture("01-confirm")
	await click(world.journal.get_node("Root/SleepPage/Surface/Cancel"))
	check("mouse_cancel_no_effect", world.journal.mode == "" and world.foraging.to_data(world.player.position) == initial and world.player.position == bed_position)
	await process_frame
	check("held_e_no_reopen", world.journal.mode == "" and world.release_input)
	await key(KEY_E, false)
	await key(KEY_E, true)
	await key(KEY_E, false)
	check("e_reopens_after_release", world.journal.mode == "sleep")
	await key(KEY_ESCAPE, true)
	await key(KEY_ESCAPE, false)
	check("escape_cancels", world.journal.mode == "" and world.foraging.to_data(world.player.position) == initial)
	await key(KEY_E, true)
	await key(KEY_E, false)
	var blocker := directory.path_join("blocked")
	var f := FileAccess.open(blocker, FileAccess.WRITE)
	f.store_string("blocked")
	f.close()
	world.save_service.directory = blocker.path_join("child")
	await click(world.journal.get_node("Root/SleepPage/Surface/Confirm"))
	check("native_failure_stays", world.journal.mode == "sleep" and world.foraging.to_data(world.player.position) == initial and world.journal.get_node("Root/SleepPage/Surface/Body").text.contains("尚未保存"))
	await capture("02-save-failure")
	var request_id: int = world.journal.sleep_request_id
	world.save_service.directory = directory
	await click(world.journal.get_node("Root/SleepPage/Surface/Confirm"))
	check("native_confirm_advances_once", world.journal.mode == "daily" and paused and world.foraging.life.day_id == 2 and world.foraging.life.action_seq == request_id and world.foraging.life.daily_reports.size() == 1)
	check("native_stays_at_bed", world.foraging.location == "house" and world.player.position == bed_position and not world.home.transition.busy)
	check("native_summary", world.journal.get_node("Root/DailyPage/Surface/Title").text.contains("第1日") and world.journal.get_node("Root/DailyPage/Surface/Title").text.contains("第2日"))
	await capture("03-next-day")
	# A second native click at the former confirm position cannot submit another sleep.
	await click(world.journal.get_node("Root/SleepPage/Surface/Confirm"))
	check("double_click_once", world.foraging.life.day_id == 2)
	var stored: Dictionary = world.save_service.read_save()
	check("actual_disk_day2", stored.ok and stored.data.life.day_id == 2 and stored.data.life.last_settled_day == 1 and stored.data.location == "house")
	var expected_sequence: int = world.foraging.life.action_seq
	world.queue_free()
	paused = false
	await process_frame
	world = make_world()
	check("native_continue", world.continue_game() and world.foraging.life.day_id == 2 and world.foraging.life.action_seq == expected_sequence and world.player.position == bed_position)
	await process_frame
	await process_frame
	await key(KEY_E, true)
	await key(KEY_E, false)
	check("reloaded_confirmation_day2", world.journal.mode == "sleep" and world.journal.get_node("Root/SleepPage/Surface/Title").text.contains("第2日"))
	await capture("04-reloaded")
	await click(world.journal.get_node("Root/SleepPage/Surface/Cancel"))
	check("reload_cancel_no_settlement", world.foraging.life.day_id == 2 and world.foraging.life.daily_reports.size() == 1)
	finish()

func finish() -> void:
	var failed: int = support.checks.values().count(false)
	var f := FileAccess.open(evidence.path_join("checks.json"), FileAccess.WRITE)
	f.store_string(JSON.stringify(support.checks, "\t"))
	f.close()
	print("LIFE_DAY_NATIVE ", support.checks.size() - failed, "/", support.checks.size(), " failures=", failed)
	quit(0 if failed == 0 else 1)
