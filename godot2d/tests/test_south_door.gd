extends SceneTree
const Room = preload("res://scripts/room_data.gd")
var failures := 0

func _initialize() -> void:
	call_deferred("run")

func check(id: String, valid: bool) -> void:
	print(("PASS " if valid else "FAIL ") + id)
	if not valid: failures += 1

func run() -> void:
	var scene = load("res://scenes/harbor.tscn").instantiate()
	scene.set_meta("journal_test", true)
	scene.set_meta("save_directory", "/private/tmp/coastal-south-test-" + str(Time.get_ticks_usec()))
	root.add_child(scene)
	await process_frame
	check("south_edge", Room.DOOR == Vector2(320, Room.FLOOR.end.y))
	check("south_spawn", Room.SPAWN == Vector2(320, 288))
	scene.home.switch_room("house", Vector2.ZERO)
	var door = scene.home.active_door()
	check("inside_up", door.entrance_normal == Vector2.UP)
	check("north_wall_closed", Room.blockers().has(Rect2(160, 96, 320, 32)))
	check("south_walls_open_center", Room.blockers().has(Rect2(176, 320, 124, 16)) and Room.blockers().has(Rect2(340, 320, 124, 16)))
	for depth in [0, 16, 32, 56]:
		for lateral in [-24, 0, 24]:
			check("inside_range_%d_%d" % [depth, lateral], door.can_interact(door.position + door.entrance_normal * depth + Vector2(lateral, 0)))
	check("inside_back_rejected", not door.can_interact(door.position - door.entrance_normal))
	check("old_north_save_fallback", scene.home.safe_position("house", Vector2(320, 128)) == Room.SPAWN)
	check("old_legal_save_preserved", scene.home.safe_position("house", Vector2(320, 240)) == Vector2(320, 240))
	check("near_south_legal_save_preserved", scene.home.safe_position("house", Vector2(320, 300)) == Vector2(320, 300))
	check("south_door_save_fallback", scene.home.safe_position("house", Vector2(320, 320)) == Room.SPAWN)
	check("new_safe_point", scene.home.safe_position("house", Room.SPAWN) == Room.SPAWN)
	var player = scene.player
	player.position = Vector2(320, 304)
	var closed_hit = player.move_and_collide(Vector2(0, 32))
	check("closed_leaf_blocks_center", closed_hit != null and player.position.y < 320)
	var jamb_body = door.get_node_or_null("JambCollision")
	check("fixed_jamb_body", jamb_body is StaticBody2D and jamb_body != door.body)
	if jamb_body is StaticBody2D:
		check("two_fixed_jambs", jamb_body.get_child_count() == 2)
		door.set_pose(2)
		await physics_frame
		await physics_frame
		check("jambs_remain_solid", jamb_body.get_children().all(func(child): return child is CollisionShape2D and not child.disabled))
		check("open_leaf_clear", door.collision.disabled)
		player.position = Vector2(320, 304)
		check("open_center_walkable", player.move_and_collide(Vector2(0, 32)) == null and player.position.y > 330)
		for lateral in [-12, 12]:
			player.position = Vector2(320 + lateral, 304)
			var hit = player.move_and_collide(Vector2(0, 32))
			check("open_jamb_blocks_%d" % lateral, hit != null and player.position.y < 320)
	scene.home.switch_room("harbor", Vector2.ZERO)
	door = scene.home.active_door()
	check("outside_down", door.entrance_normal == Vector2.DOWN)
	for depth in [0, 16, 32, 56]:
		for lateral in [-24, 0, 24]:
			check("outside_range_%d_%d" % [depth, lateral], door.can_interact(door.position + door.entrance_normal * depth + Vector2(lateral, 0)))
	check("outside_back_rejected", not door.can_interact(door.position - door.entrance_normal))
	player.position = door.position + door.entrance_normal * 24
	var outside_closed_hit = player.move_and_collide(-door.entrance_normal * 36)
	check("outside_closed_leaf_blocks", outside_closed_hit != null and outside_closed_hit.get_collider() == door.body)
	var outside_jambs = door.get_node_or_null("JambCollision")
	check("outside_fixed_jambs", outside_jambs is StaticBody2D and outside_jambs.get_child_count() == 2)
	door.set_pose(2)
	await physics_frame
	await physics_frame
	player.position = door.position + door.entrance_normal * 24
	check("outside_open_center_walkable", player.move_and_collide(-door.entrance_normal * 36) == null)
	for lateral in [-8, 8]:
		player.position = door.position + door.entrance_normal * 24 + Vector2(lateral, 0)
		var outside_jamb_hit = player.move_and_collide(-door.entrance_normal * 36)
		check("outside_open_jamb_blocks_%d" % lateral, outside_jamb_hit != null and outside_jamb_hit.get_collider() == outside_jambs)
	if DisplayServer.get_name() != "headless": await check_registered_leaf_render()
	print("SOUTH_DOOR failures=", failures)
	scene.queue_free()
	quit(1 if failures else 0)

func check_registered_leaf_render() -> void:
	var viewport := SubViewport.new()
	viewport.size = Vector2i(96, 96)
	viewport.transparent_bg = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var leaf = Node2D.new()
	leaf.set_script(preload("res://scripts/interactive_door.gd"))
	leaf.inside = true
	leaf.position = Vector2(48, 48)
	viewport.add_child(leaf)
	await process_frame
	await RenderingServer.frame_post_draw
	var before: Color = viewport.get_texture().get_image().get_pixel(48, 44)
	var image := Image.create(30, 59, false, Image.FORMAT_RGBA8)
	image.fill(Color.MAGENTA)
	leaf.pilot_frames[0] = ImageTexture.create_from_image(image)
	leaf.queue_redraw()
	await process_frame
	await RenderingServer.frame_post_draw
	var after: Color = viewport.get_texture().get_image().get_pixel(48, 44)
	check("registered_leaf_texture_used", before != after and after.r > 0.8 and after.b > 0.8 and after.g < 0.3)
	leaf.pilot_frames[0] = preload("res://assets/house-interior/door-closed.png")
	if OS.get_cmdline_user_args().has("--capture-door-poses"):
		for pose in [0, 1, 2]:
			leaf.set_pose(pose)
			await process_frame
			await RenderingServer.frame_post_draw
			var path := "/private/tmp/coastal-south-door-pose-%d.png" % pose
			check("capture_pose_%d" % pose, viewport.get_texture().get_image().save_png(path) == OK)
	viewport.queue_free()
