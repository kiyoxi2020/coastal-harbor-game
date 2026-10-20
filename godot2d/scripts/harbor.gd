extends Node2D

const data = preload("res://scripts/harbor_data.gd")
const ActionService = preload("res://scripts/simulation/action_service.gd")
const ACTION_MESSAGES := {
	"unknown_action":"此操作尚未开放。", "unknown_item":"无法识别该物品。",
	"invalid_amount":"数量须为1至99的整数。", "invalid_request":"操作请求无效，请重新选择。",
	"stale_request":"此操作已过期，请重新选择。", "unknown_account":"无法找到该商户。",
	"not_allowed":"当前无法进行此操作。", "insufficient_funds":"买方金币不足，交易未完成。",
	"insufficient_stock":"所需物品数量不足。", "inventory_full":"接收方容器已满，交易未完成。",
	"quota_exceeded":"商户今日收购额度不足。", "invalid_state":"进度校验失败，操作未完成。",
	"plot_empty":"这格还没有作物。", "plot_occupied":"这格已有作物。",
	"not_tilled":"请先用锄头翻土。", "already_tilled":"这格已经翻过土。",
	"already_watered":"今天已经浇过水。", "not_mature":"作物尚未成熟。",
	"save_failed":"尚未保存，请重试；本次操作未生效。", "invalid_day":"日期已变化，请关闭后重新确认。"
}
const Art = preload("res://scripts/atlas.gd")
var player: CharacterBody2D
var sort_layer: Node2D
var hud: CanvasLayer
var foraging = preload("res://scripts/foraging_state.gd").new()
var pickup_nodes: Dictionary = {}
var journal
var save_service
var action_service
var settings
var persistence_enabled := false
var session_started := false
var release_input := false
var save_message := ""
var startup_error := ""
var home
var regions
var world_map
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
	regions=$Regions
	regions.initialize(self)
	world_map=$WorldMap
	for pickup in exterior.get_node("DepthSortedObjects/ForagePickups").get_children():
		pickup_nodes[pickup.name] = pickup
	hud.show_toast("低潮赶海：沿台阶下沙滩。暂不保存，重开重置。",8.0)
	var args := OS.get_cmdline_user_args()
	var old_verification: bool = get_meta("skip_verification",false)
	for arg in args:
		if arg.begins_with("--verify-") and arg not in ["--verify-journal","--verify-house"]:
			old_verification = true
	persistence_enabled = (DisplayServer.get_name() != "headless" and not old_verification) or get_meta("journal_test",false) or args.has("--verify-journal") or args.has("--verify-house")
	var options := resolve_save_options(args, get_meta("save_directory", ""), args.has("--verify-journal") or args.has("--verify-house"))
	var save_directory: String = options.directory
	startup_error = options.error
	save_service = preload("res://scripts/save_service.gd").new(save_directory)
	action_service = ActionService.new(save_service)
	settings = preload("res://scripts/settings_service.gd").new(save_service.directory)
	journal.initialize(self)
	hud.bag_requested.connect(func():
		if persistence_enabled and session_started and not hud.panel.visible and journal.mode == "" and not home.transition.busy:
			journal.selected_side = "bag"
			journal.selected_index = 0
			journal.show_page("bag"))
	if persistence_enabled or startup_error != "":
		get_tree().auto_accept_quit = false
		hud.controls.text = "WASD 移动   Shift 跑步   Tab 换工具   E 操作   B 手账   R 回路口"
		hud.show_toast("沿台阶赶海；屋内木箱可存放收获。",8)
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

# Test injection has priority; every CLI test-path argument is still validated.
static func resolve_save_options(args: PackedStringArray, injected_directory: String = "", verification: bool = false) -> Dictionary:
	var cli_directory := ""
	for arg in args:
		if arg != "--test-save-directory" and not arg.begins_with("--test-save-directory="):
			continue
		var value := arg.trim_prefix("--test-save-directory=")
		var normalized := value.simplify_path()
		if arg == "--test-save-directory" or not normalized.begins_with("/private/tmp/coastal-") or normalized == "/private/tmp/coastal-":
			return {"directory":"/private/tmp/coastal-invalid-%d" % Time.get_ticks_usec(), "error":"测试存档目录无效，已阻止开始会话。请使用 /private/tmp/coastal- 开头的目录。"}
		cli_directory = normalized
	var directory := injected_directory
	if directory == "":
		directory = cli_directory
	if directory == "":
		directory = "/private/tmp/coastal-export-journal-%d" % Time.get_ticks_usec() if verification else "user://coastal-progress"
	return {"directory":directory, "error":""}

func configure_input() -> void:
	var keys = {"left":[KEY_A,KEY_LEFT],"right":[KEY_D,KEY_RIGHT],"up":[KEY_W,KEY_UP],"down":[KEY_S,KEY_DOWN],"inspect":[KEY_E],"reset":[KEY_R],"journal":[KEY_B],"run":[KEY_SHIFT]}
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
	var locations: Array=home.interior.locations() if foraging.location=="house" else regions.active_scene().locations()
	for location in locations:
		var gap := point.distance_to(location.point)
		if gap < distance:
			distance = gap
			nearest = location
	return nearest

