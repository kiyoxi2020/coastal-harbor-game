extends SceneTree

func _initialize() -> void:
	var notices = FileAccess.open("res://licenses/GODOT-THIRD-PARTY.json",FileAccess.WRITE)
	notices.store_string(JSON.stringify({"engine":Engine.get_version_info(),"copyright":Engine.get_copyright_info(),"licenses":Engine.get_license_info()},"\t"))
	quit()
