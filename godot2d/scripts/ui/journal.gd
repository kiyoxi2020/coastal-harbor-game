extends CanvasLayer

const Catalog = preload("res://scripts/inventory/item_catalog.gd")
const Art = preload("res://scripts/atlas.gd")
const PixelSkin = preload("res://scripts/ui/pixel_style.gd")
var world
var mode := ""
var last_page := "bag"
var from_title := false
var root: Control
var surface: Panel
var modal: Control
var modal_kind := ""
var quantity: SpinBox
var quantity_action: Callable
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

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	layer = 20
	theme = Theme.new()
	theme.default_font = load("res://assets/NotoSansCJKsc-Regular.otf")
	theme.default_font_size = 24
	theme.set_color("font_uneditable_color","LineEdit",Color("264e55"))
	for type in ["Label", "Button", "LineEdit", "CheckButton", "SpinBox"]:
		theme.set_color("font_color",type,Color("264e55"))
	for state in ["normal","hover","pressed","focus","disabled"]:
		var box = PixelSkin.new({"normal":"button","hover":"hover","pressed":"active","focus":"focus","disabled":"button"}[state])
		theme.set_stylebox(state,"Button",box)
		theme.set_color("font_"+state+"_color","Button",Color("264e55"))
	for state in ["normal","focus","read_only"]:
		var input_box := StyleBoxFlat.new()
		input_box.bg_color = Color("fff7e5")
		input_box.border_color = Color("4b7c7c")
		input_box.set_border_width_all(2)
		input_box.set_content_margin_all(8)
		theme.set_stylebox(state,"LineEdit",input_box)

func _button(parent: Control, text: String, rect: Rect2, action: Callable, id: String = "") -> Button:
	var button := Button.new()
	button.text = text
	button.position = rect.position
	button.size = rect.size
	if id.begins_with("tab_"):
		button.add_theme_stylebox_override("normal",PixelSkin.new("active" if id == "tab_"+mode else "paper"))
	elif id in ["move","transfer","continue"]:
		button.add_theme_stylebox_override("normal",PixelSkin.new("teal"))
	if id != "":
		button.name = id
	button.pressed.connect(action)
	parent.add_child(button)
	return button

func _label(parent: Control, text: String, rect: Rect2, font_size: int = 24) -> Label:
	var label := Label.new()
	label.text = text
	label.position = rect.position
	label.size = rect.size
	label.add_theme_font_size_override("font_size",font_size)
	if parent == surface and rect.position.y >= 575:
		label.add_theme_color_override("font_color",Color("f5e8c7"))
	elif parent == surface and rect.position.y >= 60 and rect.position.y < 120:
		label.add_theme_color_override("font_color",Color("f5e8c7"))
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	parent.add_child(label)
	return label

func _panel(parent: Control, rect: Rect2) -> Panel:
	var panel := Panel.new()
	panel.position = rect.position
	panel.size = rect.size
	var box = PixelSkin.new("paper")
	panel.add_theme_stylebox_override("panel",box)
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(panel)
	return panel

func show_page(page: String) -> void:
	if mode == "title":
		from_title = true
	elif page != "settings":
		from_title = false
	mode = page
	if page in ["bag","profile","settings"] and not from_title:
		last_page = page
	pending = ""
	get_tree().paused = true
	world.player.velocity = Vector2.ZERO
	world.player.sprite.stop()
	render()

