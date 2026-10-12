extends RefCounted

static func region(id: String) -> AtlasTexture:
	var info: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/regions.json"))
	assert(info.has(id), "Missing sprite region: " + id)
	var coords: Array = info[id]
	var texture := AtlasTexture.new()
	texture.atlas = load("res://assets/environment.png")
	texture.region = Rect2(coords[0],coords[1],coords[2],coords[3])
	texture.filter_clip = true
	return texture

static func player_frames() -> SpriteFrames:
	var texture: Texture2D = load("res://assets/player.png")
	var frames := SpriteFrames.new()
	frames.remove_animation("default")
	var directions = ["south", "west", "east", "north"]
	for row in range(4):
		var id: String = directions[row]
		frames.add_animation(id)
		frames.set_animation_speed(id, 7.0)
		for column in range(4):
			var piece := AtlasTexture.new()
			piece.atlas = texture
			var left := floori(column * texture.get_width() / 4.0)
			var top := floori(row * texture.get_height() / 4.0)
			var right := floori((column+1) * texture.get_width() / 4.0)
			var bottom := floori((row+1) * texture.get_height() / 4.0)
			piece.region = Rect2(left,top,right-left,bottom-top)
			piece.filter_clip = true
			frames.add_frame(id,piece)
	return frames
