extends Control
## Fixed-ground production-speed diagnostic. No gameplay, player state or foot edits.
const ReviewData = preload("res://review_data.gd")
const TravelClock = preload("res://travel_clock.gd")
const TOTAL_LOOPS: int = 10
const CAPTURE_FPS: float = 30.0
var data = ReviewData.new()
var clock = TravelClock.new()
var loaded: bool = false
var auto_capture: bool = true
var capture_dir: String = ""
var elapsed_ms: float = 0.0
var previous_ms: float = 0.0
var resets: Array = []
var records: Array = []
var start_tick: int = 0
var start_utc: String = ""
@onready var sprites: Array = [$A, $B]

func _ready() -> void:
	var manifest_path := ""
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--manifest="):
			manifest_path = argument.trim_prefix("--manifest=")
		elif argument.begins_with("--capture-dir="):
			capture_dir = argument.trim_prefix("--capture-dir=")
		elif argument == "--test-no-capture":
			auto_capture = false
	if not data.open_manifest(manifest_path):
		printerr("TRAVEL REJECTED: ", data.error)
		get_tree().quit(1)
		return
	if capture_dir.is_empty():
		capture_dir = "/private/tmp/coastal-motion-travel-%d" % Time.get_ticks_usec()
	if not capture_dir.begins_with("/private/tmp/coastal-") or capture_dir.simplify_path() != capture_dir:
		printerr("Capture directory must be canonical /private/tmp/coastal-*")
		get_tree().quit(1)
		return
	var durations: Array = []
	for frame in data.manifest["frames"]:
		durations.append(frame["duration_ms"])
	clock.configure(durations)
	configure_display()
	start_tick = Time.get_ticks_usec()
	start_utc = Time.get_datetime_string_from_system(true)
	loaded = true
	apply_time(0.0)
	if auto_capture:
		run_capture.call_deferred()

func configure_display() -> void:
	var root: Array = data.manifest["root_anchor_px"]
	for sprite in sprites:
		sprite.scale = Vector2.ONE * float(data.manifest["display_scale"])
		sprite.offset = -Vector2(root[0], root[1])

func _process(_delta: float) -> void:
	if loaded and not auto_capture:
		apply_time(float(Time.get_ticks_usec() - start_tick) / 1000.0)

func apply_time(value_ms: float) -> void:
	elapsed_ms = value_ms
	resets.append_array(clock.resets_between(previous_ms, elapsed_ms))
	previous_ms = elapsed_ms
	var frame := clock.frame_at(elapsed_ms)
	var x := clock.root_x_at(elapsed_ms)
	for i in range(2):
		sprites[i].position.x = x
		sprites[i].texture = data.textures["A" if i == 0 else "B"][frame]
	$Status.text = "%s | %.1f ms | loop %d/%d | root x %.2f | pass %d" % [data.manifest["frames"][frame]["pose_id"], elapsed_ms, clock.loop_at(elapsed_ms), TOTAL_LOOPS, x, clock.pass_at(elapsed_ms)]
	$ResetInfo.text = "288 screen px/s LEFT = 72 world/s x camera4 | reset every %d COMPLETE loops | resets observed %d%s" % [clock.loops_per_pass, resets.size(), " | ROOT OFFSCREEN" if x < 0 else ""]

func capture(kind: String, filename: String, sampled_usec: int) -> void:
	var frame := clock.frame_at(elapsed_ms)
	var sample_elapsed := elapsed_ms
	var root_positions: Array = []
	var displayed_indices: Array = []
	for i in range(2):
		root_positions.append([sprites[i].position.x, sprites[i].position.y])
		displayed_indices.append(data.textures["A" if i == 0 else "B"].find(sprites[i].texture))
	await RenderingServer.frame_post_draw
	var error := get_viewport().get_texture().get_image().save_png(capture_dir.path_join(filename))
	records.append({"kind": kind, "file": filename, "wall_usec": sampled_usec, "captured_usec": Time.get_ticks_usec(), "elapsed_ms": sample_elapsed, "frame": frame, "pose_id": data.manifest["frames"][frame]["pose_id"], "loop": clock.loop_at(sample_elapsed), "pass": clock.pass_at(sample_elapsed), "root_positions_px": root_positions, "root_screen_x": root_positions[0][0], "world_speed_per_s": clock.WORLD_SPEED, "camera_zoom": clock.CAMERA_ZOOM, "screen_velocity_px_s": -clock.SCREEN_SPEED, "displayed_indices": displayed_indices, "root_offscreen": root_positions[0][0] < 0, "png_error": error})
	if error != OK:
		printerr("TRAVEL PNG failed: ", error)
		get_tree().quit(1)

func run_capture() -> void:
	if DirAccess.make_dir_recursive_absolute(capture_dir) != OK:
		printerr("Cannot create travel capture directory")
		get_tree().quit(1)
		return
	await capture("still_start", "start.png", Time.get_ticks_usec())
	await get_tree().process_frame
	start_tick = Time.get_ticks_usec()
	var sample := 0
	var next_capture_ms := 0.0
	while true:
		var now := Time.get_ticks_usec()
		apply_time(float(now - start_tick) / 1000.0)
		if elapsed_ms >= next_capture_ms:
			await capture("continuous", "travel_%04d.png" % sample, now)
			sample += 1
			next_capture_ms = elapsed_ms + 1000.0 / CAPTURE_FPS
			if elapsed_ms >= clock.cycle_ms * TOTAL_LOOPS:
				break
		await get_tree().process_frame
	var hashes := {}
	for filename in ["travel_review.gd", "travel_review.tscn", "travel_clock.gd", "review_data.gd", "timeline.gd", "project.godot"]:
		hashes[filename] = FileAccess.get_sha256("res://" + filename)
	var evidence := {"schema_version": 1, "scope": "native_fixed_ground_travel_diagnostic_contact_art_unassessed", "recorded_utc": start_utc, "manifest_path": data.manifest_path, "manifest_sha256": FileAccess.get_sha256(data.manifest_path), "artifact_digest": data.manifest.get("artifact_digest", ""), "review_tools": hashes, "frames": data.manifest["frames"], "cycle_ms": clock.cycle_ms, "requested_loops": TOTAL_LOOPS, "display_scale": data.manifest["display_scale"], "root_anchor_px": data.manifest["root_anchor_px"], "world_speed_per_s": clock.WORLD_SPEED, "camera_zoom": clock.CAMERA_ZOOM, "screen_velocity_px_s": -clock.SCREEN_SPEED, "root_start_x": clock.START_X, "min_root_x_for_pass_planning": clock.MIN_ROOT_X, "loops_per_pass": clock.loops_per_pass, "capture_target_fps": CAPTURE_FPS, "clock": "real_monotonic_usec_including_png_writes", "resets": resets, "captures": records}
	var file := FileAccess.open(capture_dir.path_join("travel-capture.json"), FileAccess.WRITE)
	if file == null:
		printerr("Cannot write travel metadata")
		get_tree().quit(1)
		return
	file.store_string(JSON.stringify(evidence, "\t"))
	file.close()
	print("TRAVEL CAPTURE COMPLETE: ", capture_dir, " samples=", sample, " elapsed_ms=", elapsed_ms, " resets=", resets.size())
	get_tree().quit(0)
