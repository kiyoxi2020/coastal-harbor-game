extends SceneTree
func _initialize() -> void:
	call_deferred("check_scene")
func check_scene() -> void:
	assert(DisplayServer.get_name() != "headless", "Native renderer required")
	root.size = Vector2i(1280,960)
	root.content_scale_size = Vector2i(1280,960)
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	var scene = load("res://scenes/reviews/character_head_proof.tscn").instantiate()
	root.add_child(scene)
	var count = 0
	var content = scene.get_node("Scroll/Content")
	for state in ["bare", "hair", "hat", "hair_hat"]:
		for direction in ["south", "west", "east", "north"]:
			var sprite = content.get_node(state+"_"+direction)
			assert(sprite.texture != null and sprite.texture.get_size()==Vector2(512,768))
			assert(sprite.texture_filter==0)
			count += 1
	assert(scene.texture_filter==CanvasItem.TEXTURE_FILTER_NEAREST)
	# Switch the same preview actor through every baked state and direction.
	var actor = Sprite2D.new(); scene.add_child(actor)
	for state in ["bare", "hair", "hat", "hair_hat"]:
		for direction in ["south", "west", "east", "north"]:
			var expected = "res://assets/characters/adult-standard-v1/head-proof/"+state+"_"+direction+".png"
			actor.texture = load(expected)
			assert(actor.texture.resource_path==expected)
	print("HEAD_PROOF_SCENE_OK ",count," grid frames and 16 preview texture switches; no gameplay or saves")
	actor.visible = false
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute("/private/tmp/coastal-head-proof-native-scene")
	root.get_texture().get_image().save_png("/private/tmp/coastal-head-proof-native-scene/review.png")
	quit()
