extends CanvasLayer

const Reports=preload("res://scripts/simulation/report_builder.gd")
const Crops = preload("res://scripts/simulation/crop_catalog.gd")
const Catalog = preload("res://scripts/inventory/item_catalog.gd")
const Art = preload("res://scripts/atlas.gd")

@export_multiline var title_status_template := "{status}\n\n单人生活原型\n自动保存 / 单存档槽\n可在旧屋床边休息换日；可照料菜畦；可在鱼摊买种、出售收获；日记记录每天的收支"
@export_multiline var profile_template := "{name}\n居住地：临海旧屋\n\n累计采集：{total} 个\n发现海产：{discovered} / 3 种"
@export_multiline var save_failure_template := "{message}\n请选择重试或返回，不会自动退出。"

var world
var mode := ""
var last_page := "bag"
var from_title := false
var root: Control
var surface: Panel
var modal: Control
var modal_kind := ""
var quantity: SpinBox
var quantity_action := Callable()
var confirm_action := Callable()
var save_error_exit_game := false
var selected_side := "bag"
var selected_index := 0
var pending := ""
var pending_source := -1
var pending_amount := 0
var category := ""
var slots_count := 0
var profile_text := ""
var theme: Theme
var catalog := Catalog.new()
var note := ""
var main_menu: Control
var pause_menu: Control
var storage_page: Control
var bag_page: Control
var profile_page: Control
var settings_page: Control
var sleep_page: Control
var sleep_request_id := 0
var sleep_expected_day := 0
var sleep_submitting := false
var sleep_wait_release := false
var sleep_title_template := ""
var sleep_body_template := ""
var modal_return_focus: Control
var dialogs: Control

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	root = $Root
	main_menu = $Root/MainMenu
	pause_menu = $Root/PauseMenu
	storage_page = $Root/StoragePage
	bag_page = $Root/PauseMenu/Surface/BagPage
	profile_page = $Root/PauseMenu/Surface/ProfilePage
	settings_page = $Root/PauseMenu/Surface/SettingsPage
	sleep_page = $Root/SleepPage
	sleep_title_template = $Root/SleepPage/Surface/Title.text
	sleep_body_template = $Root/SleepPage/Surface/Body.text
	dialogs = $Root/Dialogs
	theme = root.theme
	quantity = $Root/Dialogs/QuantityDialog/Panel/quantity
	quantity.get_line_edit().focus_mode = Control.FOCUS_NONE
	quantity.get_line_edit().editable = false
	_bind_controls()

func initialize(owner_world) -> void:
	world = owner_world

