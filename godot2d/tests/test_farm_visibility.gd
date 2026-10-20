extends SceneTree
func _initialize() -> void:
	var world=load("res://scenes/world/harbor_exterior.tscn").instantiate()
	root.add_child(world)
	var passed:=true
	for garden_name in ["GardenA","GardenB"]:
		var garden=world.get_node("DepthSortedObjects/"+garden_name)
		var field=Rect2(garden.global_position+Vector2(-32,-32),Vector2(64,32))
		for i in range(5):
			var tree=world.get_node("DepthSortedObjects/CoastalTree"+str(i))
			var sprite: Sprite2D=tree.get_node("Sprite2D")
			var bounds: Rect2=sprite.global_transform*sprite.get_rect()
			var clear:=not bounds.intersects(field)
			print(("PASS " if clear else "FAIL ")+garden_name+"_tree_"+str(i))
			passed=passed and clear
	world.queue_free()
	quit(0 if passed else 1)
