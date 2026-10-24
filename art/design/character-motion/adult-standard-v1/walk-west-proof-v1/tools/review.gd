extends Control
## Isolated reviewer. No user://, production scenes, or player state.
const Timeline = preload("res://timeline.gd")
const ReviewData = preload("res://review_data.gd")
@export var light_text_color := Color("1f242b")
@export var dark_text_color := Color("f2f4f5")
var data = ReviewData.new()
var timeline = Timeline.new()
var elapsed_ms: float = 0.0
var paused: bool = false
var dark: bool = false
var auto_active: bool = false
var capture_dir: String = ""
var selected_frame: int = -1
var selected_layer: int = 0
var selected_recipe: String = "A"
var source_mode: int = 0
var records: Array = []
var start_tick: int
var anchor: Vector2
var sprites: Array = []
var loaded: bool = false
@onready var status: Label = $Status
@onready var background: ColorRect = $Background
@onready var source_sprite: Sprite2D = $SourcePreview
@onready var layer_picker: OptionButton = $Layer

func _ready() -> void:
	var manifest_path := ""
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--manifest="):
			manifest_path = argument.trim_prefix("--manifest=")
		elif argument.begins_with("--capture-dir="):
			capture_dir = argument.trim_prefix("--capture-dir=")
	if not data.open_manifest(manifest_path):
		status.text = "REJECTED: " + data.error
		printerr(status.text)
		get_tree().quit(1)
		return
	if not capture_dir.is_empty() and (not capture_dir.begins_with("/private/tmp/coastal-") or capture_dir.simplify_path() != capture_dir):
		printerr("Capture directory must be canonical /private/tmp/coastal-*")
		get_tree().quit(1)
		return
	var durations: Array = []
	for frame in data.manifest["frames"]:
		durations.append(frame["duration_ms"])
	timeline.configure(durations)
	anchor = Vector2(data.manifest["root_anchor_px"][0], data.manifest["root_anchor_px"][1])
	sprites = [$A1, $B1, $A2, $B2]
	for i in range(4):
		sprites[i].scale = Vector2.ONE * float(data.manifest["display_scale"]) * (1.0 if i < 2 else 2.0)
		sprites[i].offset = -anchor
	source_sprite.offset = -anchor
	$Pause.pressed.connect(toggle_pause)
	$Previous.pressed.connect(func(): step(-1))
	$Next.pressed.connect(func(): step(1))
	$Backdrop.pressed.connect(toggle_background)
	$Recipe.item_selected.connect(func(index): selected_recipe = "A" if index == 0 else "B"; refresh_layers(); update_view())
	$Mode.item_selected.connect(func(index): source_mode = index; update_view())
	layer_picker.item_selected.connect(func(index): selected_layer = index; update_view())
	refresh_layers()
	loaded = true
	start_tick = Time.get_ticks_usec()
	update_view()
	if not capture_dir.is_empty():
		auto_active = true
		run_capture.call_deferred()

func _process(delta: float) -> void:
	if not loaded or auto_active:
		return
	if not paused:
		elapsed_ms += delta * 1000.0
	update_view()

func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo or auto_active or not loaded:
		return
	match event.keycode:
		KEY_SPACE: toggle_pause()
		KEY_LEFT: step(-1)
		KEY_RIGHT: step(1)
		KEY_B: toggle_background()

func toggle_pause() -> void:
	if auto_active:
		return
	paused = not paused
	update_view()

func step(direction: int) -> void:
	if auto_active:
		return
	paused = true
	elapsed_ms = timeline.start_ms(posmod(timeline.frame_at(elapsed_ms) + direction, 4))
	update_view()

func toggle_background() -> void:
	dark = not dark
	update_view()

func refresh_layers() -> void:
	layer_picker.clear()
	var frame := timeline.frame_at(elapsed_ms)
	for layer in data.manifest["recipes"][selected_recipe]["frames"][frame].get("layers", []):
		layer_picker.add_item(layer["id"])
	selected_layer = mini(selected_layer, maxi(0, layer_picker.item_count - 1))
	if layer_picker.item_count > 0:
		layer_picker.select(selected_layer)

func update_view() -> void:
	if not loaded:
		return
	var frame := timeline.frame_at(elapsed_ms)
	if frame != selected_frame:
		selected_frame = frame
		refresh_layers()
	for i in range(4):
		sprites[i].texture = data.textures["A" if i % 2 == 0 else "B"][frame]
	background.color = Color("303944") if dark else Color("dce1db")
	for label in [status, $NativeLabel, $ZoomLabel, $Bnative, $Bzoom, $SourceTitle, $SourceInfo, $Scope]:
		label.add_theme_color_override("font_color", dark_text_color if dark else light_text_color)
	$Pause.text = "Resume [Space]" if paused else "Pause [Space]"
	status.text = "%s  |  %.1f ms  |  loop %d  |  %s  |  %s\nartifact %s" % [data.manifest["frames"][frame]["pose_id"], elapsed_ms, timeline.loop_at(elapsed_ms), "paused" if paused else "playing", "dark" if dark else "light", str(data.manifest.get("artifact_digest", "missing")).left(24)]
	var layers: Array = data.manifest["recipes"][selected_recipe]["frames"][frame].get("layers", [])
	if layers.is_empty():
		source_sprite.texture = null
		$SourceInfo.text = "Legacy manifest: no source layers"
		return
	var layer: Dictionary = layers[selected_layer]
	source_sprite.texture = data.layer_textures[selected_recipe][frame][selected_layer] if source_mode == 0 else data.mask_textures[selected_recipe][frame][selected_layer]
	$SourceInfo.text = "%s / %s\nsource: %s\noffset: %s\nmask: %s\n%s" % [selected_recipe, layer["id"], layer["source"], str(layer["offset_px"]), str(layer.get("hide_mask", "none")), "Unmasked original source, registered; no hidden pixel repair" if source_mode == 0 else "Raw mask: white hides THIS target layer only"]

