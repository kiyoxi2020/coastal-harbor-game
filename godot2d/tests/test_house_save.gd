extends SceneTree
var State = load("res://scripts/player_state.gd")
var Save = load("res://scripts/save_service.gd")
var Room = load("res://scripts/room_data.gd")
var checks: Dictionary = {}
func check(id: String, value: bool) -> void:
	checks[id] = value
	print(("PASS " if value else "FAIL ")+id)
func put(path: String, value: Dictionary) -> void:
	var f := FileAccess.open(path,FileAccess.WRITE)
	f.store_string(JSON.stringify(value))
	f.close()
func finish() -> void:
	DirAccess.make_dir_recursive_absolute("/private/tmp/coastal-house-save-verification")
	var f := FileAccess.open("/private/tmp/coastal-house-save-verification/tests.json",FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":not checks.values().has(false),"checks":checks},"\t"))
	f.close()
	print("HOUSE_SAVE ",checks.size()," passed=",not checks.values().has(false))
	quit(1 if checks.values().has(false) else 0)
func _initialize() -> void:
	call_deferred("run")
func run() -> void:
	var state = State.new()
	var first: Dictionary = state.to_data(Vector2(330,250))
	check("new_format",first.get("version")==3 and first.get("location")=="harbor" and first.has("life"))
	check("migration_api",state.has_method("migrate_data"))
	if checks.values().has(false):
		finish()
		return
	var legacy: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://tests/fixtures/life_save_v1.json"))
	var original := JSON.stringify(legacy)
	var migrated: Dictionary = State.migrate_data(legacy)
	check("legacy_valid",State.valid_data(legacy))
	check("legacy_migrates",migrated.version==3 and migrated.location=="harbor" and migrated.has("life"))
	check("legacy_unchanged",JSON.stringify(legacy)==original)
	migrated.bag[0].amount = 0
	check("migration_deep_copy",legacy.bag[0].amount==1)
	var home: Dictionary = State.migrate_data(legacy)
	home.location = "house"
	home.position = [320,328]
	check("house_valid",State.valid_data(home))
	var loaded = State.new()
	check("house_restore",loaded.restore(home) and loaded.location=="house")
	check("house_snapshot",loaded.to_data(Vector2(320,328)).location=="house")
	check("inventory_preserved",loaded.bag.count_item("clam")==1 and loaded.total_collected==1)
	var invalid: Dictionary = home.duplicate(true)
	invalid.location = "unknown"
	check("unknown_location",not State.valid_data(invalid))
	check("invalid_migration",State.migrate_data(invalid).is_empty())
	check("failed_restore_atomic",not loaded.restore(invalid) and loaded.location=="house" and loaded.bag.count_item("clam")==1)
	invalid = home.duplicate(true)
	invalid.erase("location")
	check("missing_location",not State.valid_data(invalid))
	invalid = home.duplicate(true)
	invalid.location = 1
	check("typed_location",not State.valid_data(invalid))
	invalid = home.duplicate(true)
	invalid.position = [INF,0]
	check("finite_position",not State.valid_data(invalid))
	invalid = legacy.duplicate(true)
	invalid.total_collected = 999
	check("legacy_still_validated",State.migrate_data(invalid).is_empty())
	check("restore_legacy",loaded.restore(legacy) and loaded.location=="harbor")
	var path := "/private/tmp/coastal-house-save-"+str(Time.get_ticks_usec())
	DirAccess.make_dir_recursive_absolute(path)
	var main := path+"/progress.json"
	put(main,legacy)
	var before := FileAccess.get_file_as_string(main)
	var service = Save.new(path)
	var result: Dictionary = service.read_save()
	check("read_legacy",result.ok and result.data.version==3 and result.data.location=="harbor")
	check("read_does_not_write",FileAccess.get_file_as_string(main)==before)
	check("write_house",service.write_save(home))
	check("house_roundtrip",service.read_save().ok and service.read_save().data.location=="house")
	check("legacy_backup_preserved",FileAccess.get_file_as_string(path+"/progress.backup.json")==before)
	invalid = home.duplicate(true)
	invalid.location = "bad"
	put(main,invalid)
	result = service.read_save()
	check("invalid_scene_backup",result.ok and result.recovered and result.data.location=="harbor")
	invalid.version = 99
	put(main,invalid)
	var future_before := FileAccess.get_file_as_string(main)
	check("future_blocks_read",service.read_save().get("future",false))
	check("future_blocks_write",not service.write_save(home))
	check("future_untouched",FileAccess.get_file_as_string(main)==future_before)
	put(main,legacy)
	check("write_legacy",service.write_save(legacy))
	var disk: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(main))
	check("write_normalizes",disk.version==3 and disk.location=="harbor" and disk.has("life"))
	var scene = load("res://scenes/harbor.tscn").instantiate()
	scene.set_meta("journal_test",true)
	scene.set_meta("save_directory","/private/tmp/coastal-house-save-scene-"+str(Time.get_ticks_usec()))
	root.add_child(scene)
	await process_frame
	check("outdoor_doorway_save_fallback",scene.home.safe_position("harbor",Room.OUTSIDE_DOOR)==scene.data.SPAWN)
	check("outdoor_approach_save_preserved",scene.home.safe_position("harbor",Room.OUTSIDE_APPROACH)==Room.OUTSIDE_APPROACH)
	check("outdoor_scene_collision_fallback",scene.home.safe_position("harbor",Vector2(100,150))==scene.data.SPAWN)
	scene.queue_free()
	finish()
