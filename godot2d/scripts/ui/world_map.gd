extends CanvasLayer
const Catalog=preload("res://scripts/region_catalog.gd")
var world
var markers:Array[Dictionary]=[]
var scene_views:Dictionary={}
func _ready()->void:
	world=get_parent()
	for color_key in ["font_color","font_hover_color","font_focus_color","font_pressed_color"]:
		$Root/Panel/Resources.add_theme_color_override(color_key,Color("285e67"))
	$Root/Panel/Close.pressed.connect(close)
	$Root/Panel/Resources.toggled.connect(func(_v):render())
func _input(event:InputEvent)->void:
	if not event is InputEventKey or not event.pressed or event.echo:return
	if visible:
		if event.physical_keycode in [KEY_M,KEY_ESCAPE,KEY_B]:
			close()
			get_viewport().set_input_as_handled()
		elif event.physical_keycode==KEY_E:
			var focused=get_viewport().gui_get_focus_owner()
			if focused is BaseButton:
				if focused.toggle_mode:focused.button_pressed=not focused.button_pressed
				focused.pressed.emit()
			get_viewport().set_input_as_handled()
	elif event.physical_keycode==KEY_M and world.session_started and world.journal.mode=="" and not world.release_input and not world.home.transition.busy:
		open()
		get_viewport().set_input_as_handled()
func open()->void:
	if world.journal.mode!="" or not world.session_started or world.home.transition.busy:return
	visible=true
	world.get_node("FarmTools").visible=false
	world.player.velocity=Vector2.ZERO
	world.player.sprite.stop()
	get_tree().paused=true
	render()
	$Root/Panel/Close.grab_focus()
func close()->void:
	visible=false
	get_tree().paused=false
	world.release_input=true
func render()->void:
	for child in $Root/Panel/Map.get_children():child.queue_free()
	markers.clear()
	scene_views.clear()
	var terrain:=TextureRect.new()
	terrain.texture=preload("res://assets/ui/world-map-v1/terrain.png")
	terrain.expand_mode=TextureRect.EXPAND_IGNORE_SIZE
	terrain.size=Vector2(1120,560)
	terrain.mouse_filter=Control.MOUSE_FILTER_IGNORE
	$Root/Panel/Map.add_child(terrain)
	var routes:=Control.new()
	routes.mouse_filter=Control.MOUSE_FILTER_IGNORE
	routes.draw.connect(func():draw_map(routes))
	$Root/Panel/Map.add_child(routes)
	for id in Catalog.open_regions():
		var source:Node2D=world.exterior if id=="harbor" else world.get_node("HarborDistrict")
		var viewport:=snapshot_scene(source)
		scene_views[id]=viewport
		$Root/Panel/Map.add_child(viewport)
		var image:=TextureRect.new()
		image.name="View_"+id
		image.texture=viewport.get_texture()
		image.position=Catalog.frame_origin(id)
		image.expand_mode=TextureRect.EXPAND_IGNORE_SIZE
		image.size=source.world_bounds.size
		image.scale=Vector2.ONE*Catalog.OVERVIEW_SCALE
		image.mouse_filter=Control.MOUSE_FILTER_IGNORE
		$Root/Panel/Map.add_child(image)
	for region in Catalog.regions():
		var label:=Label.new()
		label.text=region.name
		label.position=region.map-Vector2(70,35)
		label.add_theme_color_override("font_shadow_color",Color("f9f3df"))
		label.add_theme_constant_override("shadow_offset_x",1)
		label.add_theme_constant_override("shadow_offset_y",1)
		label.add_theme_color_override("font_color",Color("285e67") if region.open else Color("827e6d"))
		label.add_theme_font_size_override("font_size",17)
		$Root/Panel/Map.add_child(label)
	for point in Catalog.points(world):
		if point.kind=="resource" and not $Root/Panel/Resources.button_pressed:continue
		var mark:Dictionary=point.duplicate(true)
		mark.map=Catalog.project(point.region,point.point,world)
		mark.collected=point.kind=="resource" and world.foraging.collected.has(point.id)
		markers.append(mark)
		var button:=Button.new()
		button.flat=true
		button.add_theme_color_override("font_color",Color("287078") if not mark.collected else Color("8a8376"))
		button.position=mark.map-Vector2(10,10)
		button.size=Vector2(22,22)
		if point.kind=="resource":
			button.add_theme_font_size_override("font_size",11)
			button.add_theme_stylebox_override("normal",StyleBoxEmpty.new())
			button.add_theme_stylebox_override("focus",StyleBoxEmpty.new())
			button.position+=Vector2(4,-3 if point.id.ends_with("_a") else 5)
			button.size=Vector2(14,14)
		button.text={"building":"","farm":"▦","resource":"·" if mark.collected else "●","exit":"↕","reserved":""}[point.kind]
		if point.kind in ["building","farm","reserved"]:
			button.size=Vector2(20,20)
			button.add_theme_stylebox_override("normal",StyleBoxEmpty.new())
		button.tooltip_text=point.name+(" · 今日已采" if mark.collected else "")
		button.pressed.connect(func():$Root/Panel/Info.text=button.tooltip_text+" · 仅查看，不提供传送。")
		$Root/Panel/Map.add_child(button)
	var player_mark:=Label.new()
	player_mark.text="▼ 你在这里"+(" · 屋内" if world.foraging.location=="house" else "")
	var region:String=world.foraging.location
	var point:Vector2=world.exterior.get_node("InteractPoints/house").position if region=="house" else world.player.position
	player_mark.position=Catalog.project(region,point,world)+Vector2(10,12)
	player_mark.add_theme_font_size_override("font_size",14)
	player_mark.add_theme_color_override("font_shadow_color",Color("fff3da"))
	player_mark.add_theme_constant_override("shadow_offset_x",1)
	player_mark.add_theme_constant_override("shadow_offset_y",1)
	player_mark.add_theme_color_override("font_color",Color("b45132"))
	$Root/Panel/Map.add_child(player_mark)
	$Root/Panel/Date.text="第%d日 · 全镇总览"%world.foraging.life.day_id
	$Root/Panel/Map.queue_redraw()
