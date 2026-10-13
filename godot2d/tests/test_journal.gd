extends SceneTree
func _initialize() -> void:
	if not ResourceLoader.exists("res://scripts/ui/journal.gd"):
		push_error("Missing journal UI")
		quit(1)
		return
	call_deferred("run")
func run() -> void:
	var scene = load("res://scenes/harbor.tscn").instantiate()
	scene.set_meta("journal_test", true)
	scene.set_meta("save_directory", "/private/tmp/coastal-journal-"+str(Time.get_ticks_usec()))
	root.add_child(scene)
	var runner := Node.new()
	runner.set_script(load("res://tests/journal_driver.gd"))
	scene.add_child(runner)
