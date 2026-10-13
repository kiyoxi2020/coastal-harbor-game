extends Node2D

const data = preload("res://scripts/harbor_data.gd")
const Art = preload("res://scripts/atlas.gd")
var player: CharacterBody2D
var sort_layer: Node2D
var hud: CanvasLayer
var foraging = preload("res://scripts/foraging_state.gd").new()
var pickup_nodes: Dictionary = {}
const STORAGE_POINT = Vector2(274,194)
var journal
var save_service
var settings
var persistence_enabled := false
var session_started := false
var release_input := false
var save_message := ""

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
	var terrain := Node2D.new()
	terrain.name = "Terrain"
	terrain.set_script(load("res://scripts/terrain.gd"))
	add_child(terrain)
	var water_detail := Node2D.new()
	water_detail.name = "WaterDetail"
	water_detail.set_script(load("res://scripts/water_detail.gd"))
	terrain.add_child(water_detail)
	sort_layer = Node2D.new()
	sort_layer.name = "DepthSortedObjects"
	sort_layer.y_sort_enabled = true
	add_child(sort_layer)
	add_prop("house",Vector2(174,190),168)
	add_prop("market",Vector2(442,218),144)
	add_prop("garden",Vector2(126,224),78)
	add_prop("garden",Vector2(212,224),78)
	add_prop("crates",Vector2(523,233),29)
	add_prop("boat",Vector2(532,370),114)
	var tree_variants := [0,1,0,2,3]
	for i in range(data.TREES.size()):
		var tree := Node2D.new()
		tree.name = "CoastalTree%d" % i
		tree.position = data.TREES[i]
		tree.set_meta("tree_variant",tree_variants[i])
		var sprite := Sprite2D.new()
		sprite.texture = load("res://assets/tree-set-v4/tree-%d.png" % tree_variants[i])
		# Native-size 96px canvas, with trunk anchor (48,94).
		sprite.position = Vector2(0,-46)
		tree.add_child(sprite)
		sort_layer.add_child(tree)
	for rectangle in data.blockers():
		var body := StaticBody2D.new()
		body.position = rectangle.get_center()
		var collision := CollisionShape2D.new()
		var shape := RectangleShape2D.new()
		shape.size = rectangle.size
		collision.shape = shape
		body.add_child(collision)
		add_child(body)
	player = CharacterBody2D.new()
	player.set_script(load("res://scripts/player.gd"))
	player.name = "Returnee"
	player.position = data.SPAWN
	sort_layer.add_child(player)
	var camera := Camera2D.new()
	camera.name = "WorldCamera"
	camera.set_script(preload("res://scripts/world_camera.gd"))
	camera.target = player
	add_child(camera)
	hud = CanvasLayer.new()
	hud.set_script(load("res://scripts/hud.gd"))
	add_child(hud)
	for entry in data.pickups():
		var pickup := Node2D.new()
		pickup.set_script(preload("res://scripts/forage_pickup.gd"))
		pickup.kind = entry.kind
		pickup.position = entry.point
		pickup.name = entry.id
		sort_layer.add_child(pickup)
		pickup_nodes[entry.id] = pickup
	foraging.changed.connect(func(): hud.update_inventory(foraging.counts))
	hud.update_inventory(foraging.counts)
	hud.show_toast("低潮赶海：沿台阶下沙滩。暂不保存，重开重置。",8.0)
	var args := OS.get_cmdline_user_args()
	var old_verification: bool = get_meta("skip_verification",false)
	for arg in args:
		if arg.begins_with("--verify-") and arg != "--verify-journal":
			old_verification = true
	persistence_enabled = (DisplayServer.get_name() != "headless" and not old_verification) or get_meta("journal_test",false) or args.has("--verify-journal")
	var save_directory: String = get_meta("save_directory","user://coastal-progress")
	if args.has("--verify-journal"):
		save_directory = "/private/tmp/coastal-export-journal-"+str(Time.get_unix_time_from_system())
		for arg in args:
			if arg.begins_with("--test-save-directory=/private/tmp/coastal-"):
				save_directory = arg.trim_prefix("--test-save-directory=")
	save_service = preload("res://scripts/save_service.gd").new(save_directory)
	settings = preload("res://scripts/settings_service.gd").new(save_service.directory)
	journal = CanvasLayer.new()
	journal.set_script(preload("res://scripts/ui/journal.gd"))
	journal.world = self
	add_child(journal)
	if persistence_enabled:
		add_prop("crates",STORAGE_POINT,22)
		get_tree().auto_accept_quit = false
		hud.controls.text = "WASD / 方向键 移动   E 拾取 / 查看   B / Tab 手账   R 回路口"
		hud.show_toast("沿台阶赶海；旧屋东侧木箱可存放收获。",8)
		journal.show_page("title")
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

