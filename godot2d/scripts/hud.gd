extends CanvasLayer

var prompt: Label
var panel: PanelContainer
var description: Label
var region: Label
var inventory: Label
var toast: Label
var toast_remaining := 0.0
var top: ColorRect
var bottom: ColorRect
var bag_bg: ColorRect
var controls: Label

func label_at(text: String, pos: Vector2, size: int, color: Color) -> Label:
	var label := Label.new()
	label.text = text
	label.position = pos * 2.0
	label.add_theme_font_override("font",load("res://assets/NotoSansCJKsc-Regular.otf"))
	label.add_theme_font_size_override("font_size",size * 2)
	label.add_theme_color_override("font_color",color)
	add_child(label)
	return label

func _ready() -> void:
	top = ColorRect.new()
	top.color = Color("264e55")
	top.size = Vector2(640,29)
	add_child(top)
	label_at("潮港旧屋",Vector2(16,3),16,Color("fff0cb"))
	label_at("海盐像素 · 赶海原型",Vector2(99,9),9,Color("c5d9c5"))
	region = label_at("晴  /  渔港的一天",Vector2(513,8),10,Color("fff0cb"))
	bag_bg = ColorRect.new()
	bag_bg.position = Vector2(357,32)
	bag_bg.size = Vector2(269,22)
	bag_bg.color = Color("264e55")
	add_child(bag_bg)
	inventory = label_at("",Vector2(366,35),11,Color("fff0cb"))
	toast = label_at("",Vector2(16,57),11,Color("fff0cb"))
	toast.add_theme_color_override("font_shadow_color",Color("234951"))
	toast.add_theme_constant_override("shadow_offset_x",1)
	toast.add_theme_constant_override("shadow_offset_y",1)
	bottom = ColorRect.new()
	bottom.position = Vector2(0,399)
	bottom.size = Vector2(640,17)
	bottom.color = Color("264e55")
	add_child(bottom)
	controls = label_at("WASD / 方向键  移动     E  拾取 / 查看 / 继续     R  回到路口",Vector2(15,400),9,Color("fff0cb"))
	prompt = label_at("沿着海岸走走，靠近地点可查看。",Vector2(16,374),11,Color("fff0cb"))
	prompt.add_theme_color_override("font_shadow_color",Color("234951"))
	prompt.add_theme_constant_override("shadow_offset_x",1)
	prompt.add_theme_constant_override("shadow_offset_y",1)
	panel = PanelContainer.new()
	panel.position = Vector2(136,283)
	panel.size = Vector2(368,104)
	var style := StyleBoxFlat.new()
	style.bg_color = Color("fff0cb")
	style.border_color = Color("315c63")
	style.set_border_width_all(4)
	style.content_margin_left = 28
	style.content_margin_top = 18
	style.content_margin_right = 28
	style.content_margin_bottom = 18
	panel.add_theme_stylebox_override("panel",style)
	description = Label.new()
	description.add_theme_font_override("font",load("res://assets/NotoSansCJKsc-Regular.otf"))
	description.add_theme_font_size_override("font_size",24)
	description.add_theme_color_override("font_color",Color("264e55"))
	panel.add_child(description)
	add_child(panel)
	panel.hide()
	get_viewport().size_changed.connect(layout)
	layout()

func layout() -> void:
	var viewport_size := get_viewport().get_visible_rect().size
	top.size = Vector2(viewport_size.x,58)
	region.position = Vector2(viewport_size.x-254,16)
	bag_bg.position = Vector2(viewport_size.x-566,64)
	bag_bg.size = Vector2(538,44)
	inventory.position = bag_bg.position + Vector2(18,6)
	bottom.position = Vector2(0,viewport_size.y-34)
	bottom.size = Vector2(viewport_size.x,34)
	controls.position = Vector2(30,viewport_size.y-32)
	prompt.position = Vector2(32,viewport_size.y-84)
	panel.size = Vector2(736,208)
	panel.position = Vector2((viewport_size.x-panel.size.x)/2.0,viewport_size.y-266)

func update_location(location: Dictionary) -> void:
	prompt.visible = not panel.visible
	prompt.text = "沿着海岸走走，靠近地点可查看。" if location.is_empty() else "[ E ]  " + location.title

func show_location(location: Dictionary) -> void:
	if location.is_empty():
		return
	description.text = location.title + "\n" + location.body + "\n[ E ] 关闭"
	panel.show()

func dismiss() -> void:
	panel.hide()

func update_inventory(counts: Dictionary) -> void:
	inventory.text = "背包   蛤蜊 %d   海螺 %d   海带 %d" % [counts.clam,counts.snail,counts.kelp]

func show_toast(text: String, seconds: float = 2.0) -> void:
	toast.text = text
	toast_remaining = seconds
	toast.show()

func _process(delta: float) -> void:
	toast_remaining = maxf(0.0,toast_remaining-delta)
	toast.visible = toast_remaining > 0.0 and not panel.visible
