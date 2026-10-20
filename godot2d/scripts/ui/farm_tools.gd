extends CanvasLayer
var world
var tool := "hoe"
var crop_id := "lettuce"
var mouse_target := false
var pointer_position := Vector2.INF
const TOOLS := ["hoe","water","plant","harvest"]
func _ready() -> void:
	world = get_parent()
	for i in range(4):
		$Panel/Tools.get_child(i).pressed.connect(select_tool.bind(TOOLS[i]))
	$Panel/Seeds/Lettuce.pressed.connect(select_seed.bind("lettuce"))
	$Panel/Seeds/Tomato.pressed.connect(select_seed.bind("tomato"))
func select_tool(id: String) -> void:
	tool=id
	_refresh()
func select_seed(id: String) -> void:
	crop_id=id
	tool="plant"
	_refresh()
func _refresh() -> void:
	$Panel/Seeds.visible=tool=="plant"
	for i in range(4): $Panel/Tools.get_child(i).button_pressed=tool==TOOLS[i]
	$Panel/Seeds/Lettuce.button_pressed=crop_id=="lettuce"
	$Panel/Seeds/Tomato.button_pressed=crop_id=="tomato"
	$Panel/Seeds/Counts.text="种子 %d / %d" % [world.foraging.bag.count_item("lettuce_seed"),world.foraging.bag.count_item("tomato_seed")]
func _process(_delta: float) -> void:
	visible=not world.world_map.visible and world.session_started and world.foraging.location=="harbor" and world.journal.mode=="" and not world.home.transition.busy and not world.hud.panel.visible
	_refresh()
func _unhandled_input(event: InputEvent) -> void:
	if world.world_map.visible or not visible or world.release_input or world.journal.mode!="" or world.home.transition.busy or world.hud.panel.visible or world.player.action_busy: return
	if event is InputEventMouseMotion:
		pointer_position=event.position
		mouse_target=true
	elif event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode==KEY_TAB:
			select_tool(TOOLS[(TOOLS.find(tool)+1)%4])
			get_viewport().set_input_as_handled()
		elif event.physical_keycode>=KEY_1 and event.physical_keycode<=KEY_4:
			select_tool(TOOLS[event.physical_keycode-KEY_1])
			get_viewport().set_input_as_handled()
		elif event.physical_keycode in [KEY_W,KEY_A,KEY_S,KEY_D,KEY_UP,KEY_DOWN,KEY_LEFT,KEY_RIGHT]: mouse_target=false
	elif event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT and event.pressed:
		pointer_position=event.position
		mouse_target=true
		world.use_farm_tool(world.farm_target(true))
		get_viewport().set_input_as_handled()
