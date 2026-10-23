extends SceneTree
const STATES = ["bare", "hair", "hat", "hair_hat"]
func _initialize() -> void:
	call_deferred("render")
func render() -> void:
	var args=OS.get_cmdline_user_args()
	assert(args.size()==3)
	assert(DisplayServer.get_name()!="headless")
	root.size=Vector2i(1280,880)
	root.content_scale_size=Vector2i(1280,880)
	root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	var canvas=Control.new();root.add_child(canvas)
	for background in ["e8e0ce","172127"]:
		for child in canvas.get_children():child.queue_free()
		await process_frame
		var bg=ColorRect.new();bg.color=Color(background);bg.size=Vector2(1280,880);canvas.add_child(bg)
		for row in range(2):
			for col in range(4):
				var path=args[row]+"/"+STATES[col]+"_south.png"
				var tex=ImageTexture.create_from_image(Image.load_from_file(path))
				assert(tex.get_size()==Vector2(512,768))
				var close=Sprite2D.new();close.texture=tex;close.centered=false;close.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
				close.region_enabled=true;close.region_rect=Rect2(100,218,260,153);close.scale=Vector2.ONE*1.08;close.position=Vector2(col*320+18,row*440+48);canvas.add_child(close)
				var body=Sprite2D.new();body.texture=tex;body.centered=false;body.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST;body.scale=Vector2.ONE*0.2371134;body.position=Vector2(col*320+158,row*440+412)-Vector2(230,707)*0.2371134;canvas.add_child(body)
				var label=Label.new();label.text=("BEFORE / " if row==0 else "AFTER / ")+STATES[col];label.position=Vector2(col*320+20,row*440+15);label.modulate=Color("172127") if background=="e8e0ce" else Color.WHITE;canvas.add_child(label)
		await process_frame
		await process_frame
		await RenderingServer.frame_post_draw
		DirAccess.make_dir_recursive_absolute(args[2])
		root.get_texture().get_image().save_png(args[2]+"/front-comparison-"+background+".png")
	print("FRONT_REVISION_NATIVE_8_PANELS_TWO_BACKGROUNDS_OK; no gameplay or saves")
	quit()
