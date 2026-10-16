extends SceneTree

var failures := 0
var count := 0
func _initialize() -> void:
	call_deferred("run")
func check(label: String, passed: bool) -> void:
	count += 1
	if not passed: failures += 1
	print(("PASS " if passed else "FAIL ") + label)
func set_template(ui: Object, key: String, value: String) -> void:
	var found := false
	for entry in ui.get_property_list():
		if entry.name == key:
			ui.set(key, value)
			found = true
	check(key + "_exported", found)
func run() -> void:
	var world = load("res://scenes/harbor.tscn").instantiate()
	world.set_meta("save_directory", "/private/tmp/coastal-editor-m1/save-" + str(Time.get_ticks_usec()))
	world.set_meta("journal_test", true)
	var ui = world.get_node("Journal")
	set_template(ui, "title_status_template", "状态<{status}> 自定义尾注")
	set_template(ui, "profile_template", "玩家={name}，总数={total}，发现={discovered}")
	set_template(ui, "save_failure_template", "错误<{message}> 自定义恢复说明")
	root.add_child(world)
	await process_frame
	ui._refresh_title()
	check("title_refresh_preserves_template", ui.get_node("Root/MainMenu/Surface/Status").text == "状态<" + world.save_service.read_save().message + "> 自定义尾注")
	world.start_new_game("模板测试")
	world.foraging.total_collected = 7
	world.foraging.discovered["clam"] = true
	ui._refresh_profile()
	check("profile_refresh_preserves_template", ui.profile_text == "玩家=模板测试，总数=7，发现=1")
	ui.show_save_failure("写入失败", false)
	check("save_failure_preserves_template", ui.get_node("Root/Dialogs/SaveErrorDialog/Panel/Title").text == "错误<写入失败> 自定义恢复说明")
	ui.cancel_modal()
	ui._refresh_profile()
	check("repeat_refresh_preserves_template", ui.profile_text == "玩家=模板测试，总数=7，发现=1")
	world.free()
	print("M1 RESULT %d/%d" % [count-failures,count])
	quit(0 if failures == 0 else 1)
