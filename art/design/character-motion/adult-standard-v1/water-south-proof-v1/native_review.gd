extends SceneTree
var config: Dictionary
var base: String
var textures: Array[ImageTexture] = []
var sprites: Array[Sprite2D] = []
var elapsed := 0.0
var phase := 0
var captures: Dictionary = {}
var samples: Array[Dictionary] = []
func _initialize() -> void:
	base = get_script().resource_path.get_base_dir()
	config = JSON.parse_string(FileAccess.get_file_as_string(base.path_join("candidate.json")))
	root.size = Vector2i(1280,720)
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	for f in config.frames:
		textures.append(ImageTexture.create_from_image(Image.load_from_file(base.path_join(f.file))))
	for panel_index in range(2):
		var panel := ColorRect.new()
		panel.position = Vector2(panel_index * 640,0)
		panel.size = Vector2(640,720)
		panel.color = Color("e5d8bd") if panel_index == 0 else Color("273238")
		root.add_child(panel)
		var label := Label.new()
		label.position = Vector2(panel_index * 640 + 15,15)
		label.text = "SOUTH WATER A / 2 KEY POSES / DIAGNOSTIC"
		label.modulate = Color.BLACK if panel_index == 0 else Color.WHITE
		root.add_child(label)
		for display_factor in [1.0,2.0]:
			var sprite := Sprite2D.new()
			sprite.centered = false
			sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			sprite.position = Vector2(panel_index * 640 + (30 if display_factor == 1.0 else 230),70)
			sprite.scale = Vector2.ONE * float(config.display_scale) * display_factor
			sprite.texture = textures[0]
			root.add_child(sprite)
			sprites.append(sprite)
func _process(delta: float) -> bool:
	elapsed += delta
	phase = int(elapsed * 2.0) % 2
	for sprite in sprites:sprite.texture = textures[phase]
	samples.append({"t":elapsed,"phase":phase})
	if elapsed > 0.1 and not captures.has(phase):
		captures[phase] = true
		capture.call_deferred(phase)
	if elapsed >= 10.0:
		var report := {"artifact_digest":config.artifact_digest,"diagnostic_two_pose_repetitions":10,"samples":samples,"native_display_scale":config.display_scale,"scope":"Actual Godot rendering, light/dark, 1x/2x uniform display. No complete action, trajectory, world, gameplay or user acceptance."}
		var file := FileAccess.open(base.path_join("evidence/native-samples.json"),FileAccess.WRITE)
		file.store_string(JSON.stringify(report,"  "))
		quit()
	return false
func capture(index: int) -> void:
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(base.path_join("evidence/native-%s.png" % index))
