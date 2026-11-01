extends "res://tests/test_life_farming_native.gd"
# Integration observer only: the actual harbor player owns movement and animation.
const PACKAGE := "res://assets/characters/integrations/adult-standard-v2-visible-r001/manifest.json"
var trace: Array[Dictionary] = []
var loop_counts: Dictionary = {}
var video_frames: Array[Dictionary] = []
var capture_index := 0
var last_capture := 0
var fixture_started := 0

func run() -> void:
	evidence = "/private/tmp/coastal-body-game-native-r001"
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--body-evidence="):
			evidence = argument.trim_prefix("--body-evidence=")
	if not evidence.begins_with("/private/tmp/coastal-") or ".." in evidence or not FileAccess.file_exists(evidence.path_join("inputs.json")):
		push_error("Body observer requires a pre-frozen isolated evidence directory")
		quit(1)
		return
	if FileAccess.file_exists(evidence.path_join("trace.json")):
		push_error("Refusing to overwrite body observation")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(evidence.path_join("motion"))
	fixture_started = Time.get_ticks_msec()
	w = load("res://scenes/harbor.tscn").instantiate()
	w.set_meta("save_directory", evidence.path_join("save"))
	root.add_child(w)
	check("native", DisplayServer.get_name() != "headless")
	check("isolated", w.save_service.directory == evidence.path_join("save"))
	if DisplayServer.get_name() == "headless" or w.save_service.directory != evidence.path_join("save"):
		finish_observation()
		return
	check("start", w.start_new_game("身体接入验收"))
	for i in range(5): await physics_frame
	w.player.sprite.animation_looped.connect(func():
		var name: String = w.player.sprite.animation
		loop_counts[name] = int(loop_counts.get(name, 0)) + 1)
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(PACKAGE))
	check("manifest_local_only", manifest.status == "local-development-integration" and not manifest.production_release)
	for clip in manifest.clips:
		for f in range(clip.frames.size()):
			var texture: Texture2D = w.player.sprite.sprite_frames.get_frame_texture(clip.name, f)
			var actual := texture.get_image()
			actual.convert(Image.FORMAT_RGBA8)
			var hasher := HashingContext.new()
			hasher.start(HashingContext.HASH_SHA256)
			hasher.update(actual.get_data())
			check("actual_texture_" + clip.name + str(f), texture.resource_path == clip.frames[f].texture and FileAccess.get_sha256(texture.resource_path) == clip.frames[f].sha256 and hasher.finish().hex_encode() == clip.frames[f].rgba_sha256)
	# Continuous clear road runs; each directed segment counts actual loop signals.
	for running_mode in [false, true]:
		w.player.position = Vector2(90, 250)
		await move_cycles("east", running_mode, 10)
		await move_cycles("west", running_mode, 10)
		w.player.position = Vector2(288, 355)
		if running_mode:
			# The vertical road is shorter than ten running loops: two round trips,
			# each continuous six-loop leg, also exercises direction reversals.
			for trip in range(2):
				await move_cycles("north", true, 6)
				await move_cycles("south", true, 6)
		else:
			await move_cycles("north", false, 10)
			await move_cycles("south", false, 10)
	for direction in ["north", "west", "south", "east"]:
		for action in ["walk", "run"]:
			check("ten_loops_" + action + direction, int(loop_counts.get(action + "_" + direction, 0)) >= 10)
	w.player.position = Vector2(288, 245)
	await key(KEY_D, true)
	for i in range(5): await physics_frame
	check("live_walk", w.player.sprite.animation == "walk_east")
	await key(KEY_SHIFT, true)
	for i in range(5): await physics_frame
	check("live_run", w.player.sprite.animation == "run_east")
	await key(KEY_SHIFT, false)
	await key(KEY_D, false)
	for i in range(3): await physics_frame
	check("live_stop_idle", w.player.sprite.animation == "idle_east" and w.player.velocity == Vector2.ZERO)
	await capture("01-default-body-world")
	# Real tool state machine, four directions, all authored poses, no transactions.
	for direction in {"north": Vector2.UP, "west": Vector2.LEFT, "south": Vector2.DOWN, "east": Vector2.RIGHT}:
		for action in ["hoe", "water", "harvest"]:
			var vector: Vector2 = {"north": Vector2.UP, "west": Vector2.LEFT, "south": Vector2.DOWN, "east": Vector2.RIGHT}[direction]
			w.player.position = Vector2(288, 245)
			var origin: Vector2 = w.player.position
			w.player.play_tool_action(action, origin + vector * 20)
			var seen: Dictionary = {}
			var deadline := Time.get_ticks_msec() + 2500
			while w.player.action_busy and Time.get_ticks_msec() < deadline:
				seen[w.player.sprite.frame] = true
				await observe(action + "_" + direction)
			check("tool_" + action + direction, not w.player.action_busy and w.player.position == origin and seen.size() == w.player.sprite.sprite_frames.get_frame_count(action + "_" + direction) and w.player.sprite.animation == "idle_" + direction)
	# Pause during an actual action, then resume through its natural completion.
	w.player.play_tool_action("water", w.player.position + Vector2.DOWN * 20)
	for i in range(8): await process_frame
	paused = true
	var paused_frame: int = w.player.sprite.frame
	var paused_progress: float = w.player.sprite.frame_progress
	await create_timer(0.25, true).timeout
	check("pause_preserves_pose", w.player.sprite.frame == paused_frame and is_equal_approx(w.player.sprite.frame_progress, paused_progress) and w.player.action_busy)
	paused = false
	while w.player.action_busy: await process_frame
	check("resume_idle", w.player.sprite.animation == "idle_south")
	# Front/back placements inspect world ordering; positions are fixture setup,
	# never correction of an animation frame or in-motion character geometry.
	for placement in [
		["02-tree-behind", Vector2(308, 99)], ["03-tree-front", Vector2(308, 125)],
		["04-counter-behind", Vector2(442, 184)], ["05-counter-front", Vector2(442, 233)]]:
		w.player.position = placement[1]
		w.player.facing = "south"
		w.player.play_idle()
		await capture(placement[0])
	w.player.position = w.home.exterior_door.approach
	for i in range(4): await physics_frame
	for destination in ["house", "harbor"]:
		check("door_begin_" + destination, w.home.transition.begin())
		var deadline := Time.get_ticks_msec() + 10000
		var captured: Dictionary = {}
		while w.home.transition.busy and Time.get_ticks_msec() < deadline:
			var phase: String = w.home.transition.phase
			if phase in ["Crossing", "Arrival"] and not captured.has(phase):
				captured[phase] = true
				await capture("door-" + destination + "-" + phase)
			await observe("door_" + destination)
		check("door_finish_" + destination, not w.home.transition.busy and w.foraging.location == destination and w.player.doorway_hidden == 0.0)
	# Ready for a second door traversal from the actual arrival point.
	await capture("06-returned-harbor")
	finish_observation()

