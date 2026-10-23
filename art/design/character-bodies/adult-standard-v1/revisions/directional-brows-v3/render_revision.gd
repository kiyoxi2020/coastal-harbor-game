extends SceneTree
const STATES=["bare","hair","hat","hair_hat"]
func _initialize() -> void:
	call_deferred("render")
func render() -> void:
	var args=OS.get_cmdline_user_args();assert(args.size()==3)
	assert(DisplayServer.get_name()!="headless")
	root.size=Vector2i(1280,960);root.content_scale_size=Vector2i(1280,960);root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	var canvas=Control.new();root.add_child(canvas)
	for background in ["e8e0ce","172127"]:
		for child in canvas.get_children():child.queue_free()
		await process_frame
		var bg=ColorRect.new();bg.color=Color(background);bg.size=Vector2(1280,960);canvas.add_child(bg)
		for row in range(4):
			for col in range(4):
				var d="west" if col<2 else "east"
				var stage=col%2
				var tex=ImageTexture.create_from_image(Image.load_from_file(args[stage]+"/"+STATES[row]+"_"+d+".png"));assert(tex.get_size()==Vector2(512,768))
				var close=Sprite2D.new();close.texture=tex;close.centered=false;close.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
				close.region_enabled=true;close.region_rect=Rect2(145,218,235,155);close.scale=Vector2.ONE*1.08;close.position=Vector2(col*320+12,row*240+46);canvas.add_child(close)
				var label=Label.new();label.text=("BEFORE / " if stage==0 else "AFTER / ")+d+" / "+STATES[row];label.position=Vector2(col*320+12,row*240+13);label.add_theme_font_size_override("font_size",15);label.modulate=Color("172127") if background=="e8e0ce" else Color.WHITE;canvas.add_child(label)
		await process_frame
		await process_frame
		await RenderingServer.frame_post_draw
		DirAccess.make_dir_recursive_absolute(args[2]);root.get_texture().get_image().save_png(args[2]+"/side-comparison-"+background+".png")
	print("SIDE_BROWS_NATIVE_BEFORE_AFTER_16_PANELS_TWO_BACKGROUNDS_OK; no gameplay or saves")
	quit()