func render() -> void:
	var focus_name := ""
	if is_instance_valid(root):
		var focus := get_viewport().gui_get_focus_owner()
		if focus != null:
			focus_name = str(focus.name)
		remove_child(root)
		root.queue_free()
	modal = null
	root = Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.theme = theme
	add_child(root)
	var shade := ColorRect.new()
	shade.color = Color(0.07,0.18,0.21,0.76)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(shade)
	surface = _panel(root, Rect2(80,48,1120,624))
	surface.add_theme_stylebox_override("panel",PixelSkin.new("canvas"))
	_panel(surface,Rect2(16,8,730,58))
	if mode == "bag":
		_panel(surface,Rect2(16,122,608,444))
		_panel(surface,Rect2(636,122,468,444))
	else:
		_panel(surface,Rect2(16,122,1088,444))
	_label(surface,"海边生活手账  ≋",Rect2(46,16,660,42),30)
	_label(surface,note if note != "" else "方向键选择 · E 确认 · B / Tab 返回",Rect2(28,575,1050,40),22)
	slots_count = 0
	if mode == "title":
		_title()
	elif mode == "storage":
		_storage()
	else:
		for i in range(3):
			var page: String = ["bag","profile","settings"][i]
			var title: String = ["背包","个人","设置"][i]
			if not from_title or page == "settings":
				_button(surface,title,Rect2(28+i*180,70,164,44),show_page.bind(page),"tab_"+page)
		_button(surface,"返回",Rect2(970,20,120,42),close_menu,"close")
		match mode:
			"bag": _bag()
			"profile": _profile()
			"settings": _settings()
	var previous = root.find_child(focus_name,true,false) if focus_name != "" else null
	if previous is Button and not previous.disabled:
		previous.grab_focus()
	else:
		var buttons := root.find_children("*","Button",true,false)
		for button in buttons:
			if not button.disabled:
				button.grab_focus()
				break

func _title() -> void:
	_label(surface,"把海风带回旧屋",Rect2(74,126,800,60),42)
	_label(surface,"赶海、收纳、记录生活。\n海鲜市集的故事，从这一天开始。",Rect2(76,202,630,90),26)
	var status: Dictionary = world.save_service.read_save()
	var resume := _button(surface,"继续游戏",Rect2(76,320,300,52),world.continue_game,"continue")
	resume.disabled = not status.ok
	var new_button := _button(surface,"新游戏",Rect2(76,388,300,52),new_game_dialog,"new_game")
	new_button.disabled = status.get("future",false)
	_button(surface,"设置",Rect2(76,456,142,50),show_page.bind("settings"),"settings")
	_button(surface,"退出",Rect2(232,456,144,50),world.request_exit,"quit")
	_label(surface,status.message+"\n\n单人原型 · v0.5.2\n自动保存 / 单存档槽\n交易、种植和日循环尚未开放",Rect2(580,320,470,208),24)
	_portrait(surface,Vector2(860,154),144)

func new_game_dialog() -> void:
	var box := _modal("返乡人的名字", "name")
	var name_field := LineEdit.new()
	name_field.name = "player_name"
	name_field.text = "归乡人"
	name_field.max_length = 12
	name_field.position = Vector2(28,74)
	name_field.size = Vector2(460,52)
	box.add_child(name_field)
	_button(box,"取消",Rect2(28,176,210,48),cancel_modal,"cancel").grab_focus()
	_button(box,"开始",Rect2(264,176,224,48),func():
		var chosen: String = name_field.text
		cancel_modal()
		if world.save_service.has_files():
			confirm("新游戏将替换当前进度。\n确认从头开始？",func(): world.start_new_game(chosen))
		else:
			world.start_new_game(chosen)
	,"start")

func _portrait(parent: Control, point: Vector2, width: float) -> void:
	var portrait := TextureRect.new()
	portrait.texture = Art.player_frames().get_frame_texture("south",0)
	portrait.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	portrait.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	portrait.position = point
	portrait.size = Vector2(width,width*1.25)
	portrait.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	parent.add_child(portrait)

func container(side: String):
	return world.foraging.bag if side == "bag" else world.foraging.chest