func nearest_pickup(point: Vector2) -> Dictionary:
	if foraging.location!="harbor" or not exterior.foraging_area.has_point(point):
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

func farm_plots() -> Array[Node2D]:
	var result: Array[Node2D] = []
	for node in sort_layer.get_children():
		if node is Node2D and node.has_method("cell_at") and node.has_method("cell_center"):
			result.append(node)
	return result

func farm_cell(id: String) -> Dictionary:
	if not foraging.life.plots.has(id): return {}
	var result := {}
	for region in farm_plots():
		var point: Vector2 = region.cell_center(id)
		if point.is_finite():
			if not result.is_empty(): return {} # Ambiguous region IDs fail closed.
			result={"id":id,"node":region,"point":point}
	return result

func farm_target(mouse: bool = false) -> Dictionary:
	if not persistence_enabled or not session_started or foraging.location!="harbor": return {}
	var direction: Vector2 = {"north":Vector2.UP,"south":Vector2.DOWN,"east":Vector2.RIGHT,"west":Vector2.LEFT}.get(player.facing,Vector2.DOWN)
	var point: Vector2 = player.global_position+direction*12
	if mouse: point=player.get_canvas_transform().affine_inverse()*$FarmTools.pointer_position
	for region in farm_plots():
		var id: String=region.cell_at(point)
		if id!="": return farm_cell(id)
	return {}

func can_reach_cell(target: Dictionary) -> bool:
	if target.is_empty() or player.global_position.distance_to(target.point)>24: return false
	var ray := PhysicsRayQueryParameters2D.create(player.global_position,target.point,1,[player.get_rid()])
	return get_world_2d().direct_space_state.intersect_ray(ray).is_empty()

func use_farm_tool(target: Dictionary) -> void:
	if target.is_empty(): return
	var tools := $FarmTools
	var args := {"cell_id":target.id}
	if tools.tool=="plant": args.crop_id=tools.crop_id
	var result := perform_action(tools.tool,args,int(foraging.life.action_seq)+1)
	if result.ok and not result.duplicate:
		if tools.tool in ["hoe","water","harvest"]: player.play_tool_action(tools.tool,target.point)
		hud.show_toast({"hoe":"已翻土", "water":"已浇水", "plant":"已播种", "harvest":"收获 +3"}[tools.tool],1.5)

func _process(_delta: float) -> void:
	if world_map!=null and world_map.visible:return
	if journal != null and journal.mode != "": return
	if home != null and home.transition.busy: return
	if player != null and player.action_busy: return
	if release_input:
		if Input.is_physical_key_pressed(KEY_ESCAPE) or Input.is_physical_key_pressed(KEY_TAB): return
		for action in ["inspect","reset","journal","left","right","up","down"]:
			if Input.is_action_pressed(action):
				return
		release_input = false
		return
	var plot_target := farm_target($FarmTools.mouse_target)
	for region in farm_plots():
		region.select_cell(plot_target.get("id","") if plot_target.get("node")==region and not hud.panel.visible else "",can_reach_cell(plot_target) and exterior.can_cultivate(plot_target.point) if not plot_target.is_empty() else false)
	if persistence_enabled and Input.is_action_just_pressed("journal") and not hud.panel.visible:
		journal.show_page(journal.last_page)
		return
	if Input.is_action_just_pressed("inspect"):
		if not regions.nearby_exit().is_empty():
			regions.travel()
			return
		if hud.panel.visible:
			hud.dismiss()
		elif persistence_enabled and foraging.location in ["harbor","house"] and home.active_door().can_interact(player.position):
			home.transition.begin()
			return
		elif persistence_enabled and player.position.distance_to(home.storage_point()) <= 28:
			journal.selected_side = "bag"
			journal.selected_index = 0
			journal.show_page("storage")
			return
		elif persistence_enabled and can_open_sleep():
			journal.show_page("sleep")
			return
		elif can_open_trade():
			journal.show_page("trade")
			return
		elif not plot_target.is_empty():
			use_farm_tool(plot_target)
			return
		else:
			var target := nearest_pickup(player.position)
			if not target.is_empty():
				if persistence_enabled:
					var result := perform_action("collect", {"pickup_id":str(target.id)}, int(foraging.life.action_seq) + 1)
					if result.ok and not result.duplicate:
						hud.show_toast(data.ITEM_NAMES[target.kind]+" +1")
				elif foraging.collect(target.id,target.kind):
					pickup_nodes[target.id].hide()
					hud.show_toast(data.ITEM_NAMES[target.kind]+" +1")
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
	if not plot_target.is_empty():
		var cell: Dictionary=foraging.life.plots[plot_target.id]
		var stage := "未开垦" if not cell.tilled else ("空土" if cell.crop_id=="" else ("生菜" if cell.crop_id=="lettuce" else "番茄"))
		if cell.crop_id!="": stage+=" %d/%d" % [cell.growth,preload("res://scripts/simulation/crop_catalog.gd").get_crop(cell.crop_id).growth_days]
		hud.prompt.text="[ E / 点击 ] %s · %s%s" % [stage,"已浇水" if cell.watered else "干燥","" if can_reach_cell(plot_target) else " · 请靠近"]
	elif not target.is_empty():
		hud.prompt.text = "[ E ] 拾取" + data.ITEM_NAMES[target.kind]
	elif persistence_enabled and foraging.location in ["harbor","house"] and home.active_door().can_interact(player.position):
		hud.prompt.text="[ E ] 走出小屋" if foraging.location=="house" else "[ E ] 进入小屋"
	elif persistence_enabled and player.position.distance_to(home.storage_point()) <= 28:
		hud.prompt.text = "[ E ] 打开旧屋储物箱"
	elif persistence_enabled and can_open_sleep():
		hud.prompt.text = "[ E ] 休息到明天"
	elif can_open_trade():
		hud.prompt.text="[ E ] 买种子 / 出售收获"
	elif not regions.nearby_exit().is_empty():
		hud.prompt.text="[ E ] "+str(regions.nearby_exit().name)
	elif foraging.location=="harbor_district":
		hud.prompt.text="港口小食铺待复业 · M 全镇地图 · 南口返回旧屋海港"
	elif foraging.location=="house" and nearest_location(player.position).is_empty():
		hud.prompt.text="回到熟悉的屋子；床、厨房和旧照片可查看。"
	elif foraging.collected.size() == exterior.pickups().size() and nearest_location(player.position).is_empty():
		hud.prompt.text = "今日赶海收获已集齐；可到鱼摊出售，或回家休息。"