func capture(kind: String, filename: String, wall_usec: int) -> void:
	var frame := selected_frame
	var capture_elapsed := elapsed_ms
	var background_name := "dark" if dark else "light"
	await RenderingServer.frame_post_draw
	var image := get_viewport().get_texture().get_image()
	var result := image.save_png(capture_dir.path_join(filename))
	var indices: Array = []
	for i in range(4):
		indices.append(data.textures["A" if i % 2 == 0 else "B"].find(sprites[i].texture))
	records.append({"kind": kind, "file": filename, "frame": frame, "pose_id": data.manifest["frames"][frame]["pose_id"], "elapsed_ms": capture_elapsed, "loop": timeline.loop_at(capture_elapsed), "wall_usec": wall_usec, "captured_usec": Time.get_ticks_usec(), "background": background_name, "displayed_indices": indices, "png_error": result, "source_recipe": selected_recipe, "source_layer": selected_layer, "source_mode": "original" if source_mode == 0 else "mask"})
	if result != OK:
		printerr("Capture PNG failed: ", result)
		get_tree().quit(1)

func continuous_interval_ms() -> float:
	return minf(1000.0 / 24.0, float(timeline.durations_ms.min()) / 2.0)

func capture_complete(continuous_count: int, observed_frames: Dictionary) -> bool:
	return elapsed_ms >= timeline.cycle_ms * 10.0 and continuous_count >= 40 and observed_frames.size() == 4

func run_capture() -> void:
	DirAccess.make_dir_recursive_absolute(capture_dir)
	paused = true
	for backdrop in range(2):
		dark = backdrop == 1
		for frame in range(4):
			elapsed_ms = timeline.start_ms(frame)
			update_view()
			await capture("still", "still_%s_%d.png" % ["dark" if dark else "light", frame], Time.get_ticks_usec())
			await get_tree().process_frame
	# Extra views prove that raw source and target mask can be selected natively.
	elapsed_ms = 0.0
	dark = false
	for mode in range(2):
		source_mode = mode
		$Mode.select(mode)
		update_view()
		await capture("inspection", "inspection_%d.png" % mode, Time.get_ticks_usec())
		await get_tree().process_frame
	source_mode = 0
	$Mode.select(0)
	paused = false
	dark = false
	var epoch := Time.get_ticks_usec()
	var sample := 0
	var next_capture_ms := 0.0
	var interval_ms := continuous_interval_ms()
	var observed_frames := {}
	while true:
		var now := Time.get_ticks_usec()
		elapsed_ms = float(now - epoch) / 1000.0
		update_view()
		if elapsed_ms >= next_capture_ms:
			await capture("continuous", "continuous_%04d.png" % sample, now)
			sample += 1
			observed_frames[timeline.frame_at(elapsed_ms)] = true
			next_capture_ms = elapsed_ms + interval_ms
			if capture_complete(sample, observed_frames):
				break
		await get_tree().process_frame
	var continuous_records: Array = records.filter(func(record): return record["kind"] == "continuous")
	var first_ms: float = continuous_records[0]["elapsed_ms"]
	var last_ms: float = continuous_records[-1]["elapsed_ms"]
	var min_interval_ms: float = INF
	var max_interval_ms: float = 0.0
	for i in range(1, continuous_records.size()):
		var actual_interval: float = float(continuous_records[i]["elapsed_ms"]) - float(continuous_records[i - 1]["elapsed_ms"])
		min_interval_ms = minf(min_interval_ms, actual_interval)
		max_interval_ms = maxf(max_interval_ms, actual_interval)
	var actual_fps: float = (sample - 1) * 1000.0 / (last_ms - first_ms)
	var tool_hashes := {}
	for filename in ["review.gd", "review_data.gd", "review.tscn", "timeline.gd", "project.godot"]:
		tool_hashes[filename] = FileAccess.get_sha256("res://" + filename)
	var evidence := {"schema_version": 1, "recorded_utc": Time.get_datetime_string_from_system(true), "scope": "native_tool_fixture_or_artifact_playback_not_art_acceptance", "manifest_path": data.manifest_path, "manifest_sha256": FileAccess.get_sha256(data.manifest_path), "artifact_digest": data.manifest.get("artifact_digest", ""), "review_tools": tool_hashes, "cycle_ms": timeline.cycle_ms, "display_scale": data.manifest["display_scale"], "scales": [1, 1, 2, 2], "capture_target_fps": 1000.0 / interval_ms, "capture_interval_ms": interval_ms, "capture_actual_fps": actual_fps, "capture_interval_stats_ms": {"min": min_interval_ms, "mean": (last_ms - first_ms) / (sample - 1), "max": max_interval_ms}, "capture_min_continuous_samples": 40, "capture_required_pose_count": 4, "continuous_clock": "monotonic_ticks_usec_including_png_write_time", "captures": records}
	var file := FileAccess.open(capture_dir.path_join("capture.json"), FileAccess.WRITE)
	if file == null:
		printerr("Cannot save capture metadata")
		get_tree().quit(1)
		return
	file.store_string(JSON.stringify(evidence, "\t"))
	file.close()
	print("CAPTURE COMPLETE: ", capture_dir, " samples=", records.size(), " elapsed_ms=", elapsed_ms)
	get_tree().quit(0)