func _grid(parent: Control, side: String, cell: Vector2) -> void:
	var slots: Array = container(side).snapshot()
	for i in range(slots.size()):
		var slot: Dictionary = slots[i]
		var item: Dictionary = catalog.get_item(slot.id)
		var button := _button(parent,"",Rect2(Vector2(i%6, i/6)*cell,cell-Vector2(6,6)),select_slot.bind(side,i),side+"_"+str(i))
		button.add_theme_stylebox_override("normal",PixelSkin.new("slot"))
		slots_count += 1
		button.tooltip_text = "空格" if slot.id == "" else item.name+" ×"+str(slot.amount)
		if category != "" and mode == "bag" and slot.id != "" and item.category != category:
			button.modulate.a = 0.32
			button.disabled = true
		if selected_side == side and selected_index == i:
			button.add_theme_stylebox_override("normal",PixelSkin.new("selected_slot"))
		if slot.id != "":
			var icon := Node2D.new()
			icon.set_script(load("res://scripts/forage_pickup.gd"))
			icon.kind = slot.id
			icon.scale = Vector2(2.4,2.4)
			icon.position = Vector2(cell.x/2-3,cell.y/2-8)
			button.add_child(icon)
			var number := _label(button,str(slot.amount),Rect2(8,cell.y-35,cell.x-22,28),20)
			number.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
			number.mouse_filter = Control.MOUSE_FILTER_IGNORE

func _bag() -> void:
	var names := ["全部","海产","食材","材料","工具"]
	var cats := ["","seafood","ingredients","materials","tools"]
	for i in range(5):
		_button(surface,names[i],Rect2(28+i*119,132,110,40),func(): category = cats[i]; selected_side = "bag"; render(),"filter_"+str(i))
	var grid := Control.new()
	grid.position = Vector2(28,190)
	surface.add_child(grid)
	_grid(grid,"bag",Vector2(98,84))
	_label(surface,"24 格 · 每格最多 99 个",Rect2(28,530,590,30),22)
	_details(650,184)
	_button(surface,"整理全部",Rect2(842,516,240,46),func(): world.foraging.bag.organize(); render(),"sort")

func _details(x: float, y: float) -> void:
	var slot: Dictionary = container(selected_side).snapshot()[selected_index]
	var title := "选择一个格子"
	var description := "选中物品可查看用途和操作。\n\n整理不会改变物品总数。"
	if slot.id != "":
		var item: Dictionary = catalog.get_item(slot.id)
		title = item.name+"  ×"+str(slot.amount)
		description = "海产 / 赶海收获\n"+item.description+"\n用途：后续交易与料理。\n当前不可直接使用。"
	_label(surface,title,Rect2(x,y,424,44),30)
	_label(surface,description,Rect2(x,y+54,424,148),24)
	if pending != "":
		_label(surface,"请选择目标空格（B 取消）" if pending == "split" else "请选择目标格（B 取消）",Rect2(x,y+208,430,90),24)
	elif slot.id != "":
		_button(surface,"移动 / 合并",Rect2(x,y+210,210,44),func(): pending = "move"; pending_source = selected_index; render(),"move")
		var split := _button(surface,"拆分",Rect2(x+222,y+210,202,44),action_split,"split")
		split.disabled = slot.amount < 2
		_button(surface,"丢弃…",Rect2(x,y+266,210,44),action_discard,"discard")

func select_slot(side: String, index: int) -> void:
	if pending != "" and side == selected_side:
		var ok: bool = container(side).split_stack(pending_source,index,pending_amount) if pending == "split" else container(side).move_slot(pending_source,index)
		note = "已调整物品位置。" if ok else "目标不适用，物品未改变。"
		pending = ""
	selected_side = side
	selected_index = index
	render()

func action_split() -> void:
	var slot: Dictionary = container(selected_side).snapshot()[selected_index]
	if slot.amount < 2: return
	choose_quantity("拆分数量",int(slot.amount)-1,func(amount):
		pending = "split"
		pending_source = selected_index
		pending_amount = amount
		render())

func action_discard() -> void:
	var slot: Dictionary = container(selected_side).snapshot()[selected_index]
	if slot.id == "": return
	var side := selected_side
	var index := selected_index
	choose_quantity("丢弃数量",int(slot.amount),func(amount):
		confirm("丢弃 %s ×%d？\n物品将永久移除，无法恢复。" % [catalog.get_item(slot.id).name,amount],func():
			container(side).discard(index,amount,true)
			world.save_progress()
			render()))

