extends Node
var checks: Dictionary = {}
var scene: Node2D
var output_dir := "res://verification-interaction"
func _ready() -> void:
	call_deferred("run")
func check(label: String, passed: bool) -> void:
	checks[label] = passed
	print(("PASS " if passed else "FAIL ")+label)
func frames(count: int = 3) -> void:
	for i in range(count):
		await get_tree().process_frame
func key(pressed: bool, echo: bool = false) -> void:
	# Inject before scene processing, not at frame_post_draw after its input poll.
	await get_tree().process_frame
	var event := InputEventKey.new()
	event.keycode=KEY_E
	event.physical_keycode=KEY_E
	event.pressed=pressed
	event.echo=echo
	Input.parse_input_event(event)
	Input.flush_buffered_events()
	await frames()
func tap() -> void:
	await key(true)
	await key(false)
func shot(name: String) -> void:
	if DisplayServer.get_name()=="headless":
		return
	await RenderingServer.frame_post_draw
	var image := get_viewport().get_texture().get_image()
	var save_error := image.save_png(output_dir.path_join(name+".png"))
	check("saved_"+name,save_error==OK)
func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):
			output_dir=arg.trim_prefix("--output=")
	DirAccess.make_dir_recursive_absolute(output_dir)
	scene=get_parent()
	await frames(5)
	scene.player.set_physics_process(false)
	scene.player.sprite.stop()
	scene.player.position=Vector2(20,40)
	await tap()
	check("empty_location_no_panel",not scene.hud.panel.visible)
	for entry in scene.data.locations():
		scene.hud.dismiss()
		scene.player.position=entry.point
		await key(true)
		check("e_opens_"+entry.id,scene.hud.panel.visible and entry.title in scene.hud.description.text)
		check("close_hint_"+entry.id,"[ E ] 关闭" in scene.hud.description.text)
		await frames(10)
		await key(true,true)
		check("hold_keeps_open_"+entry.id,scene.hud.panel.visible)
		if entry.id=="market":
			await shot("09-e-open")
		await key(false)
		await tap()
		check("e_closes_"+entry.id,not scene.hud.panel.visible)
		await frames(5)
		check("closed_stays_closed_"+entry.id,not scene.hud.panel.visible)
		if entry.id=="market":
			await shot("10-e-closed")
		await tap()
		check("e_reopens_"+entry.id,scene.hud.panel.visible)
	scene.player.position=Vector2(20,40)
	await tap()
	check("e_closes_after_leaving_range",not scene.hud.panel.visible)
	await tap()
	check("no_stale_reopen",not scene.hud.panel.visible)
	scene.player.position=Vector2(442,236)
	await tap()
	Input.action_press("reset")
	await frames()
	Input.action_release("reset")
	await frames()
	check("reset_closes_panel",not scene.hud.panel.visible and scene.player.position==scene.data.SPAWN)
	check("no_escape_binding",not InputMap.has_action("dismiss"))
	var labels := ""
	for child in scene.hud.get_children():
		if child is Label:
			labels+=child.text
	check("footer_e_continue","E  查看 / 继续" in labels and not "Esc" in labels)
	var passed := not checks.values().has(false)
	var f := FileAccess.open(output_dir.path_join("interaction-tests.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":passed,"checks":checks,"scope":"physical E press/release and keyboard echo events; current single-page flow; "+DisplayServer.get_name()},"\t"))
	print("INTERACTION RESULT ",checks.size()," passed=",passed)
	get_tree().quit(0 if passed else 1)
