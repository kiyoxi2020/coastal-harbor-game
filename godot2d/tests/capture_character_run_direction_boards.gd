extends SceneTree
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var base := ProjectSettings.globalize_path("res://../art/design/character-motion/adult-standard-v1/run-four-directions-v1")
	var output := "/private/tmp/coastal-run-directions-native"
	DirAccess.make_dir_recursive_absolute(output)
	var trial = load("res://dev/character_walk_trial.tscn").instantiate()
	trial.art_root = ProjectSettings.globalize_path("res://../art/design/character-motion/adult-standard-v1/locomotion-v1")
	root.add_child(trial)
	trial.set_physics_process(false)
	if not trial.load_run_candidate(base):
		printerr(trial.motion_error)
		quit(1)
		return
	trial.hide()
	trial.get_node("TrialUI").hide()
	trial.get_node("WorldCamera").enabled = false
	var records: Array = []
	for direction in trial.clips.run:
		for garment in ["A", "B"]:
			if not trial.has_motion_garment("run", direction, garment): continue
			var board := Node2D.new()
			root.add_child(board)
			board.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			for row in range(2):
				var bg := ColorRect.new()
				bg.position = Vector2(0, row * 720)
				bg.size = Vector2(2560, 720)
				bg.color = Color("e5e0d2" if row == 0 else "15202b")
				board.add_child(bg)
				for i in range(4):
					for factor in [1.0, 2.0]:
						var sprite := Sprite2D.new()
						sprite.texture = trial.frames[garment][trial.clips.run[direction][i]]
						sprite.centered = false
						sprite.position = Vector2(20 + i * 610 + (130 if factor == 2 else 0), row * 720 + 100)
						sprite.scale = Vector2.ONE * (138.0 / 582.0) * factor
						board.add_child(sprite)
					var reference := Sprite2D.new()
					reference.texture = trial.frames.A[trial.clips.idle[direction][0]]
					reference.centered = false
					reference.position = Vector2(440 + i * 610, row * 720 + 100)
					reference.scale = Vector2.ONE * (138.0 / 582.0)
					board.add_child(reference)
					var label := Label.new()
					label.text = "RUN 1x / RUN 2x / IDLE 1x"
					label.position = Vector2(20 + i * 610, row * 720 + 30)
					label.modulate = Color.BLACK if row == 0 else Color.WHITE
					board.add_child(label)
			for i in range(3): await process_frame
			RenderingServer.force_draw()
			var name := "board-%s-%s.png" % [direction, garment]
			var result := root.get_texture().get_image().save_png(output.path_join(name))
			if result != OK: quit(1); return
			records.append({"file": name, "sha256": FileAccess.get_sha256(output.path_join(name)), "direction": direction, "garment": garment})
			board.queue_free()
			await process_frame
	var file := FileAccess.open(output.path_join("boards.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify({"candidate_manifest_sha256": trial.run_candidate_digest, "run_garments_sha256": trial.run_garments_digest, "walk_artifact_digest": trial.artifact_digest, "script_sha256": FileAccess.get_sha256("res://tests/capture_character_run_direction_boards.gd"), "renderer": DisplayServer.get_name(), "output_px": [2560,1440], "scale": 138.0/582.0, "magnifications": [1,2], "reference": "same-direction approved A idle at 1x", "boards": records}, "  "))
	file.close()
	print("RUN_DIRECTION_BOARDS count=", records.size(), " renderer=", DisplayServer.get_name())
	trial.queue_free()
	quit(0 if DisplayServer.get_name() != "headless" else 1)
