extends SceneTree
const Support = preload("res://tests/life_test_support.gd")
var support = Support.new()
var w
var action_evidence: Dictionary={}
var evidence := "/private/tmp/coastal-grid-native"

func check(id: String, ok: bool) -> void:
	support.check(id, ok)

func _initialize() -> void: call_deferred("run")

func key(code: int, pressed: bool) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.pressed = pressed
	Input.parse_input_event(event)
	await process_frame
	await process_frame

func tap_e() -> void:
	await key(KEY_E, true)
	await key(KEY_E, false)

func click(button: Button) -> void:
	var point := button.get_global_transform_with_canvas() * (button.size / 2)
	var motion := InputEventMouseMotion.new()
	motion.position = point
	root.push_input(motion, true)
	for pressed in [true, false]:
		var event := InputEventMouseButton.new()
		event.position = point
		event.button_index = MOUSE_BUTTON_LEFT
		event.pressed = pressed
		root.push_input(event, true)
		await process_frame

func capture(name: String) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	var picture := root.get_texture().get_image()
	check("capture_" + name, picture.get_size() == Vector2i(2560,1440) and picture.save_png(evidence.path_join(name + ".png")) == OK)

func walk_to(target: Vector2, id: String) -> bool:
	# The world clears its release latch in _process, not the physics tick.
	for i in range(3): await process_frame
	for i in range(3): await physics_frame
	var deadline := Time.get_ticks_msec() + 7000
	while w.player.position.distance_to(target) > 2 and Time.get_ticks_msec() < deadline:
		var offset: Vector2 = target - w.player.position
		for action in ["left", "right", "up", "down"]: Input.action_release(action)
		if absf(offset.x) > 1.5:
			Input.action_press("right" if offset.x > 0 else "left")
		elif absf(offset.y) > 1.5:
			Input.action_press("down" if offset.y > 0 else "up")
		await physics_frame
	if w.player.position.distance_to(target) > 2:
		print("WALK_DIAGNOSTIC ", {"id":id, "position":w.player.position, "target":target, "release_input":w.release_input, "paused":paused, "velocity":w.player.velocity, "direction":Input.get_vector("left","right","up","down")})
	for action in ["left", "right", "up", "down"]: Input.action_release(action)
	for i in range(3): await physics_frame
	var reached: bool = w.player.position.distance_to(target) <= 3
	check("walk_" + id, reached)
	return reached

func pass_door(destination: String, id: String) -> bool:
	await tap_e()
	var deadline := Time.get_ticks_msec() + 8000
	while w.home.transition.busy and Time.get_ticks_msec() < deadline: await process_frame
	for i in range(3): await physics_frame
	var ok: bool = not w.home.transition.busy and w.foraging.location == destination
	check("door_" + id, ok)
	return ok

func sleep_and_return(day: int) -> bool:
	if not await walk_to(Vector2(270,244), "east_day" + str(day)): return false
	if not await walk_to(Vector2(270,194), "north_day" + str(day)): return false
	if not await walk_to(w.home.exterior_door.approach, "door_day" + str(day)): return false
	if not await pass_door("house", "enter_day" + str(day)): return false
	if not await walk_to(Vector2(320,248), "bed_row_day" + str(day)): return false
	if not await walk_to(Vector2(232,248), "bed_day" + str(day)): return false
	await tap_e()
	check("sleep_page_day" + str(day), w.journal.mode == "sleep")
	if w.journal.mode != "sleep": return false
	await click(w.journal.get_node("Root/SleepPage/Surface/Confirm"))
	check("sleep_day" + str(day), w.foraging.life.day_id == day + 1 and w.journal.mode=="daily" and paused)
	await tap_e()
	if not await walk_to(Vector2(320,248), "return_row_day" + str(day)): return false
	if not await walk_to(w.home.active_door().approach, "inside_door_day" + str(day)): return false
	if not await pass_door("harbor", "exit_day" + str(day)): return false
	if not await walk_to(Vector2(270,194), "east_return_day" + str(day)): return false
	return await walk_to(Vector2(270,244), "south_return_day" + str(day))

func cell_click(id: String) -> void:
	await process_frame
	await process_frame
	var target: Dictionary=w.farm_cell(id)
	var point: Vector2=w.player.get_canvas_transform()*target.point
	var motion := InputEventMouseMotion.new()
	motion.position=point
	root.push_input(motion,true)
	await process_frame
	for pressed in [true,false]:
		var event := InputEventMouseButton.new()
		event.position=point
		event.button_index=MOUSE_BUTTON_LEFT
		event.pressed=pressed
		root.push_input(event,true)
		await process_frame

func apply(id: String, tool_key: int, label: String) -> void:
	await key(tool_key,true)
	await key(tool_key,false)
	var seq: int=w.foraging.life.action_seq
	await cell_click(id)
	check(label,int(w.foraging.life.action_seq)==seq+1)
	if tool_key in [KEY_1,KEY_2,KEY_4]:
		var kind: String={KEY_1:"hoe",KEY_2:"water",KEY_4:"harvest"}[tool_key]
		check("animated_"+label,w.player.action_busy)
		if w.player.action_busy and not action_evidence.has(kind):
			action_evidence[kind]=true
			var foot: Vector2=w.player.position
			# Sampling must not await synchronous PNG captures during playback.
			var played_frames: Dictionary={}
			while w.player.action_busy:
				var frame: int=w.player.sprite.frame
				if not played_frames.has(frame):
					played_frames[frame]=true
				await process_frame
			check("animated_body_changes_"+kind,played_frames.size()>=4)
			check("pinned_feet_"+kind,w.player.position==foot)
		while w.player.action_busy: await process_frame

