extends SceneTree
# Visual inspection only: renders original RGBA without changing texture or mask.
var output_dir: String
func _initialize() -> void:
	call_deferred("render_review")
func render_review() -> void:
	var args = OS.get_cmdline_user_args()
	assert(args.size() == 2, "Expected source image path and output directory")
	output_dir = args[1]
	DirAccess.make_dir_recursive_absolute(output_dir)
	root.size = Vector2i(1280, 920)
	var image = Image.load_from_file(args[0])
	assert(image != null)
	var texture = ImageTexture.create_from_image(image)
	var control = Control.new()
	root.add_child(control)
	for row in range(2):
		var bg = ColorRect.new()
		bg.color = Color("e8e0ce") if row == 0 else Color("172127")
		bg.position = Vector2(0, row * 460)
		bg.size = Vector2(1280, 460)
		control.add_child(bg)
		for column in range(4):
			var sprite = Sprite2D.new()
			sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			sprite.texture = texture
			sprite.region_enabled = true
			sprite.region_rect = Rect2(column * 512 + 64, 96, 400, 640)
			sprite.centered = false
			sprite.position = Vector2(column * 320 + 20, row * 460 + 18)
			sprite.scale = Vector2.ONE * 0.65
			control.add_child(sprite)
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output_dir + "/alpha-backgrounds.png")
	print("ALPHA_REVIEW_RENDERED ", output_dir, "; no save file loaded or written")
	quit()
