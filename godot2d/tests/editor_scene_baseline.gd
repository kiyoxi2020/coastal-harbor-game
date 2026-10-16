extends SceneTree

const OUTPUT := "/private/tmp/coastal-editor-baseline"
const SAVE_DIR := "/private/tmp/coastal-editor-baseline-save"

var world: Node2D
var checks: Dictionary = {}
var captures: Array[Dictionary] = []

func _initialize() -> void:
	call_deferred("run")

func check(id: String, value: bool) -> void:
	checks[id] = value
	print(("PASS " if value else "FAIL ") + id)

func settle(frames := 4) -> void:
	for _i in range(frames):
		await process_frame

func shot(id: String, expected_mode: String) -> void:
	await settle()
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	var path := OUTPUT.path_join(id + ".png")
	var error := image.save_png(path)
	check("shot_" + id, error == OK)
	captures.append({
		"id": id,
		"path": path,
		"size": [image.get_width(), image.get_height()],
		"journal_mode": world.journal.mode,
		"modal_kind": world.journal.modal_kind,
		"location": world.foraging.location,
		"expected": expected_mode,
	})

func run() -> void:
	DirAccess.make_dir_recursive_absolute(OUTPUT)
	world = load("res://scenes/harbor.tscn").instantiate()
	world.set_meta("save_directory", SAVE_DIR)
	root.add_child(world)
	await settle(8)

	check("isolated_save", world.save_service.directory.begins_with("/private/tmp/coastal-"))
	check("title_ready", world.journal.mode == "title" and paused)
	await shot("01-main-menu", "title")
	world.journal.new_game_dialog()
	check("name_dialog", world.journal.modal_kind == "name")
	await shot("02-name-dialog", "name dialog")
	world.journal.cancel_modal()
	check("new_game", world.start_new_game("海风"))
	await settle()
	await shot("03-hud-outdoor", "outdoor HUD")

	world.journal.show_page("bag")
	check("bag_page", world.journal.mode == "bag")
	await shot("04-bag", "bag page")
	world.journal.show_page("profile")
	await shot("05-profile", "profile page")
	world.journal.show_page("settings")
	await shot("06-settings", "settings page")
	world.journal.dismiss()

	check("collect_clam_a", world.foraging.collect("clam_a", "clam"))
	check("collect_clam_b", world.foraging.collect("clam_b", "clam"))
	world.refresh_pickups()
	world.journal.show_page("bag")
	world.journal.select_slot("bag", 0)
	world.journal.action_split()
	check("quantity_dialog", world.journal.modal_kind == "quantity")
	await shot("07-quantity-dialog", "quantity dialog")
	world.journal.cancel_modal()
	world.journal.action_discard()
	check("discard_quantity_dialog", world.journal.modal_kind == "quantity")
	world.journal.accept_quantity()
	check("confirm_dialog", world.journal.modal_kind == "confirm")
	await shot("08-confirm-dialog", "confirm dialog")
	world.journal.cancel_modal()
	world.journal.dismiss()

	world.player.position = world.home.storage_point()
	world.journal.show_page("storage")
	check("storage_page", world.journal.mode == "storage")
	await shot("09-storage", "storage page")
	world.journal.dismiss()

	var normal_save = world.save_service
	world.save_service = load("res://scripts/save_service.gd").new(SAVE_DIR + "/progress.json/impossible")
	world.show_save_error(false)
	check("save_error_dialog", world.journal.modal_kind == "save_error")
	await shot("10-save-error-dialog", "save error dialog")
	world.journal.cancel_modal()
	world.journal.dismiss()
	world.save_service = normal_save

	check("switch_indoor", world.home.switch_room("house", Vector2(320, 288)))
	await shot("11-house-interior", "house interior HUD")
	check("switch_outdoor", world.home.switch_room("harbor", world.data.SPAWN))
	await shot("12-harbor-exterior", "harbor exterior HUD")

	world.journal.show_page("bag")
	root.get_window().size = Vector2i(1600, 1000)
	await create_timer(0.35, true).timeout
	await shot("13-resized-bag", "resized bag page")
	root.get_window().mode = Window.MODE_FULLSCREEN
	await create_timer(0.65, true).timeout
	await shot("14-fullscreen-bag", "fullscreen bag page")
	root.get_window().mode = Window.MODE_WINDOWED
	world.journal.dismiss()

	var report := FileAccess.open(OUTPUT.path_join("baseline.json"), FileAccess.WRITE)
	report.store_string(JSON.stringify({
		"passed": not checks.values().has(false),
		"checks": checks,
		"captures": captures,
		"renderer": RenderingServer.get_current_rendering_method(),
		"save_directory": SAVE_DIR,
	}, "\t"))
	report.close()
	print("EDITOR_BASELINE ", checks.size(), " passed=", not checks.values().has(false))
	quit(1 if checks.values().has(false) else 0)
