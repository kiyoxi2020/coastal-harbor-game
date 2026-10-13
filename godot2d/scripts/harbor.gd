extends Node2D

const data = preload("res://scripts/harbor_data.gd")
const Art = preload("res://scripts/atlas.gd")
var player: CharacterBody2D
var sort_layer: Node2D
var hud: CanvasLayer
var foraging = preload("res://scripts/foraging_state.gd").new()
var pickup_nodes: Dictionary = {}

func _ready() -> void:
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
	var keys = {"left":[KEY_A,KEY_LEFT],"right":[KEY_D,KEY_RIGHT],"up":[KEY_W,KEY_UP],"down":[KEY_S,KEY_DOWN],"inspect":[KEY_E],"reset":[KEY_R]}
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
	if Input.is_action_just_pressed("inspect"):
		if hud.panel.visible:
			hud.dismiss()
		else:
			var target := nearest_pickup(player.position)
			if not target.is_empty():
				if foraging.collect(target.id,target.kind):
					pickup_nodes[target.id].hide()
					hud.show_toast(data.ITEM_NAMES[target.kind]+" +1")
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
	elif foraging.collected.size() == data.pickups().size() and nearest_location(player.position).is_empty():
		hud.prompt.text = "今日赶海收获已集齐；市集交易将在后续版本开放。"