func _bind_controls() -> void:
	$Root/SleepPage/Surface/Confirm.pressed.connect(confirm_sleep)
	$Root/SleepPage/Surface/Cancel.pressed.connect(close_menu)
	$Root/DailyPage/Surface/Close.pressed.connect(close_menu)
	$Root/PauseMenu/Surface/Tabs/tab_daily.pressed.connect(show_page.bind("daily"))
	$Root/MainMenu/Surface/continue.pressed.connect(_continue_game)
	$Root/MainMenu/Surface/new_game.pressed.connect(new_game_dialog)
	$Root/MainMenu/Surface/settings.pressed.connect(show_page.bind("settings"))
	$Root/MainMenu/Surface/quit.pressed.connect(_request_exit)
	$Root/PauseMenu/Surface/Tabs/tab_bag.pressed.connect(show_page.bind("bag"))
	$Root/PauseMenu/Surface/Tabs/tab_profile.pressed.connect(show_page.bind("profile"))
	$Root/PauseMenu/Surface/Tabs/tab_settings.pressed.connect(show_page.bind("settings"))
	$Root/PauseMenu/Surface/close.pressed.connect(_close_pause_menu)
	$Root/StoragePage/Surface/close.pressed.connect(close_menu)
	var cats := ["", "seafood", "ingredients", "materials", "tools"]
	for i in range(cats.size()):
		bag_page.get_node("Filter/filter_" + str(i)).pressed.connect(_set_category.bind(cats[i]))
	bag_page.get_node("Details/move").pressed.connect(_start_move)
	bag_page.get_node("Details/split").pressed.connect(action_split)
	bag_page.get_node("Details/discard").pressed.connect(action_discard)
	bag_page.get_node("sort").pressed.connect(_sort_bag)
	bag_page.get_node("return_item").pressed.connect(_return_to_item)
	_bind_slot_grid(bag_page.get_node("BagGrid"), "bag")
	_bind_slot_grid(storage_page.get_node("Surface/BagGrid"), "bag")
	_bind_slot_grid(storage_page.get_node("Surface/ChestScroll/ChestGrid"), "chest")
	storage_page.get_node("Surface/transfer").pressed.connect(action_transfer)
	storage_page.get_node("Surface/deposit").pressed.connect(_deposit_matching)
	storage_page.get_node("Surface/sort_bag").pressed.connect(_sort_bag)
	storage_page.get_node("Surface/sort_chest").pressed.connect(_sort_chest)
	for bus in ["Master", "Music", "SFX"]:
		settings_page.get_node(bus).value_changed.connect(_setting_changed.bind(bus))
	settings_page.get_node("fullscreen").pressed.connect(_toggle_fullscreen)
	settings_page.get_node("save_title").pressed.connect(_return_to_title)
	settings_page.get_node("save_quit").pressed.connect(_request_exit)
	$Root/Dialogs/NameDialog/Panel/cancel.pressed.connect(cancel_modal)
	$Root/Dialogs/NameDialog/Panel/start.pressed.connect(_accept_name)
	$Root/Dialogs/QuantityDialog/Panel/less.pressed.connect(_quantity_less)
	$Root/Dialogs/QuantityDialog/Panel/more.pressed.connect(_quantity_more)
	$Root/Dialogs/QuantityDialog/Panel/cancel.pressed.connect(cancel_modal)
	$Root/Dialogs/QuantityDialog/Panel/quantity_ok.pressed.connect(accept_quantity)
	$Root/Dialogs/ConfirmDialog/Panel/cancel.pressed.connect(cancel_modal)
	$Root/Dialogs/ConfirmDialog/Panel/confirm.pressed.connect(_accept_confirm)
	$Root/Dialogs/SaveErrorDialog/Panel/cancel.pressed.connect(_return_from_save_error)
	$Root/Dialogs/SaveErrorDialog/Panel/retry.pressed.connect(_retry_save)
	$Root/Dialogs/SaveErrorDialog/Panel/leave.pressed.connect(_leave_without_save)

func _bind_slot_grid(grid: Control, side: String) -> void:
	var buttons: Array[Node] = grid.find_children(side + "_*", "Button", false, false)
	for i in range(buttons.size()):
		(buttons[i] as Button).pressed.connect(select_slot.bind(side, i))

func _continue_game() -> void:
	if world != null:
		world.continue_game()

func _request_exit() -> void:
	if world != null:
		world.request_exit()

func _return_to_title() -> void:
	if world != null:
		world.return_to_title()

func _toggle_fullscreen() -> void:
	get_window().mode = Window.MODE_WINDOWED if get_window().mode == Window.MODE_FULLSCREEN else Window.MODE_FULLSCREEN

func _setting_changed(value: float, bus: String) -> void:
	if world != null and not world.settings.set_volume(bus, value):
		note = "设置保存失败，本次运行已应用。"
		_refresh_notes()

func _set_category(value: String) -> void:
	category = value
	selected_side = "bag"
	if category!="" and world!=null:
		var slots:Array=world.foraging.bag.snapshot()
		var chosen:int=-1
		for i in range(slots.size()):
			if slots[i].id!="" and catalog.get_item(slots[i].id).category==category:
				chosen=i;break
		if chosen<0:
			for i in range(slots.size()):
				if slots[i].id=="":chosen=i;break
		if chosen>=0:selected_index=chosen
	render()

func _return_to_item() -> void:
	if pending != "":
		selected_index = pending_source
		pending = ""
	render()
	bag_page.get_node("BagGrid").get_child(selected_index).grab_focus()

func _bag_actions() -> Array:
	return [bag_page.get_node("Details/move"),bag_page.get_node("Details/split"),bag_page.get_node("Details/discard"),bag_page.get_node("return_item"),bag_page.get_node("sort")]

func _in_bag_actions(focus: Control) -> bool:
	return focus in _bag_actions()

