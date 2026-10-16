extends SceneTree
const Room = preload("res://scripts/room_data.gd")
var failures := 0
var transition_trace: Array[Dictionary] = []

func _initialize() -> void:
	call_deferred("run")

func check(id: String, valid: bool) -> void:
	print(("PASS " if valid else "FAIL ") + id)
	if not valid: failures += 1

func record_transition_phase(value: String, scene) -> void:
	transition_trace.append({
		"phase": value,
		"location": scene.foraging.location,
		"pose": scene.home.active_door().pose,
		"position": scene.player.position,
	})

func wait_for_transition(scene) -> void:
	var started := Time.get_ticks_msec()
	while scene.home.transition.busy and Time.get_ticks_msec() - started < 6000:
		await process_frame
	check("transition_finished_%d" % transition_trace.size(), not scene.home.transition.busy)

func trace_at(phase: String, location: String) -> Dictionary:
	for item in transition_trace:
		if item.phase == phase and item.location == location:
			return item
	return {}

func trace_index(phase: String, location: String) -> int:
	for index in transition_trace.size():
		var item := transition_trace[index]
		if item.phase == phase and item.location == location:
			return index
	return -1

func run() -> void:
	var scene = load("res://scenes/harbor.tscn").instantiate()
	scene.set_meta("journal_test", true)
	scene.set_meta("save_directory", "/private/tmp/coastal-south-test-" + str(Time.get_ticks_usec()))
	root.add_child(scene)
	await process_frame
	check("session_binds_scene_exterior", scene.home.outdoor == scene.exterior)
	check("south_edge", Room.DOOR == Vector2(320, Room.FLOOR.end.y))
	check("south_spawn", Room.SPAWN == Vector2(320, 288))
	scene.home.switch_room("house", Vector2.ZERO)
	check("house_disables_scene_exterior", not scene.exterior.visible and scene.exterior.process_mode == Node.PROCESS_MODE_DISABLED)
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
	check("harbor_restores_scene_exterior", scene.exterior.visible and scene.exterior.process_mode == Node.PROCESS_MODE_INHERIT)
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
	check("transition_test_new_game", scene.start_new_game("door order"))
	var transition = scene.home.transition
	transition.phase_changed.connect(record_transition_phase.bind(scene))
	player.position = scene.home.exterior_door.approach
	transition_trace.clear()
	check("outside_entry_begin", transition.begin())
	await wait_for_transition(scene)
	var outside_fade := trace_at("FadeOut", "harbor")
	check("outside_closes_before_fade", not outside_fade.is_empty() and outside_fade.pose == 0)
	check("outside_crosses_only_eight_units", not outside_fade.is_empty() and outside_fade.position.is_equal_approx(Room.OUTSIDE_DOOR - Room.OUTSIDE_ENTRANCE_NORMAL * 8.0))
	check("outside_entry_reaches_house", scene.foraging.location == "house")
	check("house_arrival_reaches_approach", scene.foraging.location == "house" and player.position.is_equal_approx(scene.home.interior.door.approach))
	player.position = scene.home.active_door().approach
	transition_trace.clear()
	check("inside_exit_begin", transition.begin())
	await wait_for_transition(scene)
	var outside_fade_in := trace_at("FadeIn", "harbor")
	var outside_opening := trace_at("Opening", "harbor")
	var outside_fade_in_index := trace_index("FadeIn", "harbor")
	var outside_opening_index := trace_index("Opening", "harbor")
	check("outside_arrival_starts_closed", not outside_fade_in.is_empty() and outside_fade_in.pose == 0)
	check("outside_opens_after_fade_in", not outside_opening.is_empty() and outside_opening.pose == 0 and outside_fade_in_index >= 0 and outside_opening_index > outside_fade_in_index)
	check("inside_exit_reaches_harbor", scene.foraging.location == "harbor")
	check("harbor_arrival_reaches_approach", scene.foraging.location == "harbor" and player.position.is_equal_approx(scene.home.exterior_door.approach))
	if DisplayServer.get_name() != "headless":
		await check_registered_leaf_render()
		await check_outdoor_pose_render()
		await check_scene_occlusion(scene)
	print("SOUTH_DOOR failures=", failures)
	scene.queue_free()
	quit(1 if failures else 0)

