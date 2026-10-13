extends RefCounted
const MANIFEST_PATH := "res://assets/house-interior/pilot.json"
static var manifest: Dictionary = {}
static var loaded := false

static func entry(id: String) -> Dictionary:
	if not loaded:
		loaded=true
		if not FileAccess.file_exists(MANIFEST_PATH):
			push_warning("Missing cottage art manifest: "+MANIFEST_PATH)
		else:
			var parsed=JSON.parse_string(FileAccess.get_file_as_string(MANIFEST_PATH))
			if parsed is Dictionary: manifest=parsed
			else: push_warning("Invalid cottage art manifest: "+MANIFEST_PATH)
	return manifest.get(id,{})

static func texture_for(id: String) -> Texture2D:
	var data:=entry(id)
	var path: String=data.get("path",MANIFEST_PATH+"#"+id)
	if not ResourceLoader.exists(path):
		push_warning("Missing cottage art texture: "+path)
		return null
	var texture=load(path)
	if texture is Texture2D: return texture
	push_warning("Invalid cottage art texture: "+path)
	return null
