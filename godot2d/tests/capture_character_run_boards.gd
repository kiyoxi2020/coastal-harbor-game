extends SceneTree
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var base := ProjectSettings.globalize_path("res://../art/design/character-motion/adult-standard-v1/run-west-proof-v1")
	var evidence := "/private/tmp/coastal-run-garments-native"
	var board := Node2D.new()
	root.add_child(board)
	board.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	for row in range(2):
		var bg := ColorRect.new()
		bg.position = Vector2(0, row * 720)
		bg.size = Vector2(2560, 720)
		bg.color = Color("e5e0d2" if row == 0 else "15202b")
		board.add_child(bg)
		for i in range(4):
			var image := Image.load_from_file(base.path_join("baked/B_%d.png" % i))
			for factor in [1.0, 2.0]:
				var sprite := Sprite2D.new()
				sprite.texture = ImageTexture.create_from_image(image)
				sprite.centered = false
				sprite.position = Vector2(80 + i * 610 + (160 if factor == 2 else 0), row * 720 + 100)
				sprite.scale = Vector2.ONE * (138.0 / 582.0) * factor
				board.add_child(sprite)
	for i in range(3): await process_frame
	RenderingServer.force_draw()
	var result := root.get_texture().get_image().save_png(evidence.path_join("03-light-dark-native.png"))
	print("RUN_NATIVE_BOARD saved=", result == OK, " renderer=", DisplayServer.get_name())
	quit(0 if result == OK and DisplayServer.get_name() != "headless" else 1)
