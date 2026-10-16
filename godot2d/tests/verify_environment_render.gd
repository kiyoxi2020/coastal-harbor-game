extends Node

var output_dir := "res://verification-v2"
var checks: Dictionary = {}

func _ready() -> void:
	call_deferred("run")

func snap() -> Image:
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	return get_viewport().get_texture().get_image()

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):
			output_dir = arg.trim_prefix("--output=")
	DirAccess.make_dir_recursive_absolute(output_dir)
	var scene = get_parent()
	scene.player.set_physics_process(false)
	scene.player.sprite.stop()
	scene.set_process(false)
	scene.hud.set_process(false)
	(scene.get_node("WorldCamera") as Camera2D).set_process(false)
	var water = scene.get_node("HarborExterior/Terrain/WaterDetail")
	water.set_process(false)
	var frames: Array[Image] = []
	var water_transforms: Array[Transform2D] = []
	for i in range(5):
		water.elapsed = i*0.25
		water.queue_redraw()
		var frame: Image = await snap()
		frames.append(frame)
		water_transforms.append(water.get_global_transform_with_canvas())
		if i < 4:
			frame.save_png(output_dir.path_join("water-frame-%d.png" % i))
	var land_still := true
	var changes: Array = []
	for i in range(1,5):
		var delta := 0
		var screen_to_water: Transform2D = water_transforms[i].affine_inverse()
		for y in range(frames[0].get_height()):
			for x in range(frames[0].get_width()):
				if frames[0].get_pixel(x,y) != frames[i].get_pixel(x,y):
					delta += 1
					var pixel_center := Vector2(x+0.5,y+0.5)
					if not water.contains_open_water(screen_to_water*pixel_center):
						land_still = false
		changes.append(delta)
	checks["only_open_water_changes"] = land_still
	checks["four_distinct_water_frames"] = changes[0] > 20 and changes[1] > 20 and changes[2] > 20
	checks["one_second_seamless_loop"] = changes[3] == 0
	var report := FileAccess.open(output_dir.path_join("water-render-tests.json"),FileAccess.WRITE)
	var passed := not checks.values().has(false)
	report.store_string(JSON.stringify({"passed":passed,"checks":checks,"changed_pixels_from_frame_0":changes,"scope":"unscaled viewport framebuffer pixels inverse-projected through the captured WaterDetail canvas transform; not a hardware performance benchmark"}, "\t"))
	print("WATER RENDER ",checks," changes=",changes)
	get_tree().quit(0 if passed else 1)
