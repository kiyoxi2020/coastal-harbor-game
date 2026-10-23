extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
var s=Support.new()
const Service=preload("res://scripts/simulation/action_service.gd")
const Rules=preload("res://scripts/simulation/life_rules.gd")
class FailedSave extends RefCounted:
	func write_save(_data:Dictionary) -> bool:return false
func key(page,value:int,echo:bool=false):
	var event=InputEventKey.new()
	event.physical_keycode=value
	event.pressed=true
	event.echo=echo
	page.handle_key(event)
func _initialize():call_deferred("run")
func run():
	var w=load("res://scenes/harbor.tscn").instantiate()
	w.set_meta("save_directory",s.temporary_directory("P11-ui"))
	w.set_meta("journal_test",true)
	root.add_child(w)
	w.start_new_game("餐馆测试")
	s.check("restaurant_live_gate",w.has_method("can_open_restaurant"))
	if not w.has_method("can_open_restaurant"):
		w.queue_free();await process_frame;quit(1);return
	s.check("restaurant_remote_blocked",not w.perform_action("fund_restaurant",{"amount":1},1).ok)
	var page=w.journal.get_node_or_null("Root/RestaurantPage")
	s.check("restaurant_page_exists",page!=null)
	if page==null:
		w.queue_free();await process_frame;quit(1);return
	for id in ["Title","Status","Cash","Inputs","SupplyItems","Quantity","Supply","FundingAmount","FundingTotal","Fund","Open","Reasons","Close"]:
		s.check("surface_"+id,page.has_node("Surface/"+id))
	var restaurant=w.get_node_or_null("HarborDistrict/DepthSortedObjects/Restaurant")
	s.check("restaurant_world_instance",restaurant!=null and restaurant.has_node("InteractPoint"))
	if restaurant==null:
		w.queue_free();await process_frame;quit(1);return
	w.journal.dismiss()
	w.home.switch_room("harbor_district",restaurant.get_node("InteractPoint").position+restaurant.position)
	w.release_input=false
	s.check("restaurant_near_reachable",w.can_open_restaurant())
	var saved_position:Vector2=w.player.position
	w.player.position+=Vector2(29,0)
	s.check("restaurant_distance_guard",not w.can_open_restaurant())
	w.player.position=saved_position
	w.release_input=true
	s.check("restaurant_release_guard",not w.can_open_restaurant())
	w.release_input=false
	w.journal.show_page("bag")
	s.check("restaurant_other_page_guard",not w.can_open_restaurant())
	w.journal.show_page("restaurant")
	await process_frame
	await process_frame
	s.check("restaurant_six_supply_icons",page.get_node("Surface/SupplyItems").get_child_count()==6)
	for id in page.ITEMS:
		s.check("restaurant_icon_"+id,page.get_node("Surface/SupplyItems/"+id+"/Icon").item_id==id)
		w.foraging.bag.add(id,1)
	page.render()
	page.get_node("Surface/FundingAmount").value=2000
	s.check("funding_max",page.get_node("Surface/FundingAmount").value==1000)
	page.get_node("Surface/FundingAmount").value=0
	s.check("funding_min",page.get_node("Surface/FundingAmount").value==1)
	page.get_node("Surface/FundingAmount").value=28
	s.check("funding_personal_disclosure",page.get_node("Surface/FundingTotal").text.contains("28") and page.get_node("Surface/Fund").text.contains("个人"))
	page.get_node("Surface/Fund").grab_focus()
	page.wait_release=true
	var seq:int=w.foraging.life.action_seq
	page.submit("fund_restaurant")
	s.check("held_open_e_blocked",w.foraging.life.action_seq==seq)
	page.wait_release=false
	key(page,KEY_E,true)
	s.check("echo_e_blocked",w.foraging.life.action_seq==seq)
	page.submit("fund_restaurant")
	page.submit("fund_restaurant")
	page.back()
	s.check("pending_close_gate",w.journal.mode=="restaurant" and page.submitting)
	await process_frame
	await process_frame
	s.check("funding_once",w.foraging.life.wallet==72 and w.foraging.life.town.restaurant.cash==328 and w.foraging.life.action_seq==seq+1)
	s.check("funding_balances",page.get_node("Surface/Cash").text.contains("72") and page.get_node("Surface/Cash").text.contains("328"))
	var service=w.action_service
	w.action_service=Service.new(FailedSave.new())
	page.get_node("Surface/Fund").grab_focus()
	var before:Dictionary=w.foraging.to_data(w.player.position)
	page.submit("fund_restaurant")
	await process_frame
	await process_frame
	s.check("funding_failure_atomic",Rules._same_payload(before,w.foraging.to_data(w.player.position)))
	s.check("funding_failure_focus",w.journal.mode=="restaurant" and root.gui_get_focus_owner()==page.get_node("Surface/Fund") and page.get_node("Surface/Note").text.contains("尚未保存"))
	w.action_service=service
	page.submit("fund_restaurant")
	await process_frame
	await process_frame
	s.check("funding_retry",w.foraging.life.wallet==44 and w.foraging.life.town.restaurant.cash==356)
	for id in page.ITEMS:
		page.select_item(id)
		var wallet:int=w.foraging.life.wallet
		page.submit("supply")
		page.submit("supply")
		await process_frame
		await process_frame
		s.check("supply_"+id,w.foraging.bag.count_item(id)==0 and w.foraging.life.wallet==wallet+Rules.SUPPLY_PRICES[id])
	page.return_to_item()
	key(page,KEY_TAB)
	s.check("tab_actions",page._region(root.gui_get_focus_owner())==1)
	key(page,KEY_TAB)
	s.check("tab_funding",page._region(root.gui_get_focus_owner())==2)
	key(page,KEY_RIGHT)
	s.check("keyboard_funding_quantity",page.get_node("Surface/FundingAmount").value==29)
	page.get_node("Surface/FundingAmount").get_line_edit().text="31"
	key(page,KEY_E)
	s.check("numeric_funding_edit",page.get_node("Surface/FundingAmount").value==31 and root.gui_get_focus_owner()==page.get_node("Surface/Fund"))
	page.get_node("Surface/Quantity").get_line_edit().grab_focus()
	page.get_node("Surface/Quantity").get_line_edit().text="2"
	key(page,KEY_E)
	s.check("numeric_supply_edit",page.get_node("Surface/Quantity").value==2)
	page.get_node("Surface/Quantity").value=1
	key(page,KEY_B)
	s.check("back_to_items",w.journal.mode=="restaurant" and page._region(root.gui_get_focus_owner())==0)
	key(page,KEY_A)
	s.check("keyboard_item_selection",page.item_id=="clam_salad")
	key(page,KEY_ESCAPE)
	s.check("close_release",w.journal.mode=="" and w.release_input)
	w.release_input=false
	w.journal.show_page("restaurant")
	await process_frame
	page.wait_release=false
	page.submit("open_restaurant")
	await process_frame
	await process_frame
	s.check("open_trial_persisted",w.foraging.life.town.restaurant.status=="trial" and w.foraging.life.town.restaurant.enabled and w.save_service.read_save().data.life.town.restaurant.status=="trial")
	s.check("trial_visual_sync",restaurant.get_node("OpenSign").visible and not restaurant.get_node("ClosedSign").visible)
	print("P11 UI checks=",s.checks.size()," failures=",s.checks.values().count(false))
	w.queue_free();await process_frame
	quit(0 if s.passed() else 1)
