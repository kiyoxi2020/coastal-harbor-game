extends Node2D

const data = preload("res://scripts/harbor_data.gd")
const Art = preload("res://scripts/atlas.gd")
var player: CharacterBody2D
var sort_layer: Node2D
var hud: CanvasLayer
var foraging = preload("res://scripts/foraging_state.gd").new()
var pickup_nodes: Dictionary = {}
var journal
var save_service
var settings
var persistence_enabled := false
var session_started := false
var release_input := false
var save_message := ""
var home
var exterior: Node2D

func _ready() -> void:
	# Size the native window once per launch, preserving manual resizing thereafter.
	var window := get_window()
	if DisplayServer.get_name() != "headless" and not window.has_meta("startup_window_sized"):
		var available := DisplayServer.screen_get_usable_rect(window.current_screen)
		window.mode = Window.MODE_WINDOWED
		window.size = Vector2i((Vector2(available.size)*sqrt(0.5)).round())
		window.position = available.position+(available.size-window.size)/2
		window.set_meta("startup_window_sized",true)
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	configure_input()
	exterior = $HarborExterior
	sort_layer = exterior.get_node("DepthSortedObjects") as Node2D
	player = sort_layer.get_node("Returnee") as CharacterBody2D
	player.world=self
	var camera := get_node("WorldCamera") as Camera2D
	camera.target = player
	camera.update_position()
	camera.reset_smoothing()
	camera.force_update_scroll()
	hud = $HUD
	journal = $Journal
	var interior := $HouseInterior
	home = $HouseSession
	var transition := $HouseSession/RoomTransition
	home.initialize(self, exterior, interior, exterior.get_node("DepthSortedObjects/ExteriorDoor"), transition)
	for pickup in exterior.get_node("DepthSortedObjects/ForagePickups").get_children():
		pickup_nodes[pickup.name] = pickup
	hud.show_toast("低潮赶海：沿台阶下沙滩。暂不保存，重开重置。",8.0)
	var args := OS.get_cmdline_user_args()
	var old_verification: bool = get_meta("skip_verification",false)
	for arg in args:
		if arg.begins_with("--verify-") and arg not in ["--verify-journal","--verify-house"]:
			old_verification = true
	persistence_enabled = (DisplayServer.get_name() != "headless" and not old_verification) or get_meta("journal_test",false) or args.has("--verify-journal") or args.has("--verify-house")
	var save_directory: String = get_meta("save_directory","user://coastal-progress")
	if args.has("--verify-journal") or args.has("--verify-house"):
		save_directory = "/private/tmp/coastal-export-journal-"+str(Time.get_unix_time_from_system())
		for arg in args:
			if arg.begins_with("--test-save-directory=/private/tmp/coastal-"):
				save_directory = arg.trim_prefix("--test-save-directory=")
	save_service = preload("res://scripts/save_service.gd").new(save_directory)
	settings = preload("res://scripts/settings_service.gd").new(save_service.directory)
	journal.initialize(self)
	hud.bag_requested.connect(func():
		if persistence_enabled and session_started and not hud.panel.visible and journal.mode == "" and not home.transition.busy:
			journal.selected_side = "bag"
			journal.selected_index = 0
			journal.show_page("bag"))
	if persistence_enabled:
		exterior.get_node("DepthSortedObjects/StorageCrates").show()
		get_tree().auto_accept_quit = false
		hud.controls.text = "WASD / 方向键 移动   E 拾取 / 查看   B / Tab 手账   R 回路口"
		hud.show_toast("沿台阶赶海；旧屋东侧木箱可存放收获。",8)
		journal.show_page("title")
	if args.has("--verify-house"):
		var runner:=Node.new()
		runner.set_script(load("res://tests/house_driver.gd"))
		add_child(runner)
		return
	if args.has("--verify-journal"):
		var runner := Node.new()
		runner.set_script(load("res://tests/journal_driver.gd"))
		add_child(runner)
		return
	# Explicit opt-in integration harness also runs inside an exported app.
	if get_meta("skip_verification",false):
		return
	if OS.get_cmdline_user_args().has("--verify-foraging"):
		var runner := Node.new()
		runner.set_script(load("res://tests/foraging_driver.gd"))
		add_child(runner)
	elif OS.get_cmdline_user_args().has("--verify-interaction"):
		var runner := Node.new()
		runner.set_script(load("res://tests/interaction_driver.gd"))
		add_child(runner)
	elif OS.get_cmdline_user_args().has("--verify-route"):
		var runner := Node.new()
		runner.set_script(load("res://tests/route_driver.gd"))
		add_child(runner)
	elif OS.get_cmdline_user_args().has("--verify-environment"):
		var runner := Node.new()
		runner.set_script(load("res://tests/verify_environment_render.gd"))
		add_child(runner)

func configure_input() -> void:
	var keys = {"left":[KEY_A,KEY_LEFT],"right":[KEY_D,KEY_RIGHT],"up":[KEY_W,KEY_UP],"down":[KEY_S,KEY_DOWN],"inspect":[KEY_E],"reset":[KEY_R],"journal":[KEY_B,KEY_TAB]}
	for action in keys:
		if InputMap.has_action(action):
			continue
		InputMap.add_action(action)
		for key in keys[action]:
			var event := InputEventKey.new()
			event.physical_keycode = key
			InputMap.action_add_event(action,event)

