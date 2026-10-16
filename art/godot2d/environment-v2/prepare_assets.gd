extends SceneTree

var BASE: String = ProjectSettings.globalize_path("res://../").simplify_path() + "/"
var DEST: String = BASE + "godot2d/assets/environment-v2/"

func save(image: Image, name: String) -> void:
	assert(image.save_png(DEST + name + ".png") == OK)
	print("Prepared ",name," ",image.get_size())

func close_edges(image: Image) -> void:
	# Pair opposite border pixels; taper the correction over four pixels.
	# This is deterministic tile preparation, not new generated artwork.
	for y in range(64):
		var shared := image.get_pixel(0,y).lerp(image.get_pixel(63,y),0.5)
		for i in range(4):
			var weight := 1.0 - float(i)/4.0
			image.set_pixel(i,y,image.get_pixel(i,y).lerp(shared,weight))
			image.set_pixel(63-i,y,image.get_pixel(63-i,y).lerp(shared,weight))
	for x in range(64):
		var shared := image.get_pixel(x,0).lerp(image.get_pixel(x,63),0.5)
		for i in range(4):
			var weight := 1.0 - float(i)/4.0
			image.set_pixel(x,i,image.get_pixel(x,i).lerp(shared,weight))
			image.set_pixel(x,63-i,image.get_pixel(x,63-i).lerp(shared,weight))

func _initialize() -> void:
	DirAccess.make_dir_recursive_absolute(DEST)
	var source := Image.load_from_file(BASE + "art/godot2d/environment-v2/materials-source.png")
	var refined_water := Image.load_from_file(BASE + "art/godot2d/environment-v2/materials-water-refined.png")
	var half := source.get_width()/2
	var names := ["grass","shallow","deep","stone"]
	for i in range(4):
		var tile := source.get_region(Rect2i((i%2)*half,(i/2)*half,half,half))
		if i == 1 or i == 2:
			var water_half := refined_water.get_width()/2
			tile = refined_water.get_region(Rect2i((i%2)*water_half,(i/2)*water_half,water_half,water_half))
		tile.convert(Image.FORMAT_RGBA8)
		tile.resize(64,64,Image.INTERPOLATE_NEAREST)
		if i != 3:
			close_edges(tile)
		save(tile,names[i])
	var trees := Image.load_from_file(BASE + "art/godot2d/environment-v2/trees-source.png")
	# Measured from the generated 1254px atlas; pine extends past the nominal half.
	var crops := [Rect2i(0,0,647,640),Rect2i(650,0,604,640),Rect2i(0,650,685,604),Rect2i(689,650,565,604)]
	var limits := [Vector2i(78,84),Vector2i(70,76),Vector2i(82,72),Vector2i(66,68)]
	for i in range(4):
		var tree := trees.get_region(crops[i])
		tree.convert(Image.FORMAT_RGBA8)
		# Remove almost-transparent generation residue before measuring bounds.
		for y in range(tree.get_height()):
			for x in range(tree.get_width()):
				var color := tree.get_pixel(x,y)
				color.a = 1.0 if color.a >= 0.5 else 0.0
				tree.set_pixel(x,y,color)
		tree = tree.get_region(tree.get_used_rect())
		var ratio: float = minf(float(limits[i].x)/tree.get_width(),float(limits[i].y)/tree.get_height())
		tree.resize(roundi(tree.get_width()*ratio),roundi(tree.get_height()*ratio),Image.INTERPOLATE_NEAREST)
		# Anchor the trunk rather than the asymmetric crown's bounding box.
		var trunk_left := tree.get_width()
		var trunk_right := 0
		for y in range(tree.get_height()-5,tree.get_height()):
			for x in range(tree.get_width()):
				if tree.get_pixel(x,y).a > 0.5:
					trunk_left = mini(trunk_left,x)
					trunk_right = maxi(trunk_right,x)
		var anchor := (trunk_left+trunk_right)/2
		var canvas := Image.create(96,96,false,Image.FORMAT_RGBA8)
		canvas.fill(Color.TRANSPARENT)
		var left := clampi(48-anchor,1,95-tree.get_width())
		canvas.blit_rect(tree,Rect2i(Vector2i.ZERO,tree.get_size()),Vector2i(left,94-tree.get_height()))
		save(canvas,"tree-%d" % i)
	quit()
