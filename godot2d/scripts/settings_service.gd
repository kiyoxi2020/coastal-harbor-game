extends RefCounted
var path: String
var volumes := {"Master":0.8, "Music":0.7, "SFX":0.8}
func _init(directory: String) -> void:
	path = directory.path_join("settings.cfg")
	var config := ConfigFile.new()
	config.load(path)
	for bus in volumes:
		var value = config.get_value("audio",bus,volumes[bus])
		if value is float or value is int:
			volumes[bus] = clampf(value,0,1)
		if AudioServer.get_bus_index(bus) < 0:
			AudioServer.add_bus()
			AudioServer.set_bus_name(AudioServer.bus_count-1,bus)
		apply(bus)
func apply(bus: String) -> void:
	var index := AudioServer.get_bus_index(bus)
	AudioServer.set_bus_volume_db(index,linear_to_db(maxf(volumes[bus],0.0001)))
	AudioServer.set_bus_mute(index,volumes[bus] == 0)
func set_volume(bus: String, value: float) -> bool:
	volumes[bus] = clampf(value,0,1)
	apply(bus)
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var config := ConfigFile.new()
	for key in volumes:
		config.set_value("audio",key,volumes[key])
	return config.save(path) == OK
