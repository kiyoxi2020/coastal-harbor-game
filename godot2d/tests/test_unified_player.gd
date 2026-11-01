extends SceneTree
const Support = preload("res://tests/life_test_support.gd")
const FRAMES_PATH := "res://resources/player_body_frames.tres"
const MANIFEST_PATH := "res://assets/characters/integrations/adult-standard-v2-visible-r001/manifest.json"
const DIRECTIONS := {"south":Vector2.DOWN,"west":Vector2.LEFT,"east":Vector2.RIGHT,"north":Vector2.UP}
class WorldStub:
	extends Node
	var release_input := true
	var home: Node
var s := Support.new()

func _initialize() -> void: call_deferred("run")

func duration(sprite: AnimatedSprite2D, animation: String) -> float:
	var frames := sprite.sprite_frames
	var seconds := 0.0
	for i in range(frames.get_frame_count(animation)):
		seconds += frames.get_frame_duration(animation, i) / frames.get_animation_speed(animation)
	return seconds

func rgba_sha256(texture: Texture2D) -> String:
	var image := texture.get_image()
	image.convert(Image.FORMAT_RGBA8)
	var digest := HashingContext.new()
	digest.start(HashingContext.HASH_SHA256)
	digest.update(image.get_data())
	return digest.finish().hex_encode()

func save_snapshot(directory: String) -> Dictionary:
	var result := {}
	for filename in DirAccess.get_files_at(directory):
		result[filename] = FileAccess.get_file_as_bytes(directory.path_join(filename))
	return result

func check_gameplay_preflight() -> void:
	var w = load("res://scenes/harbor.tscn").instantiate()
	w.set_meta("journal_test", true)
	w.set_meta("skip_verification", true)
	w.set_meta("save_directory", s.temporary_directory("body-tool-preflight"))
	root.add_child(w)
	s.check("preflight_save_isolated", w.save_service.directory.begins_with("/private/tmp/coastal-"))
	if not w.save_service.directory.begins_with("/private/tmp/coastal-"):
		w.queue_free()
		return
	s.check("preflight_new_game", w.start_new_game("动画预检"))
	await process_frame
	w.release_input = false
	w.player.set_physics_process(false)
	var target: Dictionary = w.farm_cell("garden_a:0:0")
	w.player.global_position = target.point - Vector2.DOWN * 12
	w.player.facing = "east"
	w.get_node("FarmTools").tool = "hoe"
	s.check("preflight_real_cell_reachable", w._can_perform_action("hoe", {"cell_id":target.id}))
	var complete_frames: SpriteFrames = w.player.sprite.sprite_frames
	var fixture: Dictionary = w.foraging.to_data(w.player.position).duplicate(true)
	for invalid in ["missing", "empty", "loop", "null_frame"]:
		var fresh = preload("res://scripts/player_state.gd").new()
		s.check("preflight_"+invalid+"_fixture_restores", fresh.restore(fixture))
		w._set_state(fresh)
		w.player.facing = "east"
		var broken: SpriteFrames = complete_frames.duplicate()
		match invalid:
			"missing": broken.remove_animation("hoe_south")
			"empty": broken.clear("hoe_south")
			"loop": broken.set_animation_loop("hoe_south", true)
			"null_frame": broken.set_frame("hoe_south", 0, null)
		w.player.sprite.sprite_frames = broken
		var before: Dictionary = w.foraging.to_data(w.player.position).duplicate(true)
		var saved := save_snapshot(w.save_service.directory)
		w.use_farm_tool(target)
		s.check("gameplay_"+invalid+"_no_state_commit", w.foraging.to_data(w.player.position) == before)
		s.check("gameplay_"+invalid+"_no_save_commit", save_snapshot(w.save_service.directory) == saved)
		s.check("gameplay_"+invalid+"_no_action_lock", not w.player.action_busy and w.player.facing == "east")
		w.player.get_node("ToolAction").finish()
	# A valid animation must still commit exactly one real transaction.
	var fresh = preload("res://scripts/player_state.gd").new()
	s.check("preflight_valid_fixture_restores", fresh.restore(fixture))
	w._set_state(fresh)
	w.player.sprite.sprite_frames = complete_frames
	var seq: int = w.foraging.life.action_seq
	w.use_farm_tool(target)
	s.check("gameplay_valid_commits_once", w.foraging.life.action_seq == seq+1 and w.foraging.life.plots[target.id].tilled and w.player.action_busy)
	var committed: Dictionary = w.foraging.to_data(w.player.position).duplicate(true)
	var committed_save := save_snapshot(w.save_service.directory)
	w.player.get_node("ToolAction").finish()
	w.player.get_node("ToolAction")._animation_finished()
	s.check("gameplay_animation_finish_no_second_commit", w.foraging.to_data(w.player.position) == committed and save_snapshot(w.save_service.directory) == committed_save)
	w.queue_free()
	await process_frame

