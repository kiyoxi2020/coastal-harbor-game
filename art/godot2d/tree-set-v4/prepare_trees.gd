extends SceneTree

const PALETTE = ["285746","35704a","4b8b4e","66a44f","85b952","a7cc67","c6dc87","dce7aa","65482f","94623c","be8c53"]

func _initialize() -> void:
	for index in range(4):
		prepare(index)
	quit()

func prepare(tree_id: int) -> void:
	var base: String = ProjectSettings.globalize_path("res://../").simplify_path() + "/"
	var original := Image.load_from_file(base+("art/godot2d/tree-set-v4/tree-%d-source.png" % tree_id))
	original.convert(Image.FORMAT_RGBA8)
	var image := original.duplicate() as Image
	# Remove almost-transparent generation residue; retain one connected tree.
	var width := image.get_width()
	var height := image.get_height()
	var seen := PackedByteArray()
	seen.resize(width*height)
	var largest := PackedInt32Array()
	for y in range(height):
		for x in range(width):
			var index := y*width+x
			if seen[index] != 0 or image.get_pixel(x,y).a < 0.5:
				continue
			var queue := PackedInt32Array([index])
			seen[index] = 1
			var head := 0
			while head < queue.size():
				var here := queue[head]
				head += 1
				var hx := here%width
				var hy := here/width
				for offset in [Vector2i(-1,0),Vector2i(1,0),Vector2i(0,-1),Vector2i(0,1)]:
					var p: Vector2i = Vector2i(hx,hy)+offset
					if p.x < 0 or p.y < 0 or p.x >= width or p.y >= height:
						continue
					var next := p.y*width+p.x
					if seen[next] == 0 and image.get_pixelv(p).a >= 0.5:
						seen[next] = 1
						queue.append(next)
			if queue.size() > largest.size():
				largest = queue
	var clean := Image.create(width,height,false,Image.FORMAT_RGBA8)
	clean.fill(Color.TRANSPARENT)
	for index in largest:
		var point := Vector2i(index%width,index/width)
		var color := original.get_pixelv(point)
		color.a = 1.0
		clean.set_pixelv(point,color)
	image = clean.get_region(clean.get_used_rect())
	var sizes := [Vector2(64,84),Vector2(62,82),Vector2(72,78),Vector2(60,72)]
	var factor := minf(sizes[tree_id].x/image.get_width(),sizes[tree_id].y/image.get_height())
	image.resize(roundi(image.get_width()*factor),roundi(image.get_height()*factor),Image.INTERPOLATE_NEAREST)
	var palette: Array[Color] = []
	for value in PALETTE:
		palette.append(Color(value))
	if tree_id == 3:
		for value in ["b87528","e7ae3e","f5d77b"]:
			palette.append(Color(value))
	for y in range(image.get_height()):
		for x in range(image.get_width()):
			var c := image.get_pixel(x,y)
			if c.a < 0.5:
				image.set_pixel(x,y,Color.TRANSPARENT)
				continue
			var nearest := palette[0]
			var distance := INF
			for candidate in palette:
				var d := Vector3(c.r-candidate.r,c.g-candidate.g,c.b-candidate.b).length_squared()
				if d < distance:
					distance = d
					nearest = candidate
			image.set_pixel(x,y,nearest)
	# Remove isolated one-pixel color speckles inside foliage, not silhouette tips.
	var before := image.duplicate() as Image
	for y in range(1,image.get_height()-1):
		for x in range(1,image.get_width()-1):
			var color := before.get_pixel(x,y)
			if color.a == 0 or color.r >= color.g:
				continue
			var neighbors: Array[Color] = [before.get_pixel(x-1,y),before.get_pixel(x+1,y),before.get_pixel(x,y-1),before.get_pixel(x,y+1)]
			if neighbors.has(color):
				continue
			for candidate in neighbors:
				if candidate.a == 1 and candidate.g > candidate.r and neighbors.count(candidate) >= 3:
					image.set_pixel(x,y,candidate)
					break
	var left := image.get_width()
	var right := 0
	for y in range(image.get_height()-3,image.get_height()):
		for x in range(image.get_width()):
			if image.get_pixel(x,y).a == 1:
				left = mini(left,x)
				right = maxi(right,x)
	var anchor := (left+right)/2
	var canvas := Image.create(96,96,false,Image.FORMAT_RGBA8)
	canvas.fill(Color.TRANSPARENT)
	canvas.blit_rect(image,Rect2i(Vector2i.ZERO,image.get_size()),Vector2i(48-anchor,94-image.get_height()))
	var target := base+("godot2d/assets/tree-set-v4/tree-%d.png" % tree_id)
	assert(canvas.save_png(target) == OK)
	print("Prepared tree ",tree_id,": used=",canvas.get_used_rect()," palette max=",palette.size())