func refresh_pickups() -> void:
	for id in pickup_nodes:
		pickup_nodes[id].visible = not foraging.collected.has(id)

func refresh_life_views() -> void:
	refresh_pickups()
	for plot in farm_plots():
		plot.refresh(foraging.life.plots)
	if hud != null:
		hud.update_location(nearest_location(player.position))
		hud.update_life(foraging.life)
	if journal != null:
		journal.render()

func _set_state(value) -> void:
	foraging = value
	refresh_life_views()

func perform_action(kind: String, args: Dictionary, request_id: int) -> Dictionary:
	var result: Dictionary
	if not _can_perform_action(kind, args):
		result = ActionService.failure("not_allowed")
	else:
		result = action_service.execute(foraging, home.safe_position(foraging.location, player.position), kind, args, request_id)
	if result.ok:
		if not result.duplicate:
			journal.note = ""
			_set_state(result.next_state)
	else:
		var message: String = ACTION_MESSAGES.get(result.code, "操作未完成，请重试。")
		hud.show_toast(message, 6)
		journal.note = message
		journal.render()
	return result

func _can_perform_action(kind: String, args: Dictionary) -> bool:
	if world_map.visible or not persistence_enabled or not session_started or release_input or home.transition.busy or hud.panel.visible or player.action_busy:
		return false
	if journal.pending != "" or is_instance_valid(journal.modal):
		return false
	if kind == "sleep":
		var sleep_page := journal.get_node("Root/SleepPage") as Control
		return journal.mode == "sleep" and sleep_page.is_visible_in_tree() and can_open_sleep()
	if kind in ["hoe", "plant", "water", "harvest"]:
		if journal.mode!="" or foraging.location!="harbor" or not args.get("cell_id") is String: return false
		var target := farm_cell(args.cell_id)
		return can_reach_cell(target) and exterior.can_cultivate(target.point)
	if kind == "collect":
		if journal.mode != "" or foraging.location != "harbor" or not exterior.foraging_area.has_point(player.position):
			return false
		for entry in exterior.pickups():
			if entry.id == args.get("pickup_id"):
				for known in data.pickups():
					if known.id == entry.id and known.kind == entry.kind:
						return player.position.distance_to(entry.point) <= 24
				return false
		return false
	# The visible trade page and the live market marker are both required.
	if kind != "trade" or foraging.location != "harbor" or journal.mode != "trade" or journal.pending != "":
		return false
	var page := journal.get_node_or_null("Root/TradePage") as Control
	var target := exterior.get_node_or_null("InteractPoints/market") as Node2D
	return page != null and page.is_visible_in_tree() and target != null and player.position.distance_to(player.get_parent().to_local(target.global_position)) <= 28


func can_open_sleep() -> bool:
	if not session_started or not persistence_enabled or foraging.location != "house":
		return false
	var bed := home.interior.get_node_or_null("InteractPoints/bed") as Node2D
	return bed != null and player.position.distance_to(player.get_parent().to_local(bed.global_position)) <= 28

func can_open_trade() -> bool:
	if not persistence_enabled or not session_started or foraging.location!="harbor":return false
	var point:=exterior.get_node_or_null("InteractPoints/market") as Node2D
	return point!=null and player.global_position.distance_to(point.global_position)<=28

func show_daily_summary() -> void:
	journal.show_page("daily")

func start_new_game(chosen_name: String) -> bool:
	if startup_error != "": return false
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
	hud.show_toast("欢迎回来，"+foraging.player_name+"。1–4 选工具，点菜格或 E 使用；靠近门前菜地开始翻土。",8)
	return true

func continue_game() -> bool:
	if startup_error != "": return false
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
