extends SceneTree
func _initialize() -> void:
	call_deferred("run")
func run() -> void:
	for path in ["room_data", "house_interior", "interactive_door", "room_transition", "house_session"]:
		if not ResourceLoader.exists("res://scripts/"+path+".gd"):
			print("FAIL missing_"+path)
			quit(1)
			return
	var scene = load("res://scenes/harbor.tscn").instantiate()
	scene.set_meta("journal_test",true)
	scene.set_meta("save_directory","/private/tmp/coastal-house-"+str(Time.get_ticks_usec()))
	root.add_child(scene)
	var runner := Node.new()
	runner.set_script(load("res://tests/house_driver.gd"))
	scene.add_child(runner)