func _storage() -> void:
	_label(surface,"旧屋储物箱",Rect2(28,72,460,44),30)
	_button(surface,"关闭",Rect2(970,20,120,42),close_menu,"close")
	_label(surface,"随身背包 · 24 格",Rect2(28,120,460,32))
	_label(surface,"旧屋仓储 · 48 格（可滚动）",Rect2(586,120,500,32))
	var left := Control.new()
	left.position = Vector2(28,162)
	surface.add_child(left)
	_grid(left,"bag",Vector2(84,74))
	var scroll := ScrollContainer.new()
	scroll.position = Vector2(586,162)
	scroll.size = Vector2(516,296)
	scroll.follow_focus = true
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	surface.add_child(scroll)
	var grid := Control.new()
	grid.custom_minimum_size = Vector2(492,592)
	scroll.add_child(grid)
	_grid(grid,"chest",Vector2(82,74))
	var slot: Dictionary = container(selected_side).snapshot()[selected_index]
	_label(surface,("背包" if selected_side == "bag" else "仓储")+" / "+("空格" if slot.id == "" else catalog.get_item(slot.id).name+" ×"+str(slot.amount)),Rect2(28,464,650,34))
	var transfer := _button(surface,"存入 →" if selected_side == "bag" else "← 取出",Rect2(28,514,200,48),action_transfer,"transfer")
	transfer.disabled = slot.id == ""
	_button(surface,"存入同类",Rect2(246,514,224,48),func():
		var count: int = world.foraging.bag.deposit_matching(world.foraging.chest)
		note = "已存入 %d 个。未接收物品保留在背包。" % count
		world.save_progress()
		render(),"deposit")
	_button(surface,"整理背包",Rect2(586,514,224,48),func(): world.foraging.bag.organize(); render(),"sort_bag")
	_button(surface,"整理仓储",Rect2(836,514,240,48),func(): world.foraging.chest.organize(); render(),"sort_chest")

func action_transfer() -> void:
	var side := selected_side
	var index := selected_index
	var slot: Dictionary = container(side).snapshot()[index]
	if slot.id == "": return
	choose_quantity("存入数量" if side == "bag" else "取出数量",int(slot.amount),func(amount):
		var moved: int = container(side).transfer_to(container("chest" if side == "bag" else "bag"),index,amount)
		note = "已转移 %d 个；剩余物品保留原处。" % moved
		world.save_progress()
		render())

func _profile() -> void:
	_portrait(surface,Vector2(94,192),220)
	profile_text = "%s\n居住地：临海旧屋\n\n累计采集：%d 个\n发现海产：%d / 3 种" % [world.foraging.player_name,world.foraging.total_collected,world.foraging.discovered.size()]
	_label(surface,profile_text,Rect2(420,174,640,260),28)
	_label(surface,"每一次拾获，都是海边生活的一页。\n存入仓储或丢弃物品，不会抹去这些记录。",Rect2(420,462,620,90),24)

func _settings() -> void:
	var names := {"Master":"总音量","Music":"音乐","SFX":"音效"}
	var row := 0
	for bus in names:
		_label(surface,names[bus],Rect2(36,150+row*68,160,42))
		var slider := HSlider.new()
		slider.position = Vector2(216,150+row*68)
		slider.size = Vector2(340,42)
		slider.max_value = 1
		slider.step = 0.05
		slider.value = world.settings.volumes[bus]
		slider.value_changed.connect(func(value):
			if not world.settings.set_volume(bus,value):
				note = "设置保存失败，本次运行已应用。")
		surface.add_child(slider)
		row += 1
	_label(surface,"本版暂未加入音乐与环境音轨。",Rect2(36,360,650,38),22)
	_button(surface,"切换窗口 / 全屏",Rect2(36,412,340,50),func():
		get_window().mode = Window.MODE_WINDOWED if get_window().mode == Window.MODE_FULLSCREEN else Window.MODE_FULLSCREEN,"fullscreen")
	_label(surface,"WASD / 方向键：移动\nE：查看、拾取、确认\nB / Tab：手账、返回\nR：回到路口（保留收获）\n窗口大小可自由拖动调整。",Rect2(630,148,440,228),24)
	if not from_title:
		_button(surface,"保存并返回标题",Rect2(36,500,340,50),world.return_to_title,"save_title")
		_button(surface,"保存并退出",Rect2(402,500,300,50),world.request_exit,"save_quit")

