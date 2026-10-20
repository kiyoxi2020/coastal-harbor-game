extends SceneTree
const Support = preload("res://tests/life_test_support.gd")
var s := Support.new()
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var w = load("res://scenes/harbor.tscn").instantiate()
	w.set_meta("skip_verification",true)
	w.set_meta("journal_test",true)
	w.set_meta("save_directory",s.temporary_directory("grid-scene"))
	root.add_child(w)
	await process_frame
	s.check("start",w.start_new_game("菜园"))
	s.check("no_hidden_starting_endowment",w.foraging.bag.count_item("lettuce_seed")==0 and w.foraging.bag.count_item("tomato_seed")==0)
	await process_frame
	await process_frame
	var a = w.sort_layer.get_node("GardenA")
	s.check("region_cell_api",a.has_method("cell_center"))
	s.check("toolbar_present",w.has_node("FarmTools"))
	s.check("no_whole_bed_blocker",not a.has_node("GardenWest"))
	if a.has_method("cell_center"):
		var p: Vector2 = a.call("cell_center","garden_a:2:1")
		s.check("target_transform",a.call("cell_at",p)=="garden_a:2:1")
		var before: Vector2 = p
		a.position += Vector2(20,0)
		s.check("region_move",a.call("cell_center","garden_a:2:1")==before+Vector2(20,0) and a.call("cell_at",before+Vector2(20,0))=="garden_a:2:1")
		a.position -= Vector2(20,0)
		w.player.global_position = p
		w.release_input = false
		var result: Dictionary = w.perform_action("hoe",{"cell_id":"garden_a:2:1"},1)
		s.check("direct_world_hoe",result.ok and w.journal.mode=="")
		var target: Vector2=a.call("cell_center","garden_a:1:1")
		w.player.global_position=target
		await process_frame
		await process_frame
		var point: Vector2=w.player.get_canvas_transform()*target
		var motion:=InputEventMouseMotion.new()
		motion.position=point
		root.push_input(motion,true)
		await process_frame
		var click:=InputEventMouseButton.new()
		click.position=point
		click.button_index=MOUSE_BUTTON_LEFT
		click.pressed=true
		root.push_input(click,true)
		await process_frame
		s.check("mouse_hoes_projected_cell",w.foraging.life.plots["garden_a:1:1"].tilled)
		var soil=a.get_node("Cell21/Soil") as Sprite2D
		s.check("soil_shared_edge",soil.material is ShaderMaterial and soil.material.get_shader_parameter("join_left"))
		var b=w.sort_layer.get_node("GardenB")
		b.region_id="garden_a"
		s.check("duplicate_region_fails_closed",w.farm_cell("garden_a:1:1").is_empty())
		b.region_id="garden_b"
		var wall:=StaticBody2D.new()
		var collision:=CollisionShape2D.new()
		var shape:=RectangleShape2D.new()
		shape.size=Vector2(3,18)
		collision.shape=shape
		wall.add_child(collision)
		w.add_child(wall)
		wall.global_position=target+Vector2(8,0)
		w.player.global_position=target+Vector2(16,0)
		await physics_frame
		await physics_frame
		s.check("no_through_wall",not w.can_reach_cell(w.farm_cell("garden_a:1:1")))
		wall.queue_free()
		await physics_frame
		w.player.global_position=target
		w.journal.show_page("bag")
		await process_frame
		await process_frame
		s.check("toolbar_hidden_while_paused",not w.get_node("FarmTools").visible)
		var snapshot: Dictionary = w.foraging.to_data(w.player.position)
		result=w.perform_action("water",{"cell_id":"garden_a:2:1"},2)
		s.check("ui_blocks_world",not result.ok and w.foraging.to_data(w.player.position)==snapshot)
		w.journal.dismiss()
		result=w.perform_action("water",{"cell_id":"garden_a:2:1"},2)
		s.check("close_release_guard",not result.ok)
		w.release_input=false
		w.player.position=Vector2(330,250)
		result=w.perform_action("hoe",{"cell_id":"garden_a:3:1"},2)
		s.check("remote_blocked",not result.ok)
	w.queue_free()
	await process_frame
	print("GRID_SCENE checks=",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
