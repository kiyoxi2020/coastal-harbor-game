extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
var t=Support.new()
func _initialize()->void:call_deferred("run")
func run()->void:
	var path="res://scenes/world/restaurant.tscn"
	t.check("restaurant_scene_exists",ResourceLoader.exists(path))
	if not ResourceLoader.exists(path):quit(1);return
	var district=load("res://scenes/world/harbor_district.tscn").instantiate()
	root.add_child(district)
	await physics_frame
	var view=district.get_node("DepthSortedObjects/Restaurant")
	for n in ["StaticArt","ClosedSign","OpenSign","MenuBoard","Smoke","Customers","InteractPoint","Base/Collision"]:
		t.check("node_"+n,view.has_node(n))
	if not view.has_method("refresh"):t.check("refresh_method",false);quit(1);return
	for status in ["closed","trial","operating"]:
		var before=var_to_str({"status":status})
		var data={"status":status}
		view.refresh(data)
		t.check("read_only_"+status,before==var_to_str(data))
		t.check("closed_sign_"+status,view.get_node("ClosedSign").visible==(status=="closed"))
		t.check("open_sign_"+status,view.get_node("OpenSign").visible==(status!="closed"))
		t.check("smoke_"+status,view.get_node("Smoke").visible==(status!="closed"))
		var count=0
		for customer in view.get_node("Customers").get_children():
			if customer.visible:count+=1
		t.check("customers_"+status,count==({"closed":0,"trial":1,"operating":2}[status]))
	for customer in view.get_node("Customers").get_children():
		t.check("customer_player_scale_"+customer.name,is_equal_approx(customer.scale.x,0.15) and is_equal_approx(customer.scale.y,0.15))
	var point:Vector2=view.get_node("InteractPoint").global_position
	t.check("original_service_point",point==Vector2(180,190))
	t.check("service_safe",district.safe_position(point)==point)
	var base:Vector2=view.get_node("Base/Collision").global_position
	view.position+=Vector2(10,0)
	await physics_frame
	t.check("marker_moves",view.get_node("InteractPoint").global_position==point+Vector2(10,0))
	t.check("base_moves",view.get_node("Base/Collision").global_position==base+Vector2(10,0))
	t.check("locations_use_instance",district.locations().filter(func(p):return p.id=="restaurant")[0].point==point+Vector2(10,0))
	var packed=PackedScene.new()
	t.check("pack_moved_scene",packed.pack(district)==OK)
	var path_saved="/private/tmp/coastal-P11-moved-district.tscn"
	t.check("save_moved_scene",ResourceSaver.save(packed,path_saved)==OK)
	var restored=load(path_saved).instantiate()
	root.add_child(restored)
	await physics_frame
	t.check("saved_marker_position",restored.get_node("DepthSortedObjects/Restaurant/InteractPoint").global_position==point+Vector2(10,0))
	t.check("saved_base_position",restored.get_node("DepthSortedObjects/Restaurant/Base/Collision").global_position==base+Vector2(10,0))
	t.check("saved_service_safe",restored.safe_position(point+Vector2(10,0))==point+Vector2(10,0))
	restored.queue_free()
	for y in range(190,391,10):t.check("lane_%d"%y,district.safe_position(Vector2(320,y))==Vector2(320,y))
	district.queue_free()
	print("RESTAURANT VIEW ",t.checks.size()," checks; passed=",t.passed())
	quit(0 if t.passed() else 1)
