extends CanvasLayer

@onready var prompt: Label = $Root/Prompt
@onready var panel: PanelContainer = $Root/LocationPanel
@onready var description: Label = $Root/LocationPanel/Description
@onready var region: Label = $Root/Top/Region
signal bag_requested
@onready var bag_button: Button = $Root/BackpackButton
@onready var toast: Label = $Root/Toast
var toast_remaining := 0.0
@onready var top: ColorRect = $Root/Top
@onready var bottom: ColorRect = $Root/Bottom
@onready var controls: Label = $Root/Bottom/Controls

func _ready() -> void:
	bag_button.pressed.connect(func(): bag_requested.emit())

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

func show_toast(text: String, seconds: float = 2.0) -> void:
	toast.text = text
	toast_remaining = seconds
	toast.show()

func _process(delta: float) -> void:
	toast_remaining = maxf(0.0,toast_remaining-delta)
	toast.visible = toast_remaining > 0.0 and not panel.visible
