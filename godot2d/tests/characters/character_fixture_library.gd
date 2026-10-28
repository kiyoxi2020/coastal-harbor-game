extends RefCounted
## Synthetic loader fixtures only; these textures are never game art.
static func save_json(path: String, data: Dictionary) -> void:
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var file := FileAccess.open(path, FileAccess.WRITE)
	file.store_string(JSON.stringify(data)); file.close()

static func locomotion(target: String, west_only: bool = false) -> String:
	DirAccess.make_dir_recursive_absolute(target.path_join("baked"))
	var data := {"schema_version": 1 if west_only else 2, "canvas_px": [512, 768], "root_anchor_px": [256, 708], "display_scale": 138.0 / 582.0, "artifact_digest": "synthetic-layout-test", "frames": [], "recipes": {"A": {"frames": []}, "B": {"frames": []}}}
	if west_only:
		for index in range(4): data.frames.append({"pose_id": "walk_w_%d" % index, "duration_ms": 80})
	else:
		data.actions = {"idle": {"loop": true, "directions": {}}, "walk": {"loop": true, "directions": {}}}
		data.move_policy = {"idle": {"base_world_speed": 0, "playback_rate": 1}, "walk": {"base_world_speed": 72, "playback_rate": 0.75}}
		for action in ["idle", "walk"]:
			for direction in ["south", "west", "east", "north"]:
				data.actions[action].directions[direction] = []
				for index in range(1 if action == "idle" else 4):
					var pose := "%s_%s_%d" % [action, direction, index]
					data.frames.append({"pose_id": pose, "duration_ms": 80, "action": action, "direction": direction})
					data.actions[action].directions[direction].append(pose)
		save_json(target.path_join("source-contract.json"), {"fixture": true})
		var digest := FileAccess.get_sha256(target.path_join("source-contract.json"))
		data.source_contract = {"source-contract.json": digest}; data.inputs = {"source-contract.json": {"sha256": digest}}
	for recipe in ["A", "B"]:
		for index in range(data.frames.size()):
			var image := Image.create(512, 768, false, Image.FORMAT_RGBA8)
			image.fill(Color(0.2 + index * 0.01, 0.5, 0.7 if recipe == "A" else 0.2))
			var name := "%s_%d.png" % [recipe, index]
			image.save_png(target.path_join("baked").path_join(name))
			var frame: Dictionary = data.frames[index].duplicate(true)
			frame.file = name; frame.sha256 = FileAccess.get_sha256(target.path_join("baked").path_join(name))
			data.recipes[recipe].frames.append(frame)
	save_json(target.path_join("baked/export-manifest.json"), data)
	return target

static func run_candidate(target: String, walk_digest: String) -> String:
	DirAccess.make_dir_recursive_absolute(target)
	DirAccess.remove_absolute(target.path_join("run-garments.json"))
	var data := {"template_id": "adult-standard-v1", "status": "unapproved_complete_frame_proof", "walk_artifact_digest": walk_digest, "canvas_px": [512, 768], "root_anchor_px": [256, 708], "display_scale": 138.0 / 582.0, "phase_map": [0, 1, 2, 3], "base_world_speed": 108, "directions": ["west"], "inputs": {}, "frames": []}
	for index in range(4):
		var image := Image.create(512, 768, false, Image.FORMAT_RGBA8)
		image.fill(Color(0.2 + index * 0.1, 0.6, 0.3))
		var name := "run_%d.png" % index
		image.save_png(target.path_join(name))
		data.inputs[name] = FileAccess.get_sha256(target.path_join(name))
		data.frames.append({"pose_id": "run_west_%d" % index, "direction": "west", "duration_ms": 80, "file": name})
	save_json(target.path_join("candidate.json"), data)
	return target

static func farming_schema1(target: String) -> String:
	var original_catalog = {"schema_version": 1, "template_id": "adult-standard-v1", "clips": []}
	for action in ["water", "hoe", "harvest"]:
		var directory := target.path_join(action)
		DirAccess.make_dir_recursive_absolute(directory)
		var data := {"schema_version": 1, "template_id": "adult-standard-v1", "action_id": action, "direction": "west", "status": "synthetic-fixture", "source_density_scale_vs_idle": 2, "display_scale": 138.0/1164.0, "canvas_px": [16,24], "root_anchor_px": [8,22], "inputs": {}, "frames": []}
		for index in range(4 if action == "hoe" else 2):
			var image := Image.create(16,24,false,Image.FORMAT_RGBA8)
			image.fill(Color(0.2+index*0.1,0.5,0.7))
			var name := "%d.png" % index
			image.save_png(directory.path_join(name))
			var digest := FileAccess.get_sha256(directory.path_join(name))
			data.inputs[name] = digest
			data.frames.append({"pose_id": action+str(index), "duration_ms": 200, "file": name, "sha256": digest, "source": name, "source_sha256": digest})
		save_json(directory.path_join("candidate.json"), data)
		original_catalog.clips.append({"action_id": action, "candidate": action+"/candidate.json", "sha256": FileAccess.get_sha256(directory.path_join("candidate.json")), "note": "合成关键姿态fixture"})
	save_json(target.path_join("catalog.json"), original_catalog)
	return target