func _tab_bag(reverse: bool) -> void:
	if pending != "": return
	var focus = get_viewport().gui_get_focus_owner()
	var groups = [bag_page.get_node("BagGrid").get_children(),_bag_actions(),pause_menu.get_node("Surface/Tabs").get_children(),bag_page.get_node("Filter").get_children()]
	var current = 0
	for i in range(groups.size()):
		if focus in groups[i]:current=i
	for step in range(1,5):
		var next = posmod(current + step * (-1 if reverse else 1),4)
		if next == 0:
			_return_to_item()
			return
		for button in groups[next]:
			if KeyboardNavigation.eligible(button):
				button.grab_focus()
				return

func _start_move() -> void:
	pending = "move"
	pending_source = selected_index
	render()
	if mode=="bag":bag_page.get_node("BagGrid").get_child(selected_index).grab_focus()

func _sort_bag() -> void:
	if world == null:
		return
	world.foraging.bag.organize()
	render()

func _sort_chest() -> void:
	if world == null:
		return
	world.foraging.chest.organize()
	render()

func _deposit_matching() -> void:
	if world == null:
		return
	var count: int = world.foraging.bag.deposit_matching(world.foraging.chest)
	note = "已存入 %d 个。未接收物品保留在背包。" % count
	world.save_progress()
	render()

func show_page(page: String) -> void:
	if world == null:
		return
	if mode == "title":
		from_title = true
	elif page != "settings":
		from_title = false
	if page == "sleep" and mode != "sleep":
		sleep_request_id = 0
		sleep_expected_day = 0
		sleep_wait_release = Input.is_action_pressed("inspect")
		note = ""
	if page=="trade" and mode!="trade": $Root/TradePage.open()
	mode = page
	if page in ["bag", "profile", "settings"] and not from_title:
		last_page = page
	pending = ""
	get_tree().paused = true
	if is_instance_valid(world.player):
		world.player.velocity = Vector2.ZERO
		world.player.sprite.stop()
	render()

func render() -> void:
	if world == null or mode == "":
		return
	root.visible = true
	main_menu.visible = mode == "title"
	pause_menu.visible = mode in ["bag", "profile", "settings"]
	storage_page.visible = mode == "storage"
	sleep_page.visible = mode == "sleep"
	$Root/TradePage.visible=mode=="trade"
	$Root/DailyPage.visible=mode=="daily"
	bag_page.visible = mode == "bag"
	profile_page.visible = mode == "profile"
	settings_page.visible = mode == "settings"
	$Root/PauseMenu/Surface/BagBody.visible = mode == "bag"
	$Root/PauseMenu/Surface/DetailsBody.visible = mode == "bag"
	$Root/PauseMenu/Surface/WideBody.visible = mode in ["profile", "settings"]
	slots_count = 0
	if mode == "title":
		surface = $Root/MainMenu/Surface
		_refresh_title()
	elif mode=="trade":
		surface=$Root/TradePage/Surface
		$Root/TradePage.render()
	elif mode=="daily":
		surface=$Root/DailyPage/Surface
		var report:Dictionary=Reports.daily(world.foraging.to_data(world.player.position))
		$Root/DailyPage/Surface/Title.text="生活日记 · 尚未休息" if report.day_id==0 else "第%d日 日记 · 今天第%d日"%[report.day_id,report.current_day]
		$Root/DailyPage/Surface/Body.text="\n".join(report.lines)
	elif mode == "sleep":
		surface = $Root/SleepPage/Surface
		_refresh_sleep()
	elif mode == "storage":
		surface = $Root/StoragePage/Surface
		_refresh_storage()
	else:
		surface = $Root/PauseMenu/Surface
		_refresh_tabs()
		match mode:
			"bag":
				_refresh_bag()
			"profile":
				_refresh_profile()
			"settings":
				_refresh_settings()
	_refresh_notes()
	var focus := get_viewport().gui_get_focus_owner()
	if focus is Control and not focus.is_visible_in_tree():
		focus.release_focus()
	call_deferred("_focus_default")

func _refresh_sleep() -> void:
	$Root/SleepPage/Surface/Title.text = sleep_title_template.format({"day": int(world.foraging.life.day_id)})
	$Root/SleepPage/Surface/Body.text = sleep_body_template
	if note != "":
		$Root/SleepPage/Surface/Body.text += "\n" + note
	$Root/SleepPage/Surface/Confirm.disabled = sleep_submitting
	$Root/SleepPage/Surface/Cancel.disabled = sleep_submitting