func check_registered_leaf_render() -> void:
	var viewport := SubViewport.new()
	viewport.size = Vector2i(96, 96)
	viewport.transparent_bg = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var leaf = preload("res://scenes/world/indoor_door.tscn").instantiate()
	leaf.position = Vector2(48, 48)
	viewport.add_child(leaf)
	await process_frame
	await RenderingServer.frame_post_draw
	var before: Color = viewport.get_texture().get_image().get_pixel(48, 44)
	var original_pilot: Texture2D = leaf.pilot_frames[0]
	var original_leaf: Texture2D = leaf.leaf_textures[0]
	var image := Image.create(30, 59, false, Image.FORMAT_RGBA8)
	image.fill(Color.MAGENTA)
	var replacement := ImageTexture.create_from_image(image)
	var strip := AtlasTexture.new()
	strip.atlas = replacement
	strip.region = Rect2(0, 29, 30, 8)
	leaf.pilot_frames[0] = replacement
	leaf.leaf_textures[0] = strip
	leaf.set_pose(0)
	await process_frame
	await RenderingServer.frame_post_draw
	var after: Color = viewport.get_texture().get_image().get_pixel(48, 44)
	check("registered_leaf_texture_used", before != after and after.r > 0.8 and after.b > 0.8 and after.g < 0.3)
	leaf.pilot_frames[0] = original_pilot
	leaf.leaf_textures[0] = original_leaf
	leaf.set_pose(0)
	if OS.get_cmdline_user_args().has("--capture-door-poses"):
		for pose in [0, 1, 2]:
			leaf.set_pose(pose)
			await process_frame
			await RenderingServer.frame_post_draw
			var path := "/private/tmp/coastal-south-door-pose-%d.png" % pose
			check("capture_pose_%d" % pose, viewport.get_texture().get_image().save_png(path) == OK)
	viewport.queue_free()

func check_outdoor_pose_render() -> void:
	DirAccess.make_dir_recursive_absolute("/private/tmp/coastal-south-spatial")
	var viewport := SubViewport.new()
	viewport.size = Vector2i(96, 96)
	viewport.transparent_bg = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var door = preload("res://scenes/world/outdoor_door.tscn").instantiate()
	door.position = Vector2(48, 64)
	viewport.add_child(door)
	var poses: Array[Image] = []
	for pose in [0, 1, 2]:
		door.set_pose(pose)
		await process_frame
		await RenderingServer.frame_post_draw
		var image := viewport.get_texture().get_image()
		poses.append(image.get_region(Rect2i(32, 28, 32, 40)))
		check("capture_outdoor_pose_%d" % pose,
			image.save_png("/private/tmp/coastal-south-spatial/outdoor-pose-%d.png" % pose) == OK)
	check("outdoor_pose_0_differs_from_1", poses[0].get_data() != poses[1].get_data())
	check("outdoor_pose_1_differs_from_2", poses[1].get_data() != poses[2].get_data())
	check("outdoor_open_recess_exact_rgb",
		poses[2].get_pixel(16, 21) == Color8(23, 46, 52, 255))
	viewport.queue_free()

func capture_scene(scene, id: String) -> Image:
	await process_frame
	await RenderingServer.frame_post_draw
	var rendered: Image = root.get_texture().get_image()
	rendered.save_png("/private/tmp/coastal-south-spatial/" + id + ".png")
	return rendered

func pixel_max_channel_delta(first: Color, second: Color) -> int:
	var rgb := maxf(absf(first.r - second.r), absf(first.g - second.g))
	rgb = maxf(rgb, absf(first.b - second.b))
	return roundi(maxf(rgb, absf(first.a - second.a)) * 255.0)

func source_atlas_transmission_bound() -> int:
	var image := (load("res://assets/environment.png") as Texture2D).get_image()
	var region := Rect2i(348, 383, 61, 81)
	var maximum := 0
	for y in range(region.position.y, region.end.y):
		for x in range(region.position.x, region.end.x):
			var alpha := roundi(image.get_pixel(x, y).a * 255.0)
			maximum = maxi(maximum, 255 - alpha)
	return maximum

