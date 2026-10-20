@tool
extends SceneTree

func _initialize() -> void:
	var original = load("res://scenes/world/harbor_exterior.tscn").instantiate(PackedScene.GEN_EDIT_STATE_MAIN)
	original.get_node("DepthSortedObjects/CoastalTree0").position = Vector2(320,240)
	var packed := PackedScene.new()
	var error := packed.pack(original)
	var restored = packed.instantiate()
	var failures := 0
	for name in ["Market", "Crates", "Boat", "CoastalTree0", "CoastalTree1", "CoastalTree2", "CoastalTree3", "CoastalTree4"]:
		var path: String = "DepthSortedObjects/" + name + "/Sprite2D"
		var before: Sprite2D = original.get_node(path)
		var after: Sprite2D = restored.get_node(path)
		var ok := after.texture != null and after.texture == before.texture and after.position == before.position and after.scale == before.scale
		print(("PASS " if ok else "FAIL ") + name + "_survives_editor_save")
		if not ok: failures += 1
	for id in {"clam_a": "clam", "snail_a": "snail", "kelp_a": "kelp", "clam_b": "clam", "snail_b": "snail", "kelp_b": "kelp"}:
		var expected: String = id.get_slice("_", 0)
		var ok: bool = restored.get_node("DepthSortedObjects/ForagePickups/" + id).get("kind") == expected
		print(("PASS " if ok else "FAIL ") + id + "_kind_survives_editor_save")
		if not ok: failures += 1
	var moved: bool = restored.get_node("DepthSortedObjects/CoastalTree0").position == Vector2(320,240)
	var entry := (load("res://scenes/harbor.tscn") as PackedScene).instantiate(PackedScene.GEN_EDIT_STATE_MAIN)
	var entry_packed := PackedScene.new()
	entry_packed.pack(entry)
	var entry_restored := entry_packed.instantiate()
	var player_retained := entry_restored.has_node("HarborExterior/DepthSortedObjects/Returnee")
	print(("PASS " if player_retained else "FAIL ") + "main_player_survives_editor_save")
	if not player_retained: failures += 1
	entry.free()
	entry_restored.free()
	print("ROUNDTRIP failures=", failures, " moved=", moved, " pack=", error)
	original.free()
	restored.free()
	quit(0 if failures == 0 and moved and error == OK else 1)