func confirm_sleep() -> void:
	if mode != "sleep" or sleep_submitting or sleep_wait_release:
		return
	if sleep_request_id == 0:
		sleep_request_id = int(world.foraging.life.action_seq) + 1
		sleep_expected_day = int(world.foraging.life.day_id)
	sleep_submitting = true
	_refresh_sleep()
	var result: Dictionary = world.perform_action("sleep", {"expected_day":sleep_expected_day}, sleep_request_id)
	sleep_submitting = false
	if result.ok:
		dismiss()
		world.show_daily_summary()
	else:
		_refresh_sleep()

func _refresh_title() -> void:
	var status: Dictionary = world.save_service.read_save()
	if world.startup_error != "":
		status.message = world.startup_error
	$Root/MainMenu/Surface/continue.disabled = not status.ok or world.startup_error != ""
	$Root/MainMenu/Surface/new_game.disabled = status.get("future", false) or world.startup_error != ""
	$Root/MainMenu/Surface/Status.text = title_status_template.format({"status": status.message})
	_update_portrait($Root/MainMenu/Surface/Portrait)

func _refresh_tabs() -> void:
	$Root/PauseMenu/Surface/Tabs/tab_bag.visible = not from_title
	$Root/PauseMenu/Surface/Tabs/tab_profile.visible = not from_title
	$Root/PauseMenu/Surface/Tabs/tab_settings.visible = true
	$Root/PauseMenu/Surface/Tabs/tab_daily.visible=not from_title
	for page_name in ["bag", "profile", "settings"]:
		var button := pause_menu.get_node("Surface/Tabs/tab_" + page_name) as Button
		button.button_pressed = page_name == mode

func _refresh_notes() -> void:
	for path in ["Root/MainMenu/Surface", "Root/PauseMenu/Surface", "Root/StoragePage/Surface"]:
		var owner := get_node(path)
		owner.get_node("Note").visible = note == ""
		owner.get_node("DynamicNote").visible = note != ""
		if note != "":
			owner.get_node("DynamicNote").text = note

func _update_portrait(portrait: TextureRect) -> void:
	portrait.texture = Art.player_frames().get_frame_texture("south", 0)

func container(side: String):
	if world == null:
		return null
	return world.foraging.bag if side == "bag" else world.foraging.chest

func _refresh_slots(grid: Control, side: String) -> void:
	var inventory = container(side)
	if inventory == null:
		return
	var snapshot: Array = inventory.snapshot()
	var buttons: Array[Node] = grid.find_children(side + "_*", "Button", false, false)
	for i in range(buttons.size()):
		var button := buttons[i] as Button
		var slot: Dictionary = snapshot[i]
		var icon := button.get_node("Icon") as Control
		var amount := button.get_node("Amount") as Label
		var occupied: bool = slot.id != ""
		button.tooltip_text = "空格"
		button.disabled = false
		button.modulate.a = 1.0
		button.button_pressed = selected_side == side and selected_index == i
		icon.visible = occupied
		if not occupied: icon.item_id = ""
		amount.visible = occupied
		if occupied:
			var item: Dictionary = catalog.get_item(slot.id)
			icon.item_id = slot.id
			amount.text = str(slot.amount)
			button.tooltip_text = item.name + " ×" + str(slot.amount)
			if category != "" and mode == "bag" and item.category != category:
				button.modulate.a = 0.32
				button.disabled = true
		slots_count += 1

func _refresh_bag() -> void:
	selected_side = "bag"
	_refresh_slots(bag_page.get_node("BagGrid"), "bag")
	_refresh_details()

func _selected_slot() -> Dictionary:
	var inventory = container(selected_side)
	if inventory == null:
		return {"id": "", "amount": 0}
	var snapshot: Array = inventory.snapshot()
	if selected_index < 0 or selected_index >= snapshot.size():
		selected_index = 0
	return snapshot[selected_index]

