extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
var s:=Support.new()
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var path:="res://resources/player_unified_frames.tres"
	s.check("unified_frames_exist",ResourceLoader.exists(path))
	if not ResourceLoader.exists(path):
		print("UNIFIED_PLAYER checks=",s.checks.size()," passed=false")
		quit(1)
		return
	var frames=load(path) as SpriteFrames
	for direction in ["south","west","east","north"]:
		for action in ["walk","run","hoe","water","harvest"]:
			var id: String=direction if action=="walk" else action+"_"+direction
			s.check(id+"_six_frames",frames.has_animation(id) and frames.get_frame_count(id)==6)
			if not frames.has_animation(id):continue
			s.check(id+"_loop",frames.get_animation_loop(id)==(action in ["walk","run"]))
			var hashes: Dictionary={}
			for i in range(frames.get_frame_count(id)):
				var texture: Texture2D=frames.get_frame_texture(id,i)
				s.check(id+"_canvas_"+str(i),texture.get_size()==Vector2(384,384))
				hashes[hash(texture.get_image().get_data())]=true
			s.check(id+"_genuine_frames",hashes.size()>=4)
	for action in ["left","right","up","down","run"]:
		if not InputMap.has_action(action):InputMap.add_action(action)
	var player=load("res://scenes/actors/player.tscn").instantiate()
	root.add_child(player)
	s.check("one_character_renderer",not player.has_node("ToolAction/Pose") and player.sprite.sprite_frames==frames)
	var point: Vector2=player.position
	for direction in {"south":Vector2.DOWN,"west":Vector2.LEFT,"east":Vector2.RIGHT,"north":Vector2.UP}:
		for action in ["hoe","water","harvest"]:
			var vector: Vector2={"south":Vector2.DOWN,"west":Vector2.LEFT,"east":Vector2.RIGHT,"north":Vector2.UP}[direction]
			player.play_tool_action(action,player.global_position+vector*20)
			s.check(action+direction+"_start",player.action_busy and player.sprite.animation==action+"_"+direction and player.sprite.is_playing())
			await create_timer(0.9).timeout
			s.check(action+direction+"_finish",not player.action_busy and player.sprite.animation==direction and player.position==point)
	player.queue_free()
	await process_frame
	print("UNIFIED_PLAYER checks=",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
