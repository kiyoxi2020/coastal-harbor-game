extends Node
signal phase_changed(phase: String)
var home
var busy := false
var phase := "Idle"
var stable_snapshot: Dictionary = {}
var exit_pending := false
var fade: ColorRect
var clipping_door
const APERTURE_DEPTH:=16.0
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
	var alignment:=Vector2(door.position.x,world.player.position.y)
	if not path_clear(world.player.position,alignment,door): return false
	if not path_clear(alignment,door.position+door.entrance_normal*8,door): return false
	stable_snapshot=world.foraging.to_data(home.safe_position(world.foraging.location,world.player.position))
	busy=true
	world.hud.dismiss()
	world.player.velocity=Vector2.ZERO
	world.player.reset_doorway_visual()
	world.release_input=true
	run.call_deferred()
	return true
func pause_for(seconds: float) -> void:
	await get_tree().create_timer(seconds,false).timeout
func path_clear(from: Vector2,to: Vector2,door) -> bool:
	var query:=PhysicsShapeQueryParameters2D.new()
	var shape:=RectangleShape2D.new()
	shape.size=Vector2(10,6)
	query.shape=shape
	query.transform=Transform2D(0,from)
	query.motion=to-from
	query.exclude=[home.world.player.get_rid(),door.body.get_rid()]
	var space=home.world.player.get_world_2d().direct_space_state
	if not space.intersect_shape(query,1).is_empty(): return false
	var result: PackedFloat32Array=space.cast_motion(query)
	return result[0]>=0.999
func walk_to(point: Vector2) -> bool:
	# Physics moves at SPEED (72 units/s); duration follows distance, never a tween.
	var player=home.world.player
	var delta: Vector2=point-player.position
	player.facing="south" if delta.y>=0 else "north"
	if absf(delta.x)>absf(delta.y): player.facing="east" if delta.x>0 else "west"
	player.sprite.play(player.facing)
	while player.position.distance_to(point)>0.01:
		await get_tree().physics_frame
		var step: Vector2=player.position.direction_to(point)*minf(player.position.distance_to(point),player.SPEED*get_physics_process_delta_time())
		var hit=player.move_and_collide(step)
		update_clip()
		if hit:
			player.sprite.stop()
			return false
	player.position=point
	update_clip()
	player.sprite.stop()
	return true
func update_clip() -> void:
	if not is_instance_valid(clipping_door): return
	var player=home.world.player
	var depth: float=(player.position-clipping_door.position).dot(clipping_door.entrance_normal)
	# Keep the full figure on the floor. Conceal only after feet enter the aperture.
	player.set_doorway_hidden(-depth/APERTURE_DEPTH)
	# Local progressive hiding cannot cover hair above the fixed exterior awning.
	player.doorway_material.set_shader_parameter("aperture_top",clipping_door.aperture_top())
func restore_source(source: String) -> void:
	clipping_door=null
	home.switch_room(source,Vector2(stable_snapshot.position[0],stable_snapshot.position[1]))
	home.world.player.reset_doorway_visual()
	await opacity(0)
	busy=false
	home.world.release_input=true
	home.world.hud.show_toast("门前有阻挡，已回到安全位置。",6)
	set_phase("Idle")
	if exit_pending: home.world.request_exit()
func travel_duration(point: Vector2) -> float:
	return maxf(0.05,home.world.player.position.distance_to(point)/home.world.player.SPEED)
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
	var alignment:=Vector2(door.position.x,world.player.position.y)
	if not await walk_to(alignment):
		await restore_source(source)
		return
	set_phase("Opening")
	await animate_door(door,true)
	clipping_door=door
	set_phase("Crossing")
	var crossing_point: Vector2=door.position-door.entrance_normal*APERTURE_DEPTH
	if not await walk_to(crossing_point):
		await restore_source(source)
		return
	set_phase("FadeOut")
	await opacity(1)
	set_phase("Swap")
	if not home.switch_room(destination,Vector2.ZERO,true):
		await restore_source(source)
		return
	door=home.active_door()
	door.set_pose(2)
	clipping_door=door
	world.player.position=door.position-door.entrance_normal*APERTURE_DEPTH
	update_clip()
	set_phase("FadeIn")
	await opacity(0)
	set_phase("Arrival")
	if not await walk_to(door.approach):
		await restore_source(source)
		return
	clipping_door=null
	world.player.reset_doorway_visual()
	set_phase("Closing")
	await animate_door(door,false)
	world.player.velocity=Vector2.ZERO
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