func _modal(title: String, kind: String) -> Panel:
	cancel_modal()
	modal_kind = kind
	modal = Control.new()
	modal.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(modal)
	var shade := ColorRect.new()
	shade.color = Color(0,0,0,0.55)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	modal.add_child(shade)
	var panel := _panel(modal,Rect2(380,224,520,272))
	_label(panel,title,Rect2(28,20,464,86),24)
	return panel

func choose_quantity(title: String, maximum: int, action: Callable) -> void:
	var box := _modal(title,"quantity")
	quantity_action = action
	quantity = SpinBox.new()
	quantity.min_value = 1
	quantity.max_value = maximum
	quantity.value = maximum
	quantity.position = Vector2(100,102)
	quantity.size = Vector2(316,52)
	box.add_child(quantity)
	quantity.get_line_edit().focus_mode = Control.FOCUS_NONE
	quantity.get_line_edit().editable = false
	_button(box,"−",Rect2(28,102,60,52),func(): quantity.value -= 1,"less")
	_button(box,"+",Rect2(428,102,60,52),func(): quantity.value += 1,"more")
	_button(box,"取消",Rect2(28,188,210,48),cancel_modal,"cancel").grab_focus()
	_button(box,"确定数量",Rect2(264,188,224,48),accept_quantity,"quantity_ok")

func accept_quantity() -> void:
	if modal_kind != "quantity": return
	var value := int(quantity.value)
	var action := quantity_action
	cancel_modal()
	action.call(value)

func confirm(text: String, action: Callable) -> void:
	var box := _modal(text,"confirm")
	_button(box,"取消",Rect2(28,188,210,48),cancel_modal,"cancel").grab_focus()
	_button(box,"确认",Rect2(264,188,224,48),func(): cancel_modal(); action.call(),"confirm")

func cancel_modal() -> void:
	if is_instance_valid(modal):
		root.remove_child(modal)
		modal.queue_free()
	modal = null
	modal_kind = ""
	quantity_action = Callable()
	if is_instance_valid(surface):
		var button = surface.find_child("close",true,false)
		if button is Button: button.grab_focus()

func close_menu() -> void:
	if is_instance_valid(modal):
		cancel_modal()
		return
	if pending != "":
		pending = ""
		render()
		return
	if mode == "title": return
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
	if is_instance_valid(root):
		remove_child(root)
		root.queue_free()
	root = null
	modal = null
	get_tree().paused = false
	world.release_input = true

func _input(event: InputEvent) -> void:
	if mode == "" or not event is InputEventKey or not event.pressed or event.echo:
		return
	var key: int = event.physical_keycode if event.physical_keycode != 0 else event.keycode
	var focus := get_viewport().gui_get_focus_owner()
	if focus is LineEdit and key not in [KEY_TAB,KEY_ESCAPE]:
		return
	if key in [KEY_B,KEY_TAB]:
		get_viewport().set_input_as_handled()
		close_menu()
	elif key == KEY_E:
		get_viewport().set_input_as_handled()
		if focus is Button and not focus.disabled:
			focus.pressed.emit()

func _process(_delta: float) -> void:
	if is_instance_valid(modal):
		var focus := get_viewport().gui_get_focus_owner()
		if focus == null or not modal.is_ancestor_of(focus):
			var cancel = modal.find_child("cancel",true,false)
			if cancel is Button: cancel.grab_focus()

func show_save_failure(message: String, exit_game: bool) -> void:
	var box := _modal(message+"\n请选择重试或返回，不会自动退出。","save_error")
	_button(box,"返回游戏",Rect2(24,166,150,72),func(): cancel_modal(); dismiss(),"cancel").grab_focus()
	_button(box,"重试保存",Rect2(184,166,150,72),func():
		cancel_modal()
		if exit_game: world.request_exit()
		else: world.return_to_title(),"retry")
	_button(box,"不保存离开",Rect2(344,166,150,72),func():
		confirm("未保存的操作将丢失。\n仍然离开？",func():
			if exit_game: get_tree().quit()
			else:
				world.session_started = false
				show_page("title")),"leave")
