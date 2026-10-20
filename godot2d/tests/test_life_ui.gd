extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
const Rules=preload("res://scripts/simulation/life_rules.gd")
const Service=preload("res://scripts/simulation/action_service.gd")
var s:=Support.new()
class FailedSave extends RefCounted:
	func write_save(_data:Dictionary) -> bool:return false
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var w=load("res://scenes/harbor.tscn").instantiate()
	w.set_meta("journal_test",true)
	w.set_meta("skip_verification",true)
	w.set_meta("save_directory",s.temporary_directory("P06-ui"))
	root.add_child(w)
	w.start_new_game("鱼摊")
	await process_frame
	await process_frame
	s.check("trade_page",w.journal.has_node("Root/TradePage"))
	s.check("daily_page",w.journal.has_node("Root/DailyPage"))
	s.check("hud_date_wallet",w.hud.has_node("Root/Top/Date") and w.hud.has_node("Root/Top/Wallet"))
	s.check("market_entry",w.has_method("can_open_trade"))
	if not w.journal.has_node("Root/TradePage") or not w.journal.has_node("Root/DailyPage"):
		w.queue_free();await process_frame
		print("LIFE_UI checks=",s.checks.size()," passed=false")
		quit(1);return
	var page=w.journal.get_node("Root/TradePage")
	w.player.position=w.exterior.get_node("InteractPoints/market").position
	w.release_input=false
	w.journal.show_page("trade")
	page.get_node("Surface/Quantity").value=2
	page.render()
	s.check("buy_display",page.get_node("Surface/UnitPrice").text.contains("5") and page.get_node("Surface/Total").text.contains("10") and page.get_node("Surface/Wallet").text.contains("100"))
	page.submit()
	page.submit() # same pending operation in one frame cannot execute twice
	await process_frame
	await process_frame
	s.check("buy_saved_once",w.foraging.life.wallet==90 and w.foraging.bag.count_item("lettuce_seed")==2 and w.foraging.life.action_seq==1)
	s.check("hud_real_wallet",w.hud.get_node("Root/Top/Wallet").text.contains("90"))
	var service=w.action_service
	w.action_service=Service.new(FailedSave.new())
	var before:Dictionary=w.foraging.to_data(w.player.position)
	page.submit()
	await process_frame
	await process_frame
	s.check("save_failure_atomic",Rules._same_payload(before,w.foraging.to_data(w.player.position)) and page.get_node("Surface/Note").text.contains("尚未保存"))
	w.action_service=service
	page.submit()
	await process_frame
	await process_frame
	s.check("retry_same_request_once",w.foraging.life.wallet==80 and w.foraging.bag.count_item("lettuce_seed")==4 and w.foraging.life.action_seq==2)
	w.foraging.bag.add("clam",2)
	page.select_direction("sell")
	await process_frame
	s.check("sell_rows_clear_note",page.get_node("Surface/Items/Item17").get_global_rect().end.y+8<=page.get_node("Surface/Note").global_position.y)
	page.select_item("clam")
	page.get_node("Surface/Quantity").value=1
	page.submit()
	await process_frame
	await process_frame
	s.check("sell_display",w.foraging.life.wallet==88 and w.foraging.bag.count_item("clam")==1 and w.foraging.life.accounts.market.buy_quota.clam==11)
	page.select_direction("buy")
	page.select_item("tomato_seed")
	page.get_node("Surface/Quantity").value=2
	w.foraging.life.wallet=0
	before=w.foraging.to_data(w.player.position)
	page.submit()
	await process_frame
	await process_frame
	s.check("stale_ui_revalidated",Rules._same_payload(before,w.foraging.to_data(w.player.position)) and page.get_node("Surface/Note").text.contains("不足"))
	w.foraging.life.wallet=88 # restore isolated fixture, never a native acceptance shortcut
	w.journal.dismiss()
	var result:Dictionary=w.perform_action("trade",{"direction":"buy","account_id":"market","item_id":"lettuce_seed","amount":1},4)
	s.check("wrong_page_guard",not result.ok)
	w.journal.show_page("trade")
	w.release_input=false
	w.player.position=Vector2(330,250)
	result=w.perform_action("trade",{"direction":"buy","account_id":"market","item_id":"lettuce_seed","amount":1},4)
	s.check("distance_guard",not result.ok)
	w.journal.dismiss()
	w.home.switch_room("house",Vector2(232,248))
	w.release_input=false
	w.journal.show_page("sleep")
	w.journal.confirm_sleep()
	await process_frame
	await process_frame
	s.check("sleep_opens_daily",w.journal.mode=="daily" and w.foraging.life.day_id==2)
	var report:Dictionary=load("res://scripts/simulation/report_builder.gd").daily(w.foraging.to_data(w.player.position))
	s.check("source_day_report",report.day_id==1 and report.current_day==2 and "\n".join(report.lines).contains("支出 20") and "\n".join(report.lines).contains("收入 8"))
	s.check("hud_date",w.hud.get_node("Root/Top/Date").text.contains("2"))
	before=w.foraging.to_data(w.player.position)
	load("res://scripts/simulation/report_builder.gd").daily(before)
	s.check("report_read_only",Rules._same_payload(before,w.foraging.to_data(w.player.position)))
	w.journal.dismiss()
	w.queue_free()
	await process_frame
	print("LIFE_UI checks=",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
