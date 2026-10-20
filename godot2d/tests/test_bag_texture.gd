extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
var s=Support.new()
func _initialize():call_deferred("run")
func run():
	var w=load("res://scenes/harbor.tscn").instantiate()
	w.set_meta("journal_test",true)
	w.set_meta("skip_verification",true)
	w.set_meta("save_directory",s.temporary_directory("bag-texture"))
	root.add_child(w)
	w.start_new_game("背包图标")
	for id in ["tomato","lettuce","tomato_seed","lettuce_seed","clam","snail","kelp"]:w.foraging.bag.add(id,6)
	w.journal.show_page("bag")
	await process_frame
	var page=w.journal.bag_page
	var grid=page.get_node("BagGrid")
	s.check("24_slots",grid.get_child_count()==24)
	var icon=grid.get_child(0).get_node("Icon")
	s.check("item_renderer",icon.get_script().resource_path=="res://scripts/ui/trade_item.gd")
	if icon.get_script().resource_path!="res://scripts/ui/trade_item.gd":
		w.queue_free();await process_frame;quit(1);return
	for i in range(7):
		var item=grid.get_child(i).get_node("Icon")
		var id:String=w.foraging.bag.snapshot()[i].id
		s.check("mapped_"+id,item.item_id==id and item.visible)
		if id in ["tomato","lettuce"]:s.check("texture_"+id,item.crop_texture().resource_path.ends_with(id+"_mature.png"))
	for i in range(7,24):s.check("empty_"+str(i),not grid.get_child(i).get_node("Icon").visible)
	s.check("slot_texture",grid.get_child(0).get_theme_stylebox("normal") is StyleBoxTexture)
	var surface=w.journal.get_node("Root/PauseMenu/Surface")
	s.check("background_texture",surface.has_node("Background"))
	s.check("button_texture",page.get_node("sort").get_theme_stylebox("normal") is StyleBoxTexture)
	w.queue_free();await process_frame
	print("BAG_TEXTURE ",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
