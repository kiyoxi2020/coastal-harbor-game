extends SceneTree
const DIRS=["south","west","east","north"]
const ROOTS=[Vector2(230,707),Vector2(251,708),Vector2(268,708),Vector2(282,708)]
const PAGES=[["baseline","top","pants","shoes"],["top_pants","top_shoes","pants_shoes","top_pants_shoes"],["full_hair","full_hair_hat"]]
func _initialize() -> void:
	call_deferred("render")
func render() -> void:
	var args=OS.get_cmdline_user_args();assert(args.size()==2);assert(DisplayServer.get_name()!="headless")
	root.size=Vector2i(1280,960);root.content_scale_size=Vector2i(1280,960);root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	var canvas=Control.new();root.add_child(canvas);DirAccess.make_dir_recursive_absolute(args[1])
	# Same native actor really changes between all 8 clothing states in all 4 directions.
	var actor=Sprite2D.new();actor.visible=false;root.add_child(actor)
	var switches=0
	for page in [0,1]:
		for state in PAGES[page]:
			for direction in DIRS:
				var im=Image.load_from_file(args[0]+"/"+state+"_"+direction+".png")
				actor.texture=ImageTexture.create_from_image(im)
				assert(actor.texture.get_size()==Vector2(512,768))
				assert(actor.texture.get_image().get_data()==im.get_data())
				switches+=1
	assert(switches==32)
	print("NATIVE_CLOTHING_PREVIEW_32_TEXTURE_SWITCHES_OK")
	for background in ["e8e0ce","172127"]:
		for page in range(4):
			for child in canvas.get_children():child.queue_free()
			await process_frame
			var bg=ColorRect.new();bg.color=Color(background);bg.size=Vector2(1280,960);canvas.add_child(bg)
			var rows=3 if page==3 else PAGES[page].size()
			for row in range(rows):
				for col in range(4):
					var state="top_pants_shoes" if page==3 else PAGES[page][row]
					var tex=ImageTexture.create_from_image(Image.load_from_file(args[0]+"/"+state+"_"+DIRS[col]+".png"));assert(tex.get_size()==Vector2(512,768))
					if page!=3:
						var body=Sprite2D.new();body.texture=tex;body.centered=false;body.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST;body.scale=Vector2.ONE*0.2371134;body.position=Vector2(col*320+68,row*240+209)-ROOTS[col]*0.2371134;canvas.add_child(body)
					var close=Sprite2D.new();close.texture=tex;close.centered=false;close.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST;close.region_enabled=true
					if page==3:
						close.region_rect=[Rect2(65,355,380,215),Rect2(130,510,250,120),Rect2(120,620,290,110)][row];close.scale=Vector2.ONE*([0.72,1.0,0.96][row]);close.position=Vector2(col*320+12,row*240+40)
					else:
						close.region_rect=Rect2(65,360,380,365);close.scale=Vector2.ONE*0.50;close.position=Vector2(col*320+113,row*240+24)
					canvas.add_child(close)
					var label=Label.new();label.text=(("neck/cuff" if row==0 else "waist" if row==1 else "ankle/shoe") if page==3 else state)+" / "+DIRS[col];label.position=Vector2(col*320+12,row*240+216);label.add_theme_font_size_override("font_size",14);label.modulate=Color("172127") if background=="e8e0ce" else Color.WHITE;canvas.add_child(label)
			await process_frame
			await process_frame
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png(args[1]+"/page-"+str(page)+"-"+background+".png")
	print("CLOTHING_NATIVE_40_FRAMES_AND_12_INTERFACE_CLOSEUPS_TWO_BACKGROUNDS_RENDERED; not user approved")
	quit()
