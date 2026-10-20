extends CanvasLayer
const Catalog=preload("res://scripts/region_catalog.gd")
var world
var selected_region:String="harbor"
var region_buttons:Dictionary={}
@onready var overview:Control=$Root/Panel/Overview
@onready var close_button:Button=$Root/Panel/Close

func _ready()->void:
	world=get_parent()
	close_button.pressed.connect(close)
	for region in Catalog.regions():
		var button:=Button.new()
		button.name="Region_"+region.id
		if not region.open:button.theme_type_variation="MapFuture"
		button.position=region.map+Vector2(-72,26)
		button.size=Vector2(144,54)
		button.toggle_mode=true
		button.add_theme_font_size_override("font_size",17)
		button.pressed.connect(select_region.bind(region.id))
		overview.add_child(button)
		region_buttons[region.id]=button

func _input(event:InputEvent)->void:
	if not event is InputEventKey or not event.pressed:return
	# Stop engine focus traversal on repeats without repeating map actions.
	if event.echo:
		if visible:get_viewport().set_input_as_handled()
		return
	var code:int=event.physical_keycode if event.physical_keycode!=0 else event.keycode
	if visible:
		match code:
			KEY_M:close()
			KEY_ESCAPE,KEY_B:close()
			KEY_TAB:cycle_focus(-1 if event.shift_pressed else 1)
			KEY_E:
				var focused=get_viewport().gui_get_focus_owner()
				if focused is BaseButton and not focused.disabled:
					if focused.toggle_mode:focused.button_pressed=not focused.button_pressed
					focused.pressed.emit()
			KEY_W,KEY_UP:navigate(Vector2.UP)
			KEY_S,KEY_DOWN:navigate(Vector2.DOWN)
			KEY_A,KEY_LEFT:navigate(Vector2.LEFT)
			KEY_D,KEY_RIGHT:navigate(Vector2.RIGHT)
		get_viewport().set_input_as_handled()
	elif code==KEY_M and world.session_started and world.journal.mode=="" and not world.release_input and not world.home.transition.busy:
		open()
		get_viewport().set_input_as_handled()

func open()->void:
	if world.journal.mode!="" or not world.session_started or world.home.transition.busy:return
	selected_region=actual_region()
	visible=true
	world.get_node("FarmTools").visible=false
	world.player.velocity=Vector2.ZERO
	world.player.sprite.stop()
	get_tree().paused=true
	render()
	region_buttons[selected_region].grab_focus()

func close()->void:
	visible=false
	get_tree().paused=false
	world.release_input=true

func actual_region()->String:
	return "harbor" if world.foraging.location=="house" else world.foraging.location

func select_region(id:String)->void:
	if Catalog.region(id).is_empty():return
	selected_region=id
	render()
	region_buttons[id].grab_focus()

func render()->void:
	$Root/Panel/Date.text="第 %d 日 · 海湾手记"%world.foraging.life.day_id
	for entry in Catalog.regions():
		var button:Button=region_buttons[entry.id]
		var status:String="◆ 你在这里" if entry.id==actual_region() else ("可探索" if entry.open else "▪ 未开放")
		if entry.id==actual_region() and world.foraging.location=="house":status+=" · 屋内"
		button.text=entry.name+"\n"+status
		button.button_pressed=entry.id==selected_region
		button.tooltip_text=entry.description+"\n"+entry.route

# The overview and close button are the only remaining focus groups.
func cycle_focus(_step:int)->void:
	if get_viewport().gui_get_focus_owner()==close_button:
		region_buttons[selected_region].grab_focus()
	else:close_button.grab_focus()

func navigate(direction:Vector2)->void:
	var focused=get_viewport().gui_get_focus_owner()
	if focused==close_button:return
	var origin:Vector2=region_buttons[selected_region].position
	var next:String=selected_region
	var best:float=INF
	for id in region_buttons:
		var delta:Vector2=region_buttons[id].position-origin
		if delta.dot(direction)<=0:continue
		var score:float=delta.length()+absf(delta.cross(direction))*1.5
		if score<best:
			best=score
			next=id
	if next!=selected_region:select_region(next)
