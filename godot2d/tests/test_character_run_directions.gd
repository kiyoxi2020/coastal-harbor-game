extends SceneTree
const Support = preload("res://tests/life_test_support.gd")
var s := Support.new()
var fixture := "/private/tmp/coastal-run-directions-fixture"
func _initialize() -> void: call_deferred("run")
func write_json(name: String, value: Dictionary) -> void:
	var file := FileAccess.open(fixture.path_join(name), FileAccess.WRITE)
	file.store_string(JSON.stringify(value))
	file.close()
func run() -> void:
	var trial = load("res://dev/character_walk_trial.tscn").instantiate()
	trial.art_root = ProjectSettings.globalize_path("res://../art/design/character-motion/adult-standard-v1/locomotion-v1")
	root.add_child(trial)
	await process_frame
	trial.set_physics_process(false)
	var source := ProjectSettings.globalize_path("res://../art/design/character-motion/adult-standard-v1/run-west-proof-v1")
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(source.path_join("candidate.json")))
	DirAccess.make_dir_recursive_absolute(fixture)
	DirAccess.remove_absolute(fixture.path_join("run-garments.json"))
	for reference in data.inputs:
		DirAccess.make_dir_recursive_absolute(fixture.path_join(reference).get_base_dir())
		DirAccess.copy_absolute(source.path_join(reference), fixture.path_join(reference))
	# Reused west textures only test loader/control semantics, never art acceptance.
	var old_frames: Array = data.frames.duplicate(true)
	data.directions = ["south", "west", "east", "north"]
	data.frames = []
	for direction in data.directions:
		for i in range(4):
			var entry: Dictionary = old_frames[i].duplicate(true)
			entry.pose_id = "run_%s_%d" % [direction, i]
			entry.direction = direction
			data.frames.append(entry)
	write_json("candidate.json", data)
	s.check("four_direction_candidate_loads", trial.load_run_candidate(fixture))
	if not trial.clips.has("run"):
		printerr(trial.motion_error)
		trial.queue_free()
		quit(1)
		return
	trial.set_motion_direction("south")
	trial.set_locomotion_action("run")
	trial.phase_ms = 123.0
	for direction in data.directions:
		s.check("run_turn_" + direction, trial.set_motion_direction(direction) and trial.current_action == "run" and trial.facing == direction)
		s.check("turn_preserves_phase_" + direction, is_equal_approx(trial.phase_ms, 123.0))
		s.check("texture_" + direction, trial.frame_metadata[trial.current_frame()].direction == direction and trial.pose.texture != null)
	var recipes := {"A": {}, "B": {"west": []}}
	for direction in data.directions:
		recipes.A[direction] = []
		for frame in old_frames: recipes.A[direction].append(frame.file)
	for frame in old_frames: recipes.B.west.append(frame.file)
	var layered := {"candidate_manifest_sha256": FileAccess.get_sha256(fixture.path_join("candidate.json")), "inputs": data.inputs, "recipes": recipes}
	write_json("run-garments.json", layered)
	s.check("partial_direction_B_loads", trial.load_run_candidate(fixture))
	trial.set_motion_direction("west")
	trial.set_garment("B")
	s.check("B_west_runs", trial.set_locomotion_action("run"))
	trial.phase_ms = 87.0
	s.check("unsupported_B_turn_atomic", not trial.set_motion_direction("south") and trial.facing == "west" and trial.current_action == "run" and trial.phase_ms == 87.0)
	trial.set_garment("A")
	s.check("A_turn_after_swap", trial.set_motion_direction("south"))
	trial.set_garment("B")
	s.check("unsupported_B_swap_atomic", trial.garment == "A" and trial.current_action == "run")
	trial.set_locomotion_action("walk")
	trial.set_garment("B")
	s.check("B_walk_still_works", trial.garment == "B" and trial.pose.texture != null)
	layered.recipes.B.west.pop_back()
	write_json("run-garments.json", layered)
	s.check("incomplete_direction_rejected", not trial.load_run_candidate(fixture) and not trial.clips.has("run") and trial.frames.A.size() == 20 and trial.frames.B.size() == 20)
	DirAccess.remove_absolute(fixture.path_join("run-garments.json"))
	data.frames[4].direction = "south"
	write_json("candidate.json", data)
	s.check("mismatched_direction_rejected", not trial.load_run_candidate(fixture))
	data.frames[4].direction = "west"
	data.directions[3] = "east"
	write_json("candidate.json", data)
	s.check("duplicate_direction_rejected", not trial.load_run_candidate(fixture))
	trial.queue_free()
	await process_frame
	print("RUN_DIRECTIONS checks=", s.checks.size(), " passed=", s.passed())
	quit(0 if s.passed() else 1)