func _refresh_details() -> void:
	var slot := _selected_slot()
	var title := "选择一个格子"
	var description := "选中物品可查看用途和操作。\n\n整理不会改变物品总数。"
	if slot.id != "":
		var item: Dictionary = catalog.get_item(slot.id)
		title = item.name + "  ×" + str(slot.amount)
		var source := "赶海收获"
		if slot.id.ends_with("_seed"):
			source = "市场种子"
		elif item.category == "ingredients":
			source = "种植收获"
		description = ("海产" if item.category == "seafood" else "食材") + " / " + source + "\n" + item.description + "\n用途：可在鱼摊出售；料理将在后续开放。\n当前不可直接使用。"
	var details := bag_page.get_node("Details")
	details.get_node("Title").text = title
	details.get_node("Description").text = description
	details.get_node("Pending").visible = pending != ""
	details.get_node("Pending").text = "请选择目标空格（B 取消）" if pending == "split" else "请选择目标格（B 取消）"
	details.get_node("move").visible = pending == "" and slot.id != ""
	details.get_node("split").visible = pending == "" and slot.id != ""
	details.get_node("discard").visible = pending == "" and slot.id != ""
	details.get_node("split").disabled = slot.amount < 2

func select_slot(side: String, index: int) -> void:
	if world == null:
		return
	if pending != "" and side == selected_side:
		var ok: bool = container(side).split_stack(pending_source, index, pending_amount) if pending == "split" else container(side).move_slot(pending_source, index)
		note = "已调整物品位置。" if ok else "目标不适用，物品未改变。"
		pending = ""
	selected_side = side
	selected_index = index
	render()
	if mode=="bag":
		var button=bag_page.get_node("BagGrid").get_child(index)
		if not button.disabled:button.grab_focus()

func action_split() -> void:
	var slot := _selected_slot()
	if slot.amount < 2:
		return
	choose_quantity("拆分数量", int(slot.amount) - 1, func(amount):
		pending = "split"
		pending_source = selected_index
		pending_amount = amount
		render()
		if mode=="bag":bag_page.get_node("BagGrid").get_child(selected_index).grab_focus())

func action_discard() -> void:
	var slot := _selected_slot()
	if slot.id == "":
		return
	var side := selected_side
	var index := selected_index
	choose_quantity("丢弃数量", int(slot.amount), func(amount):
		confirm("丢弃 %s ×%d？\n物品将永久移除，无法恢复。" % [catalog.get_item(slot.id).name, amount], func():
			container(side).discard(index, amount, true)
			world.save_progress()
			render()))

func _refresh_storage() -> void:
	_refresh_slots(storage_page.get_node("Surface/BagGrid"), "bag")
	_refresh_slots(storage_page.get_node("Surface/ChestScroll/ChestGrid"), "chest")
	var slot := _selected_slot()
	$Root/StoragePage/Surface/Selection.text = ("背包" if selected_side == "bag" else "仓储") + " / " + ("空格" if slot.id == "" else catalog.get_item(slot.id).name + " ×" + str(slot.amount))
	$Root/StoragePage/Surface/transfer.text = "存入 →" if selected_side == "bag" else "← 取出"
	$Root/StoragePage/Surface/transfer.disabled = slot.id == ""

func action_transfer() -> void:
	var side := selected_side
	var index := selected_index
	var slot := _selected_slot()
	if slot.id == "":
		return
	choose_quantity("存入数量" if side == "bag" else "取出数量", int(slot.amount), func(amount):
		var moved: int = container(side).transfer_to(container("chest" if side == "bag" else "bag"), index, amount)
		note = "已转移 %d 个；剩余物品保留原处。" % moved
		world.save_progress()
		render())

func _refresh_profile() -> void:
	_update_portrait($Root/PauseMenu/Surface/ProfilePage/Portrait)
	profile_text = profile_template.format({"name": world.foraging.player_name, "total": world.foraging.total_collected, "discovered": world.foraging.discovered.size()})
	$Root/PauseMenu/Surface/ProfilePage/ProfileText.text = profile_text

func _refresh_settings() -> void:
	for bus in ["Master", "Music", "SFX"]:
		(settings_page.get_node(bus) as HSlider).set_value_no_signal(world.settings.volumes[bus])
	settings_page.get_node("save_title").visible = not from_title
	settings_page.get_node("save_quit").visible = not from_title

func new_game_dialog() -> void:
	if world == null:
		return
	_show_modal($Root/Dialogs/NameDialog, "name")
	$Root/Dialogs/NameDialog/Panel/player_name.text = "归乡人"
	$Root/Dialogs/NameDialog/Panel/cancel.grab_focus()

