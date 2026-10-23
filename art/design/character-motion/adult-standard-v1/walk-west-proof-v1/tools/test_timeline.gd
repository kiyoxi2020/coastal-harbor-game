extends SceneTree

func _initialize() -> void:
	var script_path: String = get_script().resource_path.get_base_dir().path_join("timeline.gd")
	if not FileAccess.file_exists(script_path):
		printerr("FAIL: timeline.gd must implement shared frame selection")
		quit(1)
		return
	var timeline = load(script_path).new()
	timeline.configure([160, 160, 160, 160])
	var cases := [[0.0, 0], [159.999, 0], [160.0, 1], [319.999, 1], [320.0, 2], [480.0, 3], [639.999, 3], [640.0, 0], [640480.0, 3], [7041.0, 0]]
	for item in cases:
		if timeline.frame_at(item[0]) != item[1]:
			printerr("FAIL frame boundary: ", item)
			quit(1)
			return
	if timeline.loop_at(6400.0) != 10 or timeline.loop_at(6399.9) != 9:
		printerr("FAIL loop count")
		quit(1)
		return
	timeline.configure([70, 80, 90, 100])
	if timeline.frame_at(69.9) != 0 or timeline.frame_at(70.0) != 1 or timeline.frame_at(240.0) != 3 or timeline.frame_at(340.0) != 0:
		printerr("FAIL variable durations")
		quit(1)
		return
	print("PASS shared timeline: boundaries, uneven durations, low-rate jump and 10-loop count")
	quit(0)
