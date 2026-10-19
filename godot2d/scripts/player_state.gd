extends RefCounted

signal changed
const SAVE_VERSION := 3
const SUPPORTED_VERSIONS := [1, 2, 3]
const Inventory = preload("res://scripts/inventory/inventory_container.gd")
const Schema = preload("res://scripts/simulation/state_schema.gd")
var bag = Inventory.new(24)
var chest = Inventory.new(48)
var player_name := "归乡人"
var location := "harbor"
var collected: Dictionary = {}
var discovered: Dictionary = {}
var total_collected := 0
var life: Dictionary = Schema.default_life()
var counts: Dictionary:
	get:
		return {"clam":bag.count_item("clam"), "snail":bag.count_item("snail"), "kelp":bag.count_item("kelp")}

func _init() -> void:
	_connect_containers()

func _connect_containers() -> void:
	bag.changed.connect(_container_changed)
	chest.changed.connect(_container_changed)

func _container_changed() -> void:
	changed.emit()

static func clean_name(value: String) -> String:
	var result := ""
	for c in value:
		if c.unicode_at(0) >= 32 and c.unicode_at(0) != 127:
			result += c
	result = result.strip_edges().left(12)
	return "归乡人" if result.is_empty() else result

func add_item(kind: String, amount: int) -> bool:
	return amount > 0 and bag.add(kind, amount) == amount

func collect(id: String, kind: String) -> bool:
	if id.is_empty() or collected.has(id) or bag.space_for(kind) < 1:
		return false
	collected[id] = true
	discovered[kind] = true
	total_collected += 1
	bag.add(kind, 1)
	return true

func to_data(position: Vector2) -> Dictionary:
	return {"version":SAVE_VERSION, "location":location, "player_name":player_name, "bag":bag.snapshot(), "chest":chest.snapshot(),
		"collected":collected.duplicate(), "discovered":discovered.duplicate(), "total_collected":total_collected,
		"position":[position.x,position.y], "life":life.duplicate(true)}

static func safe_position(location_name: String, point: Vector2, location_scene: Node2D) -> Vector2:
	if location_name not in ["harbor", "house"] or location_scene == null or not location_scene.has_method("safe_position"):
		return point
	return location_scene.safe_position(point)

static func _integer(value) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and float(value) == floor(float(value))

static func valid_data(value) -> bool:
	if not value is Dictionary or not _integer(value.get("version")) or int(value.version) not in SUPPORTED_VERSIONS:
		return false
	if not value.get("player_name") is String or clean_name(value.player_name) != value.player_name:
		return false
	return Schema.validate_v3(value) if int(value.version) == 3 else Schema.validate_legacy(value)

static func migrate_data(value) -> Dictionary:
	if not valid_data(value):
		return {}
	if int(value.version) in [1, 2]:
		return Schema.migrate_legacy(value)
	return value.duplicate(true)

func restore(value: Dictionary) -> bool:
	var migrated := migrate_data(value)
	if migrated.is_empty():
		return false
	var next_bag = Inventory.new(24)
	var next_chest = Inventory.new(48)
	if not next_bag.restore_slots(migrated.bag) or not next_chest.restore_slots(migrated.chest):
		return false
	location = migrated.location
	bag = next_bag
	chest = next_chest
	player_name = migrated.player_name
	collected = migrated.collected.duplicate(true)
	discovered = migrated.discovered.duplicate(true)
	total_collected = int(migrated.total_collected)
	life = migrated.life.duplicate(true)
	_connect_containers()
	changed.emit()
	return true