func _accept_name() -> void:
	var chosen: String = $Root/Dialogs/NameDialog/Panel/player_name.text
	cancel_modal()
	if world.save_service.has_files():
		confirm("新游戏将替换当前进度。\n确认从头开始？", world.start_new_game.bind(chosen))
	else:
		world.start_new_game(chosen)

func choose_quantity(title: String, maximum: int, action: Callable) -> void:
	quantity_action = action
	$Root/Dialogs/QuantityDialog/Panel/Title.text = title
	quantity.max_value = maximum
	quantity.value = maximum
	_show_modal($Root/Dialogs/QuantityDialog, "quantity")
	$Root/Dialogs/QuantityDialog/Panel/cancel.grab_focus()

func _quantity_less() -> void:
	quantity.value -= 1

func _quantity_more() -> void:
	quantity.value += 1

func accept_quantity() -> void:
	if modal_kind != "quantity":
		return
	var value := int(quantity.value)
	var action := quantity_action
	cancel_modal()
	if action.is_valid():
		action.call(value)

func confirm(text: String, action: Callable) -> void:
	confirm_action = action
	$Root/Dialogs/ConfirmDialog/Panel/Title.text = text
	_show_modal($Root/Dialogs/ConfirmDialog, "confirm")
	$Root/Dialogs/ConfirmDialog/Panel/cancel.grab_focus()

func _accept_confirm() -> void:
	if modal_kind != "confirm":
		return
	var action := confirm_action
	cancel_modal()
	if action.is_valid():
		action.call()

func _show_modal(dialog: Control, kind: String) -> void:
	var previous = get_viewport().gui_get_focus_owner()
	if previous!=null and not dialogs.is_ancestor_of(previous):modal_return_focus=previous
	for child in dialogs.get_children():
		(child as Control).visible = false
	modal = dialog
	modal_kind = kind
	dialog.visible = true
	dialogs.mouse_filter = Control.MOUSE_FILTER_STOP

func cancel_modal() -> void:
	if is_instance_valid(modal):
		modal.visible = false
	modal = null
	modal_kind = ""
	quantity_action = Callable()
	confirm_action = Callable()
	dialogs.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if is_instance_valid(modal_return_focus) and KeyboardNavigation.eligible(modal_return_focus):
		modal_return_focus.grab_focus()
	call_deferred("_focus_default")

func _close_pause_menu() -> void:
	if is_instance_valid(modal):
		cancel_modal()
		return
	world.save_progress()
	dismiss()

func close_menu() -> void:
	if mode=="trade":
		if is_instance_valid(modal):cancel_modal()
		else:$Root/TradePage.back()
		return
	if mode == "sleep":
		if not sleep_submitting: dismiss()
		return
	if is_instance_valid(modal):
		cancel_modal()
		return
	if mode=="bag" and (pending!="" or _in_bag_actions(get_viewport().gui_get_focus_owner())):
		_return_to_item()
		return
	if pending != "":
		pending = ""
		render()
		return
	if mode == "title":
		return
	if from_title:
		from_title = false
		show_page("title")
		return
	world.save_progress()
	dismiss()

func dismiss() -> void:
	mode = ""
	note = ""
	pending = ""
	from_title = false
	cancel_modal()
	root.visible = false
	main_menu.visible = false
	pause_menu.visible = false
	storage_page.visible = false
	sleep_page.visible = false
	$Root/TradePage.hide()
	$Root/DailyPage.hide()
	get_tree().paused = false
	if world != null:
		world.release_input = true

const KeyboardNavigation=preload("res://scripts/ui/keyboard_navigation.gd")
const NAV_KEYS={KEY_LEFT:Vector2i.LEFT,KEY_A:Vector2i.LEFT,KEY_RIGHT:Vector2i.RIGHT,KEY_D:Vector2i.RIGHT,KEY_UP:Vector2i.UP,KEY_W:Vector2i.UP,KEY_DOWN:Vector2i.DOWN,KEY_S:Vector2i.DOWN}