func move_cycles(direction: String, running_mode: bool, required: int) -> void:
	for input in ["left", "right", "up", "down", "run"]: Input.action_release(input)
	for i in range(3): await physics_frame
	var action := "run" if running_mode else "walk"
	var animation := action + "_" + direction
	var initial_count: int = loop_counts.get(animation, 0)
	var origin: Vector2 = w.player.position
	var input: String = {"north": "up", "west": "left", "south": "down", "east": "right"}[direction]
	Input.action_press(input)
	if running_mode: Input.action_press("run")
	var deadline := Time.get_ticks_msec() + 6000
	while int(loop_counts.get(animation, 0)) - initial_count < required and Time.get_ticks_msec() < deadline:
		await observe(animation)
	var travelled: float = w.player.position.distance_to(origin)
	check("move_" + animation + "_" + str(initial_count), int(loop_counts.get(animation, 0)) - initial_count >= required and travelled >= required * 0.32 * (108.0 if running_mode else 72.0) * 0.9)
	Input.action_release(input)
	Input.action_release("run")
	for i in range(3): await physics_frame
	check("stop_" + animation + "_" + str(initial_count), w.player.sprite.animation == "idle_" + direction and w.player.velocity == Vector2.ZERO)

func observe(segment: String) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	var now := Time.get_ticks_msec()
	var sprite: AnimatedSprite2D = w.player.sprite
	trace.append({"ms": now - fixture_started, "physics_frame": Engine.get_physics_frames(), "segment": segment,
		"position": [w.player.position.x, w.player.position.y], "animation": str(sprite.animation),
		"frame": sprite.frame, "progress": sprite.frame_progress, "busy": w.player.action_busy})
	if now - last_capture >= 80:
		last_capture = now
		var point: Vector2 = w.player.get_canvas_transform() * w.player.global_position
		var picture := root.get_texture().get_image().get_region(Rect2i(Vector2i(point) - Vector2i(160, 230), Vector2i(320, 280)))
		var name := "motion/frame-%05d.png" % capture_index
		picture.save_png(evidence.path_join(name))
		video_frames.append({"file": name, "ms": now - fixture_started, "segment": segment})
		capture_index += 1

func finish_observation() -> void:
	var file := FileAccess.open(evidence.path_join("trace.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify({"trace": trace, "video_frames": video_frames, "loops": loop_counts,
		"window_size": [root.size.x, root.size.y], "render_size": [root.get_texture().get_size().x, root.get_texture().get_size().y]}, "  "))
	file.close()
	finish()
