extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
var s=Support.new()
func _initialize():
	for id in ["clam","snail","kelp"]:
		var path="res://assets/visual-polish-v6/"+id+".png"
		s.check("sea_exists_"+id,ResourceLoader.exists(path))
		if ResourceLoader.exists(path):
			var tex=load(path)
			s.check("sea_detail_"+id,tex.get_size()==Vector2(64,64))
	var exterior=load("res://scenes/world/harbor_exterior.tscn").instantiate()
	for name in ["DaisiesWest","GoldFlowers","PinkFlowers","FlowerEdge"]:
		var node=exterior.get_node_or_null("DepthSortedObjects/"+name)
		s.check("flower_node_"+name,node!=null)
		if node==null:continue
		s.check("flower_source_"+name,node.texture.resource_path.begins_with("res://assets/flowers-v7/48/"))
		s.check("flower_pixel_scale_"+name,node.texture.get_size()==Vector2(48,42) and (node.texture.get_size()*node.scale).is_equal_approx(Vector2(16,14)))
		var image:Image=node.texture.get_image()
		var transparent:=0
		for y in range(image.get_height()):
			for x in range(image.get_width()):
				if image.get_pixel(x,y).a<0.5:transparent+=1
		s.check("flower_no_plate_"+name,transparent>image.get_width()*image.get_height()*0.35)
		s.check("flower_clear_corners_"+name,image.get_pixel(0,0).a==0 and image.get_pixel(image.get_width()-1,image.get_height()-1).a==0)
	exterior.free()
	print("SPRITE_CONSISTENCY ",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
