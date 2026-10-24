extends SceneTree

func _initialize() -> void:
	if not FileAccess.file_exists("res://review_data.gd"):
		printerr("FAIL: review_data.gd must validate the baked manifest")
		quit(1)
		return
	var data = load("res://review_data.gd").new()
	var args = OS.get_cmdline_user_args()
	if args.is_empty() or not args[0].begins_with("/private/tmp/coastal-"):
		printerr("FAIL: fixture manifest argument required")
		quit(1)
		return
	if not data.open_manifest(args[0]):
		printerr("FAIL: ", data.error)
		quit(1)
		return
	if data.textures["A"].size() != 4 or data.layer_textures["B"][0].size() != 3:
		printerr("FAIL: incomplete baked/source layers")
		quit(1)
		return
	if data.layer_textures["A"][0][0].get_size() != Vector2(512, 768):
		printerr("FAIL: registered source must stay on the full canvas")
		quit(1)
		return
	var original: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	original["recipes"]["B"]["frames"][2]["duration_ms"] = 999
	var invalid_path = args[0].get_base_dir().path_join("invalid-manifest.json")
	var file = FileAccess.open(invalid_path, FileAccess.WRITE)
	file.store_string(JSON.stringify(original))
	file.close()
	if data.open_manifest(invalid_path) or data.error != "A/B timeline mismatch":
		printerr("FAIL: mismatched timeline must be rejected")
		quit(1)
		return
	original = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	original["frames"][0]["duration_ms"] = 1.5
	for recipe in ["A", "B"]:
		original["recipes"][recipe]["frames"][0]["duration_ms"] = 1.5
	file = FileAccess.open(invalid_path, FileAccess.WRITE)
	file.store_string(JSON.stringify(original))
	file.close()
	if data.open_manifest(invalid_path):
		printerr("FAIL: fractional milliseconds violate the input contract")
		quit(1)
		return
	original = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	original["recipes"]["A"]["frames"][0]["sha256"] = "0".repeat(64)
	file = FileAccess.open(invalid_path, FileAccess.WRITE)
	file.store_string(JSON.stringify(original))
	file.close()
	if data.open_manifest(invalid_path) or not data.error.begins_with("Changed image:"):
		printerr("FAIL: changed baked image must be rejected")
		quit(1)
		return
	DirAccess.remove_absolute(invalid_path)
	print("PASS review manifest: real baked/source registration and corrupt input rejection")
	quit(0)