func nearest_location(point: Vector2) -> Dictionary:
	var nearest: Dictionary = {}
	var distance := 28.0
	var locations: Array=home.interior.locations() if foraging.location=="house" else exterior.locations()
	for location in locations:
		var gap := point.distance_to(location.point)
		if gap < distance:
			distance = gap
			nearest = location
	return nearest

func nearest_pickup(point: Vector2) -> Dictionary:
	if foraging.location=="house" or not exterior.foraging_area.has_point(point):
		return {}
	var nearest: Dictionary = {}
	var distance := 24.0
	for entry in exterior.pickups():
		if foraging.collected.has(entry.id):
			continue
		var gap := point.distance_to(entry.point)
		if gap <= 24.0 and (nearest.is_empty() or gap < distance):
			distance = gap
			nearest = entry
	return nearest

func _process(_delta: float) -> void:
	if home != null and home.transition.busy: return
	if release_input:
		for action in ["inspect","reset","journal","left","right","up","down"]:
			if Input.is_action_pressed(action):
				return
		release_input = false
		return
	if persistence_enabled and Input.is_action_just_pressed("journal") and not hud.panel.visible:
		journal.show_page(journal.last_page)
		return
	if Input.is_action_just_pressed("inspect"):
		if hud.panel.visible:
			hud.dismiss()
		elif persistence_enabled and home.active_door().can_interact(player.position):
			home.transition.begin()
			return
		elif persistence_enabled and player.position.distance_to(home.storage_point()) <= 28:
			journal.selected_side = "bag"
			journal.selected_index = 0
			journal.show_page("storage")
			return
		else:
			var target := nearest_pickup(player.position)
			if not target.is_empty():
				if foraging.collect(target.id,target.kind):
					pickup_nodes[target.id].hide()
					hud.show_toast(data.ITEM_NAMES[target.kind]+" +1")
					save_progress()
				else:
					hud.show_toast("背包已满，物品留在原地。")
			else:
				hud.show_location(nearest_location(player.position))
	if Input.is_action_just_pressed("reset"):
		home.reset_player()
	hud.update_location(nearest_location(player.position))
	var target := nearest_pickup(player.position)
	for id in pickup_nodes:
		pickup_nodes[id].highlighted = not hud.panel.visible and target.get("id","") == id
	if not target.is_empty():
		hud.prompt.text = "[ E ] 拾取" + data.ITEM_NAMES[target.kind]
	elif persistence_enabled and home.active_door().can_interact(player.position):
		hud.prompt.text="[ E ] 走出小屋" if foraging.location=="house" else "[ E ] 进入小屋"
	elif persistence_enabled and player.position.distance_to(home.storage_point()) <= 28:
		hud.prompt.text = "[ E ] 打开旧屋储物箱"
	elif foraging.location=="house" and nearest_location(player.position).is_empty():
		hud.prompt.text="回到熟悉的屋子；床、厨房和旧照片可查看。"
	elif foraging.collected.size() == exterior.pickups().size() and nearest_location(player.position).is_empty():
		hud.prompt.text = "今日赶海收获已集齐；市集交易将在后续版本开放。"

func refresh_pickups() -> void:
	for id in pickup_nodes:
		pickup_nodes[id].visible = not foraging.collected.has(id)

func _set_state(value) -> void:
	foraging = value
	refresh_pickups()

func start_new_game(chosen_name: String) -> bool:
	var state = preload("res://scripts/player_state.gd").new()
	state.player_name = state.clean_name(chosen_name)
	var spawn: Vector2 = exterior.spawn_point()
	if persistence_enabled and not save_service.write_save(state.to_data(spawn)):
		journal.note = save_service.last_error
		journal.render()
		return false
	_set_state(state)
	home.switch_room("harbor",spawn)
	session_started = true
	journal.dismiss()
	hud.show_toast("欢迎回来，"+foraging.player_name+"。E 赶海，B 打开手账。",8)
	return true

func continue_game() -> bool:
	var result: Dictionary = save_service.read_save()
	if not result.ok:
		journal.note = result.message
		journal.render()
		return false
	var state = preload("res://scripts/player_state.gd").new()
	if not state.restore(result.data): return false
	_set_state(state)
	var position := Vector2(result.data.position[0],result.data.position[1])
	var safe: bool=home.safe_position(state.location,position)==position
	home.switch_room(state.location,position)
	session_started = true
	journal.dismiss()
	hud.show_toast(result.message if result.message != "" else ("已继续上次的生活。" if safe else "已回到安全路口。"),8)
	return true

func save_progress() -> bool:
	if not persistence_enabled or not session_started: return true
	var snapshot: Dictionary=home.transition.stable_snapshot if home.transition.busy else foraging.to_data(home.safe_position(foraging.location,player.position))
	var ok: bool = save_service.write_save(snapshot)
	save_message = "进度已保存。" if ok else save_service.last_error
	if not ok:
		hud.show_toast(save_message,10)
		journal.note = save_message
	return ok

func return_to_title() -> void:
	if not save_progress():
		show_save_error(false)
		return
	session_started = false
	journal.from_title = false
	journal.show_page("title")

func request_exit() -> void:
	if home != null and home.transition.busy:
		home.transition.exit_pending=true
		return
	if save_progress():
		get_tree().quit()
	else:
		show_save_error(true)

func show_save_error(exit_game: bool) -> void:
	if journal.mode == "": journal.show_page("settings")
	journal.show_save_failure(save_service.last_error,exit_game)

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST and persistence_enabled:
		request_exit()
