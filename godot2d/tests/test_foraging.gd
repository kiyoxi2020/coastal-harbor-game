extends SceneTree

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var scene = load("res://scenes/harbor.tscn").instantiate()
	scene.set_meta("save_directory", "/private/tmp/coastal-foraging-" + str(Time.get_ticks_usec()))
	root.add_child(scene)
	var runner := Node.new()
	runner.set_script(load("res://tests/foraging_driver.gd"))
	scene.add_child(runner)