func run() -> void:
	for action in ["left","right","up","down","run"]:
		if not InputMap.has_action(action): InputMap.add_action(action)
	var player = load("res://scenes/actors/player.tscn").instantiate()
	root.add_child(player)
	player.set_physics_process(false)
	var frames: SpriteFrames = player.sprite.sprite_frames
	s.check("body_frames_bound", frames.resource_path == FRAMES_PATH)
	s.check("one_character_renderer", not player.has_node("ToolAction/Pose"))
	s.check("registered_geometry", not player.sprite.centered and player.sprite.offset == Vector2(-123,-201) and player.sprite.position == Vector2.ZERO and player.sprite.scale == Vector2(0.25,0.25))
	s.check("collision_unchanged", player.get_node("CollisionShape2D").shape.size == Vector2(10,6))
	s.check("independent_idle_api", player.has_method("play_idle"))
	s.check("startup_idle", player.sprite.animation == "idle_south")
	var packed := PackedScene.new()
	s.check("player_scene_packs", packed.pack(player) == OK)
	var restored = packed.instantiate()
	var restored_sprite: AnimatedSprite2D = restored.get_node("AnimatedSprite2D")
	s.check("inspector_geometry_survives_pack", restored_sprite.sprite_frames == frames and restored_sprite.position == player.sprite.position and restored_sprite.scale == player.sprite.scale and restored_sprite.centered == player.sprite.centered and restored_sprite.offset == player.sprite.offset)
	restored.free()
	var measured_top := 0.0
	var measured_bottom := 0.0
	for direction in DIRECTIONS:
		for action in ["idle", "walk"]:
			var id: String = action+"_"+direction
			if not frames.has_animation(id): continue
			for i in range(frames.get_frame_count(id)):
				var texture := frames.get_frame_texture(id,i)
				var bounds := texture.get_image().get_used_rect()
				measured_top = minf(measured_top, (bounds.position.y - 201) * 0.25)
				measured_bottom = maxf(measured_bottom, (bounds.end.y - 201) * 0.25)
	s.check("door_bounds_use_registered_origin", is_equal_approx(player.visual_top, measured_top) and is_equal_approx(player.visual_bottom, measured_bottom))
	if FileAccess.file_exists(MANIFEST_PATH):
		var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST_PATH))
		s.check("complete_24_clips", manifest.clips.size() == 24 and frames.get_animation_names().size() == 24)
		var total := 0
		for clip in manifest.clips:
			var id: String = clip.name
			s.check(id+"_frames", frames.has_animation(id) and frames.get_frame_count(id) == clip.frames.size())
			if not frames.has_animation(id): continue
			s.check(id+"_loop", frames.get_animation_loop(id) == clip.loop)
			for i in range(mini(frames.get_frame_count(id), clip.frames.size())):
				var texture: Texture2D = frames.get_frame_texture(id, i)
				s.check(id+"_source_"+str(i), texture.resource_path == clip.frames[i].texture and texture.get_size() == Vector2(256,224))
				s.check(id+"_imported_rgba_"+str(i), rgba_sha256(texture) == clip.frames[i].get("rgba_sha256", ""))
				s.check(id+"_duration_"+str(i), is_equal_approx(frames.get_frame_duration(id,i) / frames.get_animation_speed(id) * 1000.0, float(clip.frames[i].duration_ms)))
				total += 1
		s.check("108_actual_frames", total == 108)
		var reference: Dictionary = manifest.clips[0].frames[0]
		var original: Texture2D = load(reference.texture)
		var changed := original.get_image().duplicate() as Image
		changed.convert(Image.FORMAT_RGBA8)
		var pixel := changed.get_pixel(0,0)
		changed.set_pixel(0,0, Color(1.0-pixel.r,pixel.g,pixel.b,1.0-pixel.a))
		s.check("changed_imported_image_rejected", rgba_sha256(ImageTexture.create_from_image(changed)) != reference.get("rgba_sha256", "") and rgba_sha256(original) == reference.get("rgba_sha256", ""))
	else:
		s.check("integration_manifest_exists", false)
	# Unknown or missing actions must not lock input or change facing.
	var tool = player.get_node("ToolAction")
	var saved_frames: SpriteFrames = frames
	player.sprite.sprite_frames = frames.duplicate()
	player.sprite.sprite_frames.remove_animation("hoe_south")
	player.facing = "east"
	player.play_tool_action("hoe", player.position + Vector2.DOWN * 20)
	s.check("missing_action_fails_closed", not player.action_busy and player.facing == "east")
	tool.finish()
	player.sprite.sprite_frames.add_animation("hoe_south")
	player.play_tool_action("hoe", player.position + Vector2.DOWN * 20)
	s.check("empty_action_fails_closed", not player.action_busy and player.facing == "east")
	player.sprite.sprite_frames = saved_frames
	if player.has_method("play_idle"): player.play_idle()
	var point: Vector2 = player.position
	for direction in DIRECTIONS:
		for action in ["hoe","water","harvest"]:
			var id: String = action+"_"+direction
			player.play_tool_action(action, player.global_position + DIRECTIONS[direction] * 20)
			s.check(id+"_start", player.action_busy and player.sprite.animation == id and player.sprite.is_playing() and player.sprite.frame == 0)
			Input.action_press("left")
			player._physics_process(0.016)
			Input.action_release("left")
			s.check(id+"_locked", player.facing == direction and player.velocity == Vector2.ZERO and player.position == point)
			var wait_time := duration(player.sprite,id) if frames.has_animation(id) else 0.1
			await create_timer(wait_time + 0.12).timeout
			s.check(id+"_finish_idle", not player.action_busy and player.sprite.animation == "idle_"+direction and player.position == point)
			player.play_tool_action(action, player.global_position + DIRECTIONS[direction] * 20)
			s.check(id+"_replay_zero", player.action_busy and player.sprite.frame == 0 and is_zero_approx(player.sprite.frame_progress))
			tool.finish()
			var idle_animation: StringName = player.sprite.animation
			tool._animation_finished()
			s.check(id+"_finish_once", not player.action_busy and player.sprite.animation == idle_animation)
	var world := WorldStub.new()
	player.world = world
	player.facing = "west"
	player.running = true
	player.walking = true
	player._physics_process(0.016)
	s.check("release_latch_idle", player.sprite.animation == "idle_west" and not player.running and not player.walking and player.velocity == Vector2.ZERO)
	world.free()
	player.queue_free()
	await process_frame
	await check_gameplay_preflight()
	print("UNIFIED_PLAYER checks=",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
