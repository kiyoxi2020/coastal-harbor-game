extends SceneTree

const DEFAULT_MANIFEST := "res://assets/house-interior/pilot.json"
const IDS := ["bed", "door_closed", "door_half", "door_open"]

func _initialize() -> void:
	var manifest_path := DEFAULT_MANIFEST
	var args := OS.get_cmdline_user_args()
	if args.size() >= 2 and args[0] == "--manifest":
		manifest_path = args[1]
	if not FileAccess.file_exists(manifest_path):
		printerr("FAIL missing pilot manifest")
		quit(1)
		return
	var data = JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
	if not data is Dictionary:
		printerr("FAIL invalid manifest")
		quit(1)
		return
	var door_size: Array = []
	var door_pivot: Array = []
	var floor_anchor: Array = []
	var widths: Array[int] = []
	var closed_size: Array = []
	for id in IDS:
		if not data.has(id) or not data[id] is Dictionary:
			printerr("FAIL missing entry: ", id)
			quit(1)
			return
		var entry: Dictionary = data[id]
		var size: Array = entry.get("logical_size", [])
		if size.size() != 2 or int(size[0]) <= 0 or int(size[1]) <= 0:
			printerr("FAIL logical size: ", id)
			quit(1)
			return
		if id == "bed":
			if int(size[0]) != 48 or int(size[1]) != 80:
				printerr("FAIL bed logical size")
				quit(1)
				return
		else:
			if door_size.is_empty():
				door_size = size
			elif size != door_size:
				printerr("FAIL door envelope mismatch")
				quit(1)
				return
			var pivot: Array = entry.get("pivot", [])
			if pivot.size() != 2 or int(pivot[0]) < 0 or int(pivot[1]) < 0 or int(pivot[0]) >= int(size[0]) or int(pivot[1]) >= int(size[1]):
				printerr("FAIL pivot bounds: ", id)
				quit(1)
				return
			if door_pivot.is_empty():
				door_pivot = pivot
			elif pivot != door_pivot:
				printerr("FAIL door pivot mismatch")
				quit(1)
				return
			var floor: Array = entry.get("floor_anchor", [])
			if floor.size() != 2 or int(floor[0]) < 0 or int(floor[1]) < 0 or int(floor[0]) >= int(size[0]) or int(floor[1]) > int(size[1]):
				printerr("FAIL floor anchor bounds: ", id)
				quit(1)
				return
			if floor_anchor.is_empty():
				floor_anchor = floor
			elif floor != floor_anchor:
				printerr("FAIL floor anchor mismatch")
				quit(1)
				return
			var recorded_closed: Array = entry.get("closed_leaf_size", [])
			if closed_size.is_empty():
				closed_size = recorded_closed
			elif recorded_closed != closed_size:
				printerr("FAIL closed leaf mismatch")
				quit(1)
				return
		if int(entry.get("alpha_threshold", -1)) != 128 or entry.get("source_region", []).size() != 4:
			printerr("FAIL source metadata: ", id)
			quit(1)
			return
		var source := str(entry.get("source", ""))
		if source.is_empty() or not FileAccess.file_exists(ProjectSettings.globalize_path("res://../" + source)):
			printerr("FAIL source missing: ", id)
			quit(1)
			return
		var resource = load(str(entry.get("path", "")))
		if not resource is Texture2D:
			printerr("FAIL missing texture: ", id)
			quit(1)
			return
		var bitmap: Image = resource.get_image()
		if bitmap == null or bitmap.is_empty() or bitmap.get_width() != int(size[0]) or bitmap.get_height() != int(size[1]):
			printerr("FAIL texture dimensions: ", id)
			quit(1)
			return
		var occupied := bitmap.get_used_rect()
		if occupied.size.x == 0 or occupied.size.y == 0:
			printerr("FAIL empty silhouette: ", id)
			quit(1)
			return
		var has_transparent := false
		for y in bitmap.get_height():
			for x in bitmap.get_width():
				var alpha := bitmap.get_pixel(x, y).a
				if alpha > 0.001 and alpha < 0.999:
					printerr("FAIL nonbinary alpha: ", id)
					quit(1)
					return
				if alpha < 0.001:
					has_transparent = true
		if not has_transparent:
			printerr("FAIL opaque texture: ", id)
			quit(1)
			return
		if id != "bed":
			widths.append(occupied.size.x)
			var recorded_visible: Array = entry.get("visible_leaf_size", [])
			if recorded_visible.size() != 2 or int(recorded_visible[0]) != occupied.size.x or int(recorded_visible[1]) != occupied.size.y:
				printerr("FAIL visible leaf metadata: ", id)
				quit(1)
				return
	if widths[0] <= widths[1] or widths[1] <= widths[2] or closed_size != data["door_closed"]["visible_leaf_size"]:
		printerr("FAIL door pose widths or closed leaf")
		quit(1)
		return
	print("PASS cottage pilot assets: 4")
	quit(0)
