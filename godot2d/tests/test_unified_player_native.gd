extends "res://tests/test_life_farming_native.gd"
var frame_number:=0
func run() -> void:
	evidence="/private/tmp/coastal-unified-native"
	DirAccess.make_dir_recursive_absolute(evidence)
	w=load("res://scenes/harbor.tscn").instantiate()
	root.add_child(w)
	check("native",DisplayServer.get_name()!="headless")
	w.start_new_game("动作验收")
	for i in range(4): await process_frame
	w.player.position=Vector2(124,244)
	for i in range(3):await process_frame
	# Actual Shift input changes both movement speed and animation selection.
	await key(KEY_D,true)
	for i in range(4):await physics_frame
	check("walk_animation",w.player.sprite.animation=="east" and is_equal_approx(w.player.velocity.length(),72))
	await key(KEY_SHIFT,true)
	for i in range(4):await physics_frame
	check("run_animation",w.player.sprite.animation=="run_east" and is_equal_approx(w.player.velocity.length(),108))
	await key(KEY_SHIFT,false)
	await key(KEY_D,false)
	for i in range(3):await physics_frame
	check("run_release_idle",not w.player.running and w.player.velocity==Vector2.ZERO)
	# Fixed-foot native preview: render every authored image, without transforming it.
	w.player.position=Vector2(124,244)
	w.player.set_physics_process(false)
	for i in range(3):await process_frame
	for direction in ["south","west","east","north"]:
		for action in ["walk","run","hoe","water","harvest"]:
			var id: String=direction if action=="walk" else action+"_"+direction
			w.player.sprite.stop()
			w.player.sprite.animation=id
			for f in range(6):
				w.player.sprite.frame=f
				await process_frame
				await RenderingServer.frame_post_draw
				var point: Vector2=w.player.get_canvas_transform()*w.player.global_position
				var picture:=root.get_texture().get_image().get_region(Rect2i(Vector2i(point)-Vector2i(128,224),Vector2i(256,256)))
				check("render_"+id+str(f),picture.save_png(evidence.path_join("frame-%03d.png"%frame_number))==OK)
				frame_number+=1
	w.player.set_physics_process(true)
	for direction in {"south":Vector2.DOWN,"west":Vector2.LEFT,"east":Vector2.RIGHT,"north":Vector2.UP}:
		for action in ["hoe","water","harvest"]:
			var vec: Vector2={"south":Vector2.DOWN,"west":Vector2.LEFT,"east":Vector2.RIGHT,"north":Vector2.UP}[direction]
			var point: Vector2=w.player.position
			w.player.play_tool_action(action,w.player.global_position+vec*20)
			var seen: Dictionary={}
			while w.player.action_busy:
				seen[w.player.sprite.frame]=true
				await process_frame
			check("play_all_"+action+direction,seen.size()==6 and w.player.position==point and w.player.sprite.animation==direction)
	finish()