func draw_map(map:Control)->void:
	var color:=Color("285e67")
	for region in Catalog.open_regions():
		var frame:=Rect2(Catalog.frame_origin(region),Vector2(640,416)*Catalog.OVERVIEW_SCALE)
		map.draw_rect(frame.grow(2),color,false,3)
	# Topological link between framed scenes; each scene keeps its own metric scale.
	map.draw_polyline(PackedVector2Array([Vector2(440,325),Vector2(480,325),Vector2(480,270),Vector2(520,270)]),color,3)
	for endpoint in [Vector2(950,120),Vector2(310,160),Vector2(935,365)]:
		map.draw_dashed_line(Vector2(850,200),endpoint,Color("a18b5c"),2,8)

# Snapshot the live visual subtree, without gameplay scripts, player or physics.
# Each isolated view is rendered once on map refresh, never every gameplay frame.
func snapshot_scene(source:Node2D)->SubViewport:
	var viewport:=SubViewport.new()
	viewport.disable_3d=true
	viewport.world_2d=World2D.new()
	viewport.transparent_bg=true
	viewport.size=Vector2i(source.world_bounds.size)
	viewport.render_target_update_mode=SubViewport.UPDATE_ONCE
	viewport.gui_disable_input=true
	viewport.process_mode=Node.PROCESS_MODE_ALWAYS
	var scene:Node2D=source.duplicate(0)
	scene.name="Scene"
	strip_snapshot(scene)
	scene.visible=true
	scene.transform=Transform2D.IDENTITY
	scene.position=-source.world_bounds.position
	scene.process_mode=Node.PROCESS_MODE_DISABLED
	viewport.add_child(scene)
	return viewport

func strip_snapshot(node:Node)->void:
	node.set_script(null)
	for child in node.get_children():
		if child is CollisionObject2D or child is CollisionShape2D or child is AudioStreamPlayer2D or child is Camera2D:
			node.remove_child(child)
			child.free()
		else:strip_snapshot(child)
