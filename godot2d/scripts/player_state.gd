extends RefCounted

signal changed
const SAVE_VERSION := 2
const Inventory = preload("res://scripts/inventory/inventory_container.gd")
const Data = preload("res://scripts/harbor_data.gd")
const Catalog = preload("res://scripts/inventory/item_catalog.gd")
var bag = Inventory.new(24)
var chest = Inventory.new(48)
var player_name := "归乡人"
var location := "harbor"
var collected: Dictionary = {}
var discovered: Dictionary = {}
var total_collected := 0
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
		"position":[position.x,position.y]}

static func safe_position(location_name: String, point: Vector2, location_scene: Node2D) -> Vector2:
	if location_name not in ["harbor", "house"] or location_scene == null or not location_scene.has_method("safe_position"):
		return point
	return location_scene.safe_position(point)

static func _integer(value) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and float(value) == floor(float(value))

static func valid_data(value) -> bool:
	if not value is Dictionary or (value.get("version") != 1 and value.get("version") != SAVE_VERSION):
		return false
	if value.version == SAVE_VERSION and value.get("location") not in ["harbor","house"]:
		return false
	if not value.get("player_name") is String or clean_name(value.player_name) != value.player_name:
		return false
	var catalog := Catalog.new()
	var inventory_totals := {"clam":0, "snail":0, "kelp":0}
	for key in ["bag", "chest"]:
		if not value.get(key) is Array or value[key].size() != (24 if key == "bag" else 48):
			return false
		for slot in value[key]:
			if not slot is Dictionary or not slot.get("id") is String or not _integer(slot.get("amount")):
				return false
			if slot.id == "":
				if slot.amount != 0:
					return false
			elif not inventory_totals.has(slot.id) or slot.amount < 1 or slot.amount > catalog.stack_limit(slot.id):
				return false
			else:
				inventory_totals[slot.id] += int(slot.amount)
	if not value.get("collected") is Dictionary or not value.get("discovered") is Dictionary:
		return false
	var known: Dictionary = {}
	for entry in Data.pickups():
		known[entry.id] = entry.kind
	var earned := {"clam":0, "snail":0, "kelp":0}
	var found: Dictionary = {}
	for id in value.collected:
		if not known.has(id) or not value.collected[id] is bool or not value.collected[id]:
			return false
		earned[known[id]] += 1
		found[known[id]] = true
	if not _integer(value.get("total_collected")) or value.total_collected != value.collected.size() or value.discovered != found:
		return false
	for kind in earned:
		if inventory_totals[kind] > earned[kind]:
			return false
	if not value.get("position") is Array or value.position.size() != 2:
		return false
	for coordinate in value.position:
		if not (coordinate is int or coordinate is float) or not is_finite(float(coordinate)):
			return false
	return true

static func migrate_data(value) -> Dictionary:
	if not valid_data(value):
		return {}
	var migrated: Dictionary = value.duplicate(true)
	if migrated.version == 1:
		migrated.location = "harbor"
	migrated.version = SAVE_VERSION
	return migrated

func restore(value: Dictionary) -> bool:
	if not valid_data(value):
		return false
	location = "harbor" if value.version == 1 else value.location
	bag = Inventory.new(24)
	chest = Inventory.new(48)
	bag._slots = value.bag.duplicate(true)
	chest._slots = value.chest.duplicate(true)
	player_name = value.player_name
	collected = value.collected.duplicate()
	discovered = value.discovered.duplicate()
	total_collected = int(value.total_collected)
	_connect_containers()
	changed.emit()
	return true