func _focus_default() -> void:
	if not is_inside_tree() or mode == "" or is_instance_valid(modal):
		return
		return
	if mode=="trade":
		if $Root/TradePage.submitting:return
		var current:=get_viewport().gui_get_focus_owner()
		if current!=null and $Root/TradePage.is_ancestor_of(current) and KeyboardNavigation.eligible(current):return
		var page=$Root/TradePage
		var ids=page.BUY if page.direction=="buy" else page.SELL
		page.get_node("Surface/Items").get_child(maxi(0,ids.find(page.item_id))).grab_focus()
		return
	if mode=="daily":
		$Root/DailyPage/Surface/Close.grab_focus()
		return
	if mode == "sleep":
		$Root/SleepPage/Surface/Cancel.grab_focus()
		return
	var focus := get_viewport().gui_get_focus_owner()
	if focus!=null and KeyboardNavigation.eligible(focus):
		return
	if surface == null:
		return
	if mode=="bag":
		var button=bag_page.get_node("BagGrid").get_child(selected_index)
		if not button.disabled:
			button.grab_focus()
			return
	for node in surface.find_children("*", "Button", true, false):
		var button := node as Button
		if button.is_visible_in_tree() and not button.disabled:
			button.grab_focus()
			return

func _move_bag_cursor(direction: Vector2i) -> bool:
	var grid := bag_page.get_node("BagGrid")
	var cell := Vector2i(selected_index % 6,selected_index / 6)+direction
	while cell.x>=0 and cell.x<6 and cell.y>=0 and cell.y<4:
		var index := cell.y*6+cell.x
		var button := grid.get_child(index) as Button
		if not button.disabled:
			# Moving the cursor only previews; select_slot would commit a pending move.
			selected_side="bag"
			selected_index=index
			render()
			button.grab_focus()
			return true
		cell+=direction
	return false

func _focus_navigation_target(target:Control) -> void:
	if target==null:return
	if mode=="bag" and bag_page.get_node("BagGrid").is_ancestor_of(target):
		selected_side="bag"
		selected_index=target.get_index()
		render()
	elif mode=="trade" and $Root/TradePage/Surface/Items.is_ancestor_of(target):
		$Root/TradePage.select_slot(target.get_index())
	target.grab_focus()

func _navigate_menu(direction:Vector2i) -> void:
	var focus:=get_viewport().gui_get_focus_owner()
	var scope:Node=modal if is_instance_valid(modal) else surface
	if scope==null:return
	if focus is Slider and direction.x!=0:
		focus.value+=direction.x*focus.step
		return
	if mode=="bag" and not is_instance_valid(modal):
		if focus!=null and bag_page.get_node("BagGrid").is_ancestor_of(focus):
			if _move_bag_cursor(direction):return
			if pending!="":return
		if direction==Vector2i.LEFT and focus in [bag_page.get_node("Details/move"),bag_page.get_node("Details/discard")]:
			_return_to_item()
			return
		# Keep vertical action navigation in its column, rather than jumping into the grid.
		var actions=bag_page.get_node("Details")
		var target:Control=null
		if direction.y>0:
			if focus==actions.get_node("move"):target=actions.get_node("discard")
			elif focus in [actions.get_node("split"),actions.get_node("discard")]:target=bag_page.get_node("sort")
		elif direction.y<0 and focus==bag_page.get_node("sort"):
			target=actions.get_node("discard")
		if target!=null and KeyboardNavigation.eligible(target):
			_focus_navigation_target(target)
			return
		# From the last filter, right enters actions without changing the selected item.
		if direction==Vector2i.RIGHT and focus==bag_page.get_node("Filter/filter_4"):
			for path in ["Details/move","Details/split","Details/discard","sort"]:
				var button=bag_page.get_node(path)
				if KeyboardNavigation.eligible(button):
					_focus_navigation_target(button)
					return
	if mode=="trade" and not is_instance_valid(modal):
		var page=$Root/TradePage
		var grid=page.get_node("Surface/Items")
		var ids=page.BUY if page.direction=="buy" else page.SELL
		var item=grid.get_child(maxi(0,ids.find(page.item_id)))
		if focus!=null and grid.is_ancestor_of(focus):
			if direction.x!=0:
				var index:int=focus.get_index()+direction.x
				if index>=0 and index<ids.size():_focus_navigation_target(grid.get_child(index))
			elif direction.y<0:
				_focus_navigation_target(page.get_node("Surface/BuyTab" if page.direction=="buy" else "Surface/SellTab"))
			else:
				var plus=page.get_node("Surface/Plus")
				_focus_navigation_target(plus if KeyboardNavigation.eligible(plus) else page.get_node("Surface/Minus"))
			return
		if direction.y>0 and focus in [page.get_node("Surface/BuyTab"),page.get_node("Surface/SellTab")]:
			_focus_navigation_target(item)
			return
		if direction.y<0 and focus in [page.get_node("Surface/Plus"),page.get_node("Surface/Minus"),page.get_node("Surface/Submit"),page.get_node("Surface/Info")]:
			_focus_navigation_target(item)
			return
	_focus_navigation_target(KeyboardNavigation.next(scope,focus,direction))