func concealed_only_behind_atlas(first: Image, second: Image,
		without_atlas: Image, transmission_bound: int) -> bool:
	if first.get_size() != second.get_size() or first.get_size() != without_atlas.get_size():
		return false
	var exercised_transmission := false
	for y in first.get_height():
		for x in first.get_width():
			var a := first.get_pixel(x, y)
			var b := second.get_pixel(x, y)
			var delta := pixel_max_channel_delta(a, b)
			if delta == 0:
				continue
			exercised_transmission = true
			if delta > transmission_bound:
				return false
			# A nonzero actor/reference delta is allowed only where the two source-atlas
			# foreground sprites actually cover the actor. Opaque frame areas and every
			# pixel outside that measured coverage retain a zero-difference contract.
			if pixel_max_channel_delta(b, without_atlas.get_pixel(x, y)) <= transmission_bound:
				return false
	return exercised_transmission

func check_scene_occlusion(scene) -> void:
	DirAccess.make_dir_recursive_absolute("/private/tmp/coastal-south-spatial")
	scene.start_new_game("spatial test")
	scene.release_input = true
	for location in ["harbor", "house"]:
		scene.home.switch_room(location, Vector2.ZERO)
		var door = scene.home.active_door()
		scene.player.position = door.position + door.entrance_normal * 12
		scene.home.transition.busy = true
		for lateral in [-6, 0, 6]:
			check(location + "-lateral-walk-%d" % lateral, await scene.home.transition.walk_to(door.position + door.entrance_normal * 12 + Vector2(lateral, 0)))
			await capture_scene(scene, location + "-moving-scrape-%d" % lateral)
		scene.home.transition.busy = false
		if location == "harbor":
			door.set_pose(2)
			scene.player.visible = false
			var opening = await capture_scene(scene, "exterior-open-recess")
			var pixel: Vector2 = door.get_global_transform_with_canvas() * Vector2(0, -15)
			check("open_recess_is_dark_background", opening.get_pixelv(Vector2i(pixel)).is_equal_approx(Color("172e34")))
			scene.player.visible = true
		for pose in [0, 2]:
			door.set_pose(pose)
			for depth in [7, 12, 24, 40]:
				for lateral in [-8, 0, 8]:
					scene.player.position = door.position + door.entrance_normal * depth + Vector2(lateral, 0)
					scene.player.sprite.animation = "south"
					scene.player.sprite.frame = 0
					var id = "%s-pose%d-depth%d-side%d" % [location, pose, depth, lateral]
					var normal = await capture_scene(scene, id)
					# Same whole scene and same foot position: reference draws actor after trim.
					# Only sample floor depths where no legitimate foreground overlaps it.
					if depth in [7, 12, 24]:
						var garden_layers: Dictionary = {}
						if location == "harbor":
							for prop in scene.sort_layer.get_children():
								if prop.position.y == 224 and prop != scene.player:
									garden_layers[prop] = prop.z_index
									prop.z_index = 6
						scene.player.sprite.z_index = 5
						var reference = await capture_scene(scene, id + "-reference")
						scene.player.sprite.z_index = 0
						for prop in garden_layers: prop.z_index = garden_layers[prop]
						check(id + "-full-floor-silhouette", actor_region(scene, normal, location).get_data() == actor_region(scene, reference, location).get_data())
					if pose == 2 and lateral == 0 and depth == 24:
						scene.home.transition.clipping_door = door
						scene.home.transition.update_clip()
						var crossing = await capture_scene(scene, id + "-crossing")
						check(location + "-crossing-keeps-floor-silhouette", actor_region(scene, normal, location).get_data() == actor_region(scene, crossing, location).get_data())
						scene.home.transition.clipping_door = null
						scene.player.reset_doorway_visual()
		# The approved exterior route crosses only 8 units before the real leaf closes.
		# The older deep endpoint remains useful only as a negative collision boundary.
		door.set_pose(2)
		await physics_frame
		await physics_frame
		scene.player.position = door.position + door.entrance_normal * 24
		var hit = scene.player.move_and_collide(-door.entrance_normal * 100)
		print("MEASURE ", location, " physical_stop=", scene.player.position, " hit=", hit != null)
		if location == "harbor":
			check("harbor-deep-endpoint-remains-blocked", hit != null and scene.player.position.y > door.crossing_point(scene.player).y)
			scene.player.position = door.position + door.entrance_normal * 24
			scene.home.transition.busy = true
			scene.home.transition.clipping_door = null
			var shallow_target: Vector2 = door.position - door.entrance_normal * 8.0
			check("harbor-real-walk-to-shallow-crossing", await scene.home.transition.walk_to(shallow_target))
			check("harbor-shallow-crossing-position", scene.player.position.is_equal_approx(shallow_target))
			check("harbor-shallow-crossing-does-not-use-clip", scene.player.doorway_hidden == 0.0)
			var opened = await capture_scene(scene, "harbor-shallow-open")
			scene.player.visible = false
			var absent = await capture_scene(scene, "harbor-shallow-absent-reference")
			scene.player.visible = true
			check("harbor-open-shallow-keeps-player-visible",
				actor_region(scene, opened, location).get_data() != actor_region(scene, absent, location).get_data())
			door.set_pose(0)
			await process_frame
			await RenderingServer.frame_post_draw
			var closed = await capture_scene(scene, "harbor-shallow-closed")
			scene.player.visible = false
			var closed_absent = await capture_scene(scene, "harbor-shallow-closed-absent-reference")
			var house_top := scene.sort_layer.get_node("House/AtlasParts/Top") as Sprite2D
			var door_leaf := door.get_node("DoorLeaf") as Sprite2D
			house_top.visible = false
			door_leaf.visible = false
			var without_atlas = await capture_scene(scene, "harbor-shallow-closed-atlas-hidden-reference")
			house_top.visible = true
			door_leaf.visible = true
			scene.player.visible = true
			var transmission_bound := source_atlas_transmission_bound()
			check("harbor-source-atlas-transmission-bound", transmission_bound == 2)
			check("harbor-closed-before-fade-alpha-clear", scene.home.transition.fade.modulate.a == 0.0)
			check("harbor-closed-leaf-conceals-player",
				concealed_only_behind_atlas(
					actor_region(scene, closed, location),
					actor_region(scene, closed_absent, location),
					actor_region(scene, without_atlas, location), transmission_bound))
			door.set_pose(2)
			await process_frame
			var reopened = await capture_scene(scene, "harbor-shallow-reopened")
			check("harbor-reopened-leaf-reveals-player",
				actor_region(scene, reopened, location).get_data() != actor_region(scene, absent, location).get_data())
			check("harbor-real-walk-from-shallow-crossing", await scene.home.transition.walk_to(door.approach))
			scene.home.transition.busy = false
		else:
			scene.player.position = door.position + door.entrance_normal * 24
			scene.home.transition.busy = true
			scene.home.transition.clipping_door = door
			check("house-real-walk-to-hidden-endpoint", await scene.home.transition.walk_to(door.crossing_point(scene.player)))
			check("house-endpoint-hidden-progress", scene.player.doorway_hidden == 1.0)
			var hidden = await capture_scene(scene, "house-actual-endpoint")
			scene.player.visible = false
			var absent = await capture_scene(scene, "house-absent-endpoint-reference")
			check("house-actual-endpoint-has-no-player-pixels", actor_region(scene, hidden, location).get_data() == actor_region(scene, absent, location).get_data())
			scene.player.visible = true
			check("house-real-walk-from-hidden-endpoint", await scene.home.transition.walk_to(door.approach))
			scene.home.transition.clipping_door = null
			scene.home.transition.busy = false
			scene.player.reset_doorway_visual()
	for direction in ["north", "south"]:
		for frame in range(4):
			var texture: Texture2D = scene.player.sprite.sprite_frames.get_frame_texture(direction, frame)
			var bounds = texture.get_image().get_used_rect()
			var visual_top = scene.player.sprite.position.y + (bounds.position.y - texture.get_height() * 0.5) * scene.player.sprite.scale.y
			var visual_bottom = scene.player.sprite.position.y + (bounds.end.y - texture.get_height() * 0.5) * scene.player.sprite.scale.y
			print("MEASURE ", direction, frame, " visual_y=", visual_top, "..", visual_bottom)

func actor_region(scene, rendered: Image, location: String) -> Image:
	# Inspect the actor in the complete scene, excluding animated water and HUD.
	# A south threshold may cover the lowest boot pixels at depth 7, never the torso.
	var transform: Transform2D = scene.player.get_global_transform_with_canvas()
	var top: Vector2 = transform * Vector2(-24, -48)
	var bottom: Vector2 = transform * Vector2(24, -4 if location == "house" else 3)
	return rendered.get_region(Rect2i(top, bottom - top))