func run() -> void:
	DirAccess.make_dir_recursive_absolute(evidence)
	w=load("res://scenes/harbor.tscn").instantiate()
	root.add_child(w)
	check("native_renderer",DisplayServer.get_name()!="headless")
	check("start",w.start_new_game("园丁"))
	# P06 market UI is outside P05: seed the native fixture via real P03 purchases,
	# preserving finite cash/stock and saving each successful transaction.
	for item in ["lettuce_seed","tomato_seed"]:
		var purchase: Dictionary=w.action_service.execute(w.foraging,w.player.position,"trade",{"direction":"buy","account_id":"market","item_id":item,"amount":1},int(w.foraging.life.action_seq)+1)
		check("fixture_purchase_"+item,purchase.ok)
		if purchase.ok: w._set_state(purchase.next_state)
	for i in range(4): await process_frame
	await capture("01-background-and-empty-grid")
	var previous: String=w.get_node("FarmTools").tool
	await key(KEY_TAB,true)
	await key(KEY_TAB,false)
	check("tab_cycles_no_journal",w.get_node("FarmTools").tool!=previous and w.journal.mode=="")
	check("outside_stack_removed",not w.sort_layer.has_node("StorageCrates"))
	check("road_not_cultivable",not w.exterior.can_cultivate(Vector2(296,200)))
	# UI clicks select tools only and must not execute a soil command underneath.
	var seq: int=w.foraging.life.action_seq
	await click(w.get_node("FarmTools/Panel/Tools/Water"))
	check("toolbar_click_no_world_action",w.foraging.life.action_seq==seq)
	# Walk through all sixteen centers using actual movement and crop-free collision.
	if not await walk_to(Vector2(270,244),"farm_approach"): finish(); return
	for id in preload("res://scripts/simulation/state_schema.gd").cell_ids():
		if not await walk_to(w.farm_cell(id).point,id): finish(); return
		await apply(id,KEY_1,"hoe_"+id)
	await capture("02-sixteen-tilled-cells")
	if not await walk_to(w.farm_cell("garden_a:0:0").point,"mixed_plant"): finish(); return
	await apply("garden_a:0:0",KEY_2,"prewater_lettuce")
	await key(KEY_3,true)
	await key(KEY_3,false)
	await click(w.get_node("FarmTools/Panel/Seeds/Lettuce"))
	await cell_click("garden_a:0:0")
	while w.player.action_busy: await process_frame
	check("lettuce_planted_wet",w.foraging.life.plots["garden_a:0:0"].crop_id=="lettuce" and w.foraging.life.plots["garden_a:0:0"].watered)
	await key(KEY_3,true)
	await key(KEY_3,false)
	await click(w.get_node("FarmTools/Panel/Seeds/Tomato"))
	await cell_click("garden_a:1:0")
	while w.player.action_busy: await process_frame
	await apply("garden_a:1:0",KEY_2,"water_tomato")
	await capture("03-mixed-seeds-wet-soil")
	# E facing target: face south from the upper row and water the empty lower cell.
	if not await walk_to(w.farm_cell("garden_a:0:0").point,"keyboard_cell"): finish(); return
	await key(KEY_S,true)
	await physics_frame
	await physics_frame
	await key(KEY_S,false)
	await key(KEY_2,true)
	await key(KEY_2,false)
	seq=w.foraging.life.action_seq
	var facing_target: Dictionary=w.farm_target(false)
	await tap_e()
	if w.foraging.life.action_seq!=seq+1: print("E_DIAGNOSTIC ",{"position":w.player.position,"facing":w.player.facing,"target":facing_target,"mouse_mode":w.get_node("FarmTools").mouse_target,"note":w.journal.note})
	check("E_uses_facing_cell_without_modal",w.journal.mode=="" and w.foraging.life.action_seq==seq+1 and w.foraging.life.plots["garden_a:0:1"].watered)
	for day in range(1,5):
		if not await sleep_and_return(day): finish(); return
		if not await walk_to(w.farm_cell("garden_a:0:0").point,"return_crop_day"+str(day)): finish(); return
		if day==1: await capture("04-sprouts")
		if day==2:
			await capture("05-lettuce-mature")
			await apply("garden_a:0:0",KEY_4,"harvest_lettuce")
			check("lettuce_yield",w.foraging.bag.count_item("lettuce")==3)
		if day<4:
			if day==1: await apply("garden_a:0:0",KEY_2,"water_lettuce_day2")
			await apply("garden_a:1:0",KEY_2,"water_tomato_day"+str(day+1))
		if day==3: await capture("06-young-tomato")
	await capture("07-tomato-mature")
	await apply("garden_a:1:0",KEY_4,"harvest_tomato")
	check("tomato_yield",w.foraging.bag.count_item("tomato")==3)
	await capture("08-harvested-tilled-soil")
	var before: Dictionary=w.foraging.to_data(w.player.position)
	check("reload",w.continue_game() and preload("res://scripts/simulation/life_rules.gd")._same_payload(w.foraging.life,before.life) and w.foraging.bag.snapshot()==before.bag)
	finish()

func finish() -> void:
	var file:=FileAccess.open(evidence.path_join("checks.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(support.checks,"  "))
	file.close()
	print("GRID_NATIVE checks=",support.checks.size()," passed=",support.passed())
	quit(0 if support.passed() else 1)
