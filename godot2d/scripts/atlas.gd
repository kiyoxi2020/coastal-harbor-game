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
	return preload("res://resources/player_frames.tres")
