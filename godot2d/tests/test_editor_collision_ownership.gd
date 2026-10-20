extends SceneTree

const EXTERIOR = preload("res://scenes/world/harbor_exterior.tscn")
const EXPECTED = {
	"BoundaryTop": [Vector2(320, 0), Vector2(704, 64)],
	"BoundaryLeft": [Vector2(-8, 224), Vector2(48, 448)],
	"BoundaryRight": [Vector2(648, 224), Vector2(48, 448)],
	"HouseWest": [Vector2(144, 156), Vector2(104, 60)],
	"HouseMiddle": [Vector2(239, 156), Vector2(34, 60)],
	"HouseLintel": [Vector2(209, 130), Vector2(26, 8)],
	"MarketBlocker": [Vector2(442, 204.5), Vector2(128, 27)],
	"CrateBlocker": [Vector2(521.5, 225), Vector2(23, 16)],
	"TreeBlocker0": [Vector2(46, 128), Vector2(10, 8)],
	"TreeBlocker1": [Vector2(308, 110), Vector2(10, 8)],
	"TreeBlocker2": [Vector2(568, 184), Vector2(10, 8)],
	"TreeBlocker3": [Vector2(614, 114), Vector2(10, 8)],
	"TreeBlocker4": [Vector2(40, 225), Vector2(10, 8)],
	"WaterWest": [Vector2(136, 294.5), Vector2(272, 45)],
	"WaterWestBeach": [Vector2(112, 382.5), Vector2(224, 131)],
	"WaterStepsRight": [Vector2(364, 294.5), Vector2(88, 45)],
	"WaterBeachRight": [Vector2(388, 382.5), Vector2(40, 131)],
	"WaterEast": [Vector2(556, 360), Vector2(168, 176)],
	"WaterBeachEnd": [Vector2(296, 408), Vector2(144, 80)],
	"WaterPierEnd": [Vector2(440, 420), Vector2(64, 56)],
}
var failures := 0
var count := 0

func _initialize() -> void:
	call_deferred("run")

func check(label: String, passed: bool) -> void:
	count += 1
	if not passed:
		failures += 1
	print(("PASS " if passed else "FAIL ") + label)

func blocked(world: Node2D, point: Vector2) -> bool:
	var query := PhysicsPointQueryParameters2D.new()
	query.position = world.to_global(point)
	return not world.get_world_2d().direct_space_state.intersect_point(query).is_empty()

func capture(name: String) -> void:
	if DisplayServer.get_name() == "headless":
		return
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("/private/tmp/coastal-editor-i1/" + name + ".png")

func run() -> void:
	debug_collisions_hint = true
	root.canvas_transform = Transform2D(0.0, Vector2(2, 2), 0.0, Vector2.ZERO)
	var baseline := EXTERIOR.instantiate()
	root.add_child(baseline)
	await physics_frame
	await physics_frame
	var found := 0
	for body in baseline.find_children("*", "StaticBody2D", true, false):
		var key := String(body.name)
		if key == "Base" and String(body.get_parent().name).begins_with("CoastalTree"):
			key = "TreeBlocker" + String(body.get_parent().name).trim_prefix("CoastalTree")
		if not EXPECTED.has(key):
			continue
		found += 1
		var shape: CollisionShape2D = body.get_node("CollisionShape2D")
		check("default_geometry_" + body.name, baseline.to_local(shape.global_position).is_equal_approx(EXPECTED[key][0]) and shape.shape.size == EXPECTED[key][1])
	check("default_collision_count", found == EXPECTED.size())
	await capture("default")
	baseline.free()
	var world := EXTERIOR.instantiate()
	var tree: Node2D = world.get_node("DepthSortedObjects/CoastalTree0")
	var crates: Node2D = world.get_node("DepthSortedObjects/Crates")
	tree.position = Vector2(320, 240)
	crates.position = Vector2(560, 245)
	check("tree_owns_base_before_ready", not tree.find_children("*", "StaticBody2D", true, false).is_empty())
	check("prop_owns_base_before_ready", not crates.find_children("*", "StaticBody2D", true, false).is_empty())
	root.add_child(world)
	await physics_frame
	await physics_frame
	for item in [["tree", Vector2(46,128), Vector2(320,240)], ["crates", Vector2(521.5,225), Vector2(558.5,237)]]:
		check(item[0] + "_new_physics", blocked(world, item[2]))
		check(item[0] + "_old_physics_clear", not blocked(world, item[1]))
		check(item[0] + "_new_save_rejected", world.safe_position(item[2]) == world.spawn_point())
		check(item[0] + "_old_save_allowed", world.safe_position(item[1]) == item[1])
	check("tree_shadow_follows", world.get_node("Terrain/TreeShadows/CoastalTree0Shadow").global_position == tree.global_position)
	check("house_sort_origin_preserved", world.get_node("DepthSortedObjects/House").position.y == 165)
	await capture("moved")
	world.free()
	print("I1 RESULT %d/%d" % [count - failures, count])
	quit(0 if failures == 0 else 1)
