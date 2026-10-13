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
	print("SOUTH_DOOR failures=", failures)
	scene.queue_free()
	quit(1 if failures else 0)