func add_prop(id: String, feet: Vector2, width: float) -> void:
	var root := Node2D.new()
	root.name = id.capitalize()
	root.position = feet
	var sprite := Sprite2D.new()
	sprite.texture = Art.region(id)
	var factor := width / sprite.texture.get_width()
	sprite.scale = Vector2.ONE * factor
	sprite.position = Vector2(0,-sprite.texture.get_height()*factor/2)
	root.add_child(sprite)
	sort_layer.add_child(root)

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
	for location in data.locations():
		var gap := point.distance_to(location.point)
		if gap < distance:
			distance = gap
			nearest = location
	return nearest

func nearest_pickup(point: Vector2) -> Dictionary:
	if not data.BEACH.has_point(point):
		return {}
	var nearest: Dictionary = {}
	var distance := 24.0
	for entry in data.pickups():
		if foraging.collected.has(entry.id):
			continue
		var gap := point.distance_to(entry.point)
		if gap <= 24.0 and (nearest.is_empty() or gap < distance):
			distance = gap
			nearest = entry
	return nearest

func _process(_delta: float) -> void:
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
		elif persistence_enabled and player.position.distance_to(STORAGE_POINT) <= 28:
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
		player.position = data.SPAWN
		player.velocity = Vector2.ZERO
		hud.dismiss()
	hud.update_location(nearest_location(player.position))
	var target := nearest_pickup(player.position)
	for id in pickup_nodes:
		pickup_nodes[id].highlighted = not hud.panel.visible and target.get("id","") == id
	if not target.is_empty():
		hud.prompt.text = "[ E ] 拾取" + data.ITEM_NAMES[target.kind]
	elif persistence_enabled and player.position.distance_to(STORAGE_POINT) <= 28:
		hud.prompt.text = "[ E ] 打开旧屋储物箱"
	elif foraging.collected.size() == data.pickups().size() and nearest_location(player.position).is_empty():
		hud.prompt.text = "今日赶海收获已集齐；市集交易将在后续版本开放。"

func refresh_pickups() -> void:
	for id in pickup_nodes:
		pickup_nodes[id].visible = not foraging.collected.has(id)
	hud.update_inventory(foraging.counts)

func _set_state(value) -> void:
	foraging = value
	foraging.changed.connect(func(): hud.update_inventory(foraging.counts))
	refresh_pickups()

func start_new_game(chosen_name: String) -> bool:
	var state = preload("res://scripts/player_state.gd").new()
	state.player_name = state.clean_name(chosen_name)
	if persistence_enabled and not save_service.write_save(state.to_data(data.SPAWN)):
		journal.note = save_service.last_error
		journal.render()
		return false
	_set_state(state)
	player.position = data.SPAWN
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
	var safe := data.WORLD_BOUNDS.has_point(position)
	for block in data.blockers():
		if block.grow(6).has_point(position): safe = false
	player.position = position if safe else data.SPAWN
	session_started = true
	journal.dismiss()
	hud.show_toast(result.message if result.message != "" else ("已继续上次的生活。" if safe else "已回到安全路口。"),8)
	return true

func save_progress() -> bool:
	if not persistence_enabled or not session_started: return true
	var ok: bool = save_service.write_save(foraging.to_data(player.position))
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
