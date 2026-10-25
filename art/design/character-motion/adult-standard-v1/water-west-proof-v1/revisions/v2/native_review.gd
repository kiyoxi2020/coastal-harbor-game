extends SceneTree

const DENSITY := 138.0 / 582.0
var base: String
var config: Dictionary
var textures: Array[ImageTexture] = []
var animated: Array[Sprite2D] = []
var phase := 0
var time_in_phase := 0.0
var loops := 0
var samples: Array[Dictionary] = []
var elapsed := 0.0
var captured: Dictionary = {}
var next_video_sample := 0.04
var video_samples := 0

func _initialize() -> void:
	base = get_script().resource_path.get_base_dir()
	DirAccess.make_dir_recursive_absolute(base.path_join("evidence/native-sequence"))
	config = JSON.parse_string(FileAccess.get_file_as_string(base.path_join("candidate.json")))
	root.size = Vector2i(1280, 720)
	root.content_scale_size = Vector2i(1280, 720)
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	for record in config.frames:
		var im := Image.load_from_file(base.path_join(record.file))
		textures.append(ImageTexture.create_from_image(im))
	var scene := Node2D.new()
	root.add_child(scene)
	for index in range(2):
		var panel := ColorRect.new()
		panel.position = Vector2(index * 640, 0)
		panel.size = Vector2(640, 720)
		panel.color = Color("e5d8bd") if index == 0 else Color("273238")
		scene.add_child(panel)
		var title := Label.new()
		title.position = Vector2(index * 640 + 20, 18)
		title.text = "WEST WATER / UNAPPROVED COMPLETE-FRAME PROOF"
		title.modulate = Color.BLACK if index == 0 else Color.WHITE
		scene.add_child(title)
		var sprite := Sprite2D.new()
		sprite.centered = false
		sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		sprite.position = Vector2(index * 640 + 30, 70)
		sprite.scale = Vector2.ONE * DENSITY
		sprite.texture = textures[0]
		scene.add_child(sprite)
		animated.append(sprite)
		var enlarged := Sprite2D.new()
		enlarged.centered = false
		enlarged.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		enlarged.position = Vector2(index * 640 + 230, 70)
		enlarged.scale = Vector2.ONE * DENSITY * 2.0
		enlarged.texture = textures[0]
		scene.add_child(enlarged)
		animated.append(enlarged)
		for frame in range(textures.size()):
			var still := Sprite2D.new()
			still.centered = false
			still.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			still.position = Vector2(index * 640 + 15 + (frame % 3) * 205, 400 + (frame / 3) * 145)
			still.scale = Vector2.ONE * DENSITY * 0.72
			still.texture = textures[frame]
			scene.add_child(still)

func _process(delta: float) -> bool:
	elapsed += delta
	time_in_phase += delta * 1000.0
	while time_in_phase >= config.frames[phase].duration_ms:
		time_in_phase -= config.frames[phase].duration_ms
		phase += 1
		if phase == textures.size():
			phase = 0
			loops += 1
	for sprite in animated:
		sprite.texture = textures[phase]
	samples.append({"t": elapsed, "phase": phase, "loop": loops})
	if elapsed >= next_video_sample and loops < 10:
		next_video_sample += 0.04
		capture_video.call_deferred(video_samples)
		video_samples += 1
	if not captured.has(phase) and elapsed > 0.1:
		captured[phase] = true
		capture_frame.call_deferred(phase)
	if loops >= 10:
		var report := {"artifact_digest": config.artifact_digest, "loops": loops, "samples": samples,
			"video_samples": video_samples, "nominal_video_fps": 25,
			"canvas_px": [1280,720], "native_display_scale": DENSITY,
			"scope": "Native diagnostic display only. No world integration, gameplay or frozen joint/contact trajectory."}
		var file := FileAccess.open(base.path_join("evidence/native-samples.json"), FileAccess.WRITE)
		file.store_string(JSON.stringify(report, "  "))
		quit()
	return false

func capture_frame(index: int) -> void:
	await RenderingServer.frame_post_draw
	var im := root.get_texture().get_image()
	im.save_png(base.path_join("evidence/native-%s.png" % index))

func capture_video(index: int) -> void:
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(base.path_join("evidence/native-sequence/frame-%04d.png" % index))
