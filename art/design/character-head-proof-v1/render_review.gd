extends SceneTree
const DIRECTIONS = ["south", "west", "east", "north"]
const STATES = ["bare", "hair", "hat", "hair_hat"]
const ROOTS = [Vector2(230,707), Vector2(251,708), Vector2(268,708), Vector2(282,708)]
var source_dir: String
var output_dir: String
func _initialize() -> void:
	call_deferred("render")
func render() -> void:
	var args = OS.get_cmdline_user_args()
	assert(args.size() == 2)
	source_dir = args[0]; output_dir = args[1]
	DirAccess.make_dir_recursive_absolute(output_dir)
	root.size = Vector2i(1280,960)
	root.content_scale_size = Vector2i(1280,960)
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	var canvas = Control.new(); root.add_child(canvas)
	for background in ["e8e0ce", "172127"]:
		for child in canvas.get_children(): child.queue_free()
		await process_frame
		var bg = ColorRect.new(); bg.color = Color(background); bg.size=Vector2(1280,960); canvas.add_child(bg)
		for row in range(4):
			for col in range(4):
				var direction: String = DIRECTIONS[col]
				var state: String = STATES[row]
				var tex = ImageTexture.create_from_image(Image.load_from_file(source_dir+"/"+state+"_"+direction+".png"))
				var sprite = Sprite2D.new(); sprite.texture=tex; sprite.centered=false; sprite.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
				var scale_factor = 0.2371134 # 582 source body px -> 138 screen px, matching protagonist 230*.15*4.
				sprite.scale = Vector2.ONE*scale_factor
				sprite.position=Vector2(col*320+80,row*240+209)-ROOTS[col]*scale_factor; canvas.add_child(sprite)
				var close = Sprite2D.new(); close.texture=tex; close.centered=false; close.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
				close.region_enabled=true; close.region_rect=Rect2(55,50,410,315); close.scale=Vector2.ONE*0.48
				close.position=Vector2(col*320+119,row*240+30); canvas.add_child(close)
				var label = Label.new();label.text=state+" / "+direction;label.position=Vector2(col*320+12,row*240+216);label.add_theme_font_size_override("font_size",16);label.modulate=Color("172127") if background=="e8e0ce" else Color.WHITE;canvas.add_child(label)
		await process_frame
		await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(output_dir+"/review-"+background+".png")
	print("HEAD_PROOF_NATIVE_16_STATES_TWO_BACKGROUNDS; rendered not user approved")
	quit()