func _input(event: InputEvent) -> void:
	if mode == "" or not event is InputEventKey or not event.pressed:
		return
	var key: int = event.physical_keycode if event.physical_keycode != 0 else event.keycode
	if event.echo and key not in NAV_KEYS:return
	var focus := get_viewport().gui_get_focus_owner()
	if focus is LineEdit and not focus.get_parent() is SpinBox and key not in [KEY_TAB, KEY_ESCAPE]:
		return
	if key == KEY_TAB and mode=="trade" and not is_instance_valid(modal):
		get_viewport().set_input_as_handled()
		$Root/TradePage.cycle_region(event.shift_pressed)
	elif key == KEY_TAB and mode in ["bag","profile","settings"] and not is_instance_valid(modal):
		get_viewport().set_input_as_handled()
		_tab_bag(event.shift_pressed)
	elif key in [KEY_B, KEY_TAB, KEY_ESCAPE]:
		get_viewport().set_input_as_handled()
		close_menu()
	elif key in NAV_KEYS:
		get_viewport().set_input_as_handled()
		_navigate_menu(NAV_KEYS[key])
	elif key == KEY_E:
		if mode == "sleep" and sleep_wait_release:
			get_viewport().set_input_as_handled()
			return
		get_viewport().set_input_as_handled()
		if mode=="bag" and not is_instance_valid(modal) and pending=="" and focus!=null and bag_page.get_node("BagGrid").is_ancestor_of(focus):
			if _selected_slot().id!="":bag_page.get_node("Details/move").grab_focus()
		elif mode=="trade" and not is_instance_valid(modal) and focus!=null and $Root/TradePage/Surface/Items.is_ancestor_of(focus):
			$Root/TradePage.enter_actions()
		elif focus is Button and not focus.disabled:
			focus.pressed.emit()

func _process(_delta: float) -> void:
	if mode=="bag" and pause_menu.get_node("Surface/Note").text.begins_with("WASD / 方向键"):
		var hint="WASD / 方向键选择 · E 物品操作 · Tab 切区 · Esc / B 关闭"
		if is_instance_valid(modal):hint="WASD / 方向键选择 · E 确认 · Esc / B 取消"
		elif pending!="":hint="WASD / 方向键选目标 · E 放置 · Esc / B 取消"
		elif _in_bag_actions(get_viewport().gui_get_focus_owner()):hint="WASD / 方向键选择 · E 确认 · Esc / B 返回物品"
		pause_menu.get_node("Surface/Note").text=hint
	if mode == "sleep" and not Input.is_action_pressed("inspect"):
		sleep_wait_release = false
	if is_instance_valid(modal):
		var focus := get_viewport().gui_get_focus_owner()
		if focus == null or not modal.is_ancestor_of(focus):
			var cancel = modal.find_child("cancel", true, false)
			if cancel is Button:
				cancel.grab_focus()

func show_save_failure(message: String, exit_game: bool) -> void:
	save_error_exit_game = exit_game
	$Root/Dialogs/SaveErrorDialog/Panel/Title.text = save_failure_template.format({"message": message})
	_show_modal($Root/Dialogs/SaveErrorDialog, "save_error")
	$Root/Dialogs/SaveErrorDialog/Panel/cancel.grab_focus()

func _return_from_save_error() -> void:
	cancel_modal()
	dismiss()

func _retry_save() -> void:
	var exit_game := save_error_exit_game
	cancel_modal()
	if exit_game:
		world.request_exit()
	else:
		world.return_to_title()

func _leave_without_save() -> void:
	var exit_game := save_error_exit_game
	confirm("未保存的操作将丢失。\n仍然离开？", func():
		if exit_game:
			get_tree().quit()
		else:
			world.session_started = false
			show_page("title"))
