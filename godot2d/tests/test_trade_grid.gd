extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
var s=Support.new()
func _initialize():call_deferred("run")
func run():
	var w=load("res://scenes/harbor.tscn").instantiate()
	w.set_meta("journal_test",true)
	w.set_meta("skip_verification",true)
	w.set_meta("save_directory",s.temporary_directory("trade-grid"))
	root.add_child(w)
	w.start_new_game("图标交易")
	w.player.position=w.exterior.get_node("InteractPoints/market").position
	w.journal.show_page("trade")
	await process_frame
	var p=w.journal.get_node("Root/TradePage")
	var grid=p.get_node("Surface/Items")
	s.check("grid_18",grid.get_child_count()==18)
	s.check("six_columns",grid is GridContainer and grid.get("columns")==6)
	if grid.get_child_count()!=18 or not grid is GridContainer:
		w.queue_free();await process_frame;quit(1);return
	s.check("buy_two",grid.get_child(0).get_node("Icon").item_id=="lettuce_seed" and grid.get_child(1).get_node("Icon").item_id=="tomato_seed" and grid.get_child(2).disabled)
	p.select_direction("sell")
	await process_frame
	var ids=["clam","snail","kelp","lettuce","tomato"]
	for i in range(5):
		var icon=grid.get_child(i).get_node("Icon")
		s.check("same_item_"+ids[i],icon.item_id==ids[i])
		if i<3:s.check("same_draw_"+ids[i],icon.get_node("Forage").get_script().resource_path=="res://scripts/forage_pickup.gd" and icon.get_node("Forage").kind==ids[i])
		else:s.check("same_texture_"+ids[i],icon.crop_texture().resource_path=="res://assets/farming-polish-v3/"+ids[i]+"_mature.png")
	for i in range(5,18):s.check("empty_"+str(i),grid.get_child(i).visible and grid.get_child(i).disabled and grid.get_child(i).get_node("Icon").item_id=="")
	p.select_item("lettuce")
	s.check("missing_disables_submit",p.get_node("Surface/Submit").disabled)
	p.select_direction("buy")
	p.get_node("Surface/Plus").pressed.emit()
	s.check("plus_updates_total",p.get_node("Surface/Quantity").value==2 and p.get_node("Surface/Total").text.contains("10"))
	p.get_node("Surface/Minus").pressed.emit()
	s.check("minus_updates_total",p.get_node("Surface/Quantity").value==1 and p.get_node("Surface/Total").text.contains("5"))
	w.queue_free();await process_frame
	print("TRADE_GRID ",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
