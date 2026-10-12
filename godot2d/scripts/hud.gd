extends CanvasLayer

var prompt: Label
var panel: PanelContainer
var description: Label
var region: Label

func label_at(text: String, pos: Vector2, size: int, color: Color) -> Label:
	var label := Label.new()
	label.text = text
	label.position = pos
	label.add_theme_font_override("font",load("res://assets/NotoSansCJKsc-Regular.otf"))
	label.add_theme_font_size_override("font_size",size)
	label.add_theme_color_override("font_color",color)
	add_child(label)
	return label

func _ready() -> void:
	var top := ColorRect.new()
	top.color = Color("264e55")
	top.size = Vector2(640,29)
	add_child(top)
	label_at("潮港旧屋",Vector2(16,3),16,Color("fff0cb"))
	label_at("海盐像素 · 漫步原型",Vector2(99,9),9,Color("c5d9c5"))
	region = label_at("晴  /  渔港的一天",Vector2(513,8),10,Color("fff0cb"))
	var bottom := ColorRect.new()
	bottom.position = Vector2(0,399)
	bottom.size = Vector2(640,17)
	bottom.color = Color("264e55")
	add_child(bottom)
	label_at("WASD / 方向键  移动     E  查看 / 继续     R  回到路口",Vector2(15,400),9,Color("fff0cb"))
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
	style.set_border_width_all(2)
	style.content_margin_left = 14
	style.content_margin_top = 9
	style.content_margin_right = 14
	style.content_margin_bottom = 9
	panel.add_theme_stylebox_override("panel",style)
	description = Label.new()
	description.add_theme_font_override("font",load("res://assets/NotoSansCJKsc-Regular.otf"))
	description.add_theme_font_size_override("font_size",12)
	description.add_theme_color_override("font_color",Color("264e55"))
	panel.add_child(description)
	add_child(panel)
	panel.hide()

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
