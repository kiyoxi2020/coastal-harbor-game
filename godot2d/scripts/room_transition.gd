extends Node
signal phase_changed(phase: String)
var home
var busy := false
var phase := "Idle"
var stable_snapshot: Dictionary = {}
var exit_pending := false
var fade: ColorRect
func _ready() -> void:
	var layer:=CanvasLayer.new()
	layer.layer=40
	add_child(layer)
	fade=ColorRect.new()
	fade.color=Color(0.06,0.12,0.14,1)
	fade.modulate.a=0
	fade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	fade.mouse_filter=Control.MOUSE_FILTER_IGNORE
	layer.add_child(fade)
func set_phase(value: String) -> void:
	phase=value
	phase_changed.emit(value)
func begin() -> bool:
	var world=home.world
	if busy or not world.session_started or world.journal.mode!="" or world.hud.panel.visible:
		return false
	var door=home.active_door()
	if not door.can_interact(world.player.position): return false
	stable_snapshot=world.foraging.to_data(home.safe_position(world.foraging.location,world.player.position))
	busy=true
	world.hud.dismiss()
	world.player.velocity=Vector2.ZERO
	world.player.z_index=1
	world.release_input=true
	run.call_deferred()
	return true
func pause_for(seconds: float) -> void:
	await get_tree().create_timer(seconds,false).timeout
func walk_to(point: Vector2,duration: float) -> void:
	var player=home.world.player
	var delta: Vector2=point-player.position
	player.facing="south" if delta.y>=0 else "north"
	if absf(delta.x)>absf(delta.y): player.facing="east" if delta.x>0 else "west"
	player.sprite.play(player.facing)
	var tween:=create_tween()
	tween.tween_property(player,"position",point,duration)
	await tween.finished
	player.sprite.stop()
func animate_door(door,opening: bool) -> void:
	for pose in ([0,1,2] if opening else [2,1,0]):
		door.set_pose(pose)
		await pause_for(0.1)
func opacity(value: float) -> void:
	var tween:=create_tween()
	tween.tween_property(fade,"modulate:a",value,0.15)
	await tween.finished
func run() -> void:
	var world=home.world
	var source: String=world.foraging.location
	var destination: String="house" if source=="harbor" else "harbor"
	var door=home.active_door()
	set_phase("Approach")
	await walk_to(door.approach,0.15)
	set_phase("Opening")
	await animate_door(door,true)
	set_phase("Crossing")
	await walk_to(door.position+Vector2(0,2 if door.inside else -2),0.2)
	set_phase("FadeOut")
	await opacity(1)
	set_phase("Swap")
	if not home.switch_room(destination,Vector2.ZERO,true):
		home.switch_room(source,Vector2(stable_snapshot.position[0],stable_snapshot.position[1]))
		await opacity(0)
		busy=false
		world.player.z_index=0
		world.hud.show_toast("房间暂时无法进入，已回到门前。",6)
		set_phase("Idle")
		if exit_pending: world.request_exit()
		return
	door=home.active_door()
	door.set_pose(2)
	world.player.position=door.position+Vector2(0,-2 if door.inside else 2)
	set_phase("FadeIn")
	await opacity(0)
	set_phase("Arrival")
	await walk_to(door.approach,0.2)
	set_phase("Closing")
	await animate_door(door,false)
	world.player.velocity=Vector2.ZERO
	world.player.z_index=0
	stable_snapshot=world.foraging.to_data(world.player.position)
	# Save the stable destination before accepting held input again.
	busy=false
	world.save_progress()
	busy=true
	set_phase("AwaitRelease")
	while held_input() and not exit_pending: await get_tree().process_frame
	world.release_input=false
	busy=false
	set_phase("Idle")
	if exit_pending: world.request_exit()
func held_input() -> bool:
	for action in ["inspect","left","right","up","down","reset","journal"]:
		if Input.is_action_pressed(action): return true
	return false
