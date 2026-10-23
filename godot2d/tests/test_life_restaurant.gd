extends SceneTree
const State=preload("res://scripts/player_state.gd")
const Rules=preload("res://scripts/simulation/life_rules.gd")
const Schema=preload("res://scripts/simulation/state_schema.gd")
const Service=preload("res://scripts/simulation/action_service.gd")
const Save=preload("res://scripts/save_service.gd")
const Inventory=preload("res://scripts/inventory/inventory_container.gd")
const Support=preload("res://tests/life_test_support.gd")
const POINT=Vector2(330,250)
var t=Support.new()
class FailedSave extends RefCounted:
	func write_save(_data):return false
func _initialize():call_deferred("run")
func check(id,ok):t.check(id,ok)
func act(d,kind,args={}):return Rules.plan(d,kind,args,int(d.life.action_seq)+1)
func put(slots,item,n):
	var inv=Inventory.new(slots.size());assert(inv.restore_slots(slots));assert(inv.add(item,n)==n);return inv.snapshot()
func ready_state():
	var d=State.new().to_data(POINT)
	for item in ["clam","lettuce"]:d.life.town.restaurant.slots=put(d.life.town.restaurant.slots,item,1)
	return d
func reject(d,args,code,id):
	var before=d.duplicate(true);var r=act(d,"open_restaurant",args)
	check(id,not r.ok and r.code==code and r.state=={} and r.events==[] and d==before)
func empty_depot(d):
	d.life.town.supply_depot.stock={"clam":0,"snail":0,"lettuce":0,"tomato":0}
	d.life.accounts.market.slots=Inventory.new(48).snapshot()
	d.life.town.restaurant.slots=Inventory.new(48).snapshot()
	return d
func run():
	var d=ready_state();var before=d.duplicate(true);var r=act(d,"open_restaurant")
	check("open_available",r.ok)
	reject(State.new().to_data(POINT),{},"insufficient_stock","no_input_open")
	reject(d,{"enabled":true},"invalid_request","open_unknown_args")
	var meals=State.new().to_data(POINT);meals.life.town.restaurant.slots=put(meals.life.town.restaurant.slots,"clam_salad",4)
	reject(meals,{},"insufficient_stock","meals_are_not_inputs")
	var partial=State.new().to_data(POINT);partial.life.town.restaurant.slots=put(partial.life.town.restaurant.slots,"clam",4)
	reject(partial,{},"insufficient_stock","incomplete_recipe")
	if not r.ok:finish();return
	check("open_immutable",d==before)
	check("open_only_state_change",r.state.life.town.restaurant.enabled and r.state.life.town.restaurant.status=="trial" and r.state.life.town.restaurant.cash==300 and r.state.life.town.restaurant.slots==before.life.town.restaurant.slots and r.state.life.town.restaurant.last_metrics.is_empty())
	check("open_resets_counters",r.state.life.town.restaurant.good_days==0 and r.state.life.town.restaurant.bad_days==0)
	check("open_receipt",r.state.life.last_receipt=={"request_id":1,"kind":"open_restaurant","args":{}})
	check("open_status_event",r.events.size()==1 and r.events[0].kind=="restaurant_status" and r.events[0].source=="closed" and r.events[0].target=="trial" and r.events[0].cash==0 and r.events[0].items=={} and r.events[0].day_id==1 and r.events[0].event_id=="a:1:0")
	reject(r.state,{},"not_allowed","already_enabled")
	check("open_replay",Rules.plan(r.state,"open_restaurant",{},1).events==[])
	var stew=State.new().to_data(POINT)
	for item in ["snail","tomato"]:stew.life.town.restaurant.slots=put(stew.life.town.restaurant.slots,item,1)
	check("either_recipe",act(stew,"open_restaurant").ok)
	d=r.state
	for day in range(1,3):
		r=act(d,"sleep",{"expected_day":day});check("good_day_%d"%day,r.ok)
		if not r.ok:finish();return
		d=r.state;check("good_counter_%d"%day,d.life.town.restaurant.good_days==day and d.life.town.restaurant.bad_days==0)
		check("two_good_days_%d"%day,d.life.town.restaurant.status==("trial" if day==1 else "operating"))
		check("good_status_event_%d"%day,r.events.filter(func(e):return e.kind=="restaurant_status").size()==(0 if day==1 else 1))
	d=empty_depot(d)
	for bad in range(1,4):
		var old=d.life.town.restaurant.status;var cash=d.life.town.restaurant.cash
		r=act(d,"sleep",{"expected_day":int(d.life.day_id)});check("bad_day_%d"%bad,r.ok)
		if not r.ok:finish();return
		d=r.state
		check("bad_counters_%d"%bad,d.life.town.restaurant.good_days==0 and d.life.town.restaurant.bad_days==bad)
		check("bad_status_%d"%bad,d.life.town.restaurant.status==("operating" if bad==1 else ("trial" if bad==2 else "closed")) and d.life.town.restaurant.enabled==(bad<3))
		check("bad_cash_preserved_%d"%bad,d.life.town.restaurant.cash==cash-8)
		var status_events=r.events.filter(func(e):return e.kind=="restaurant_status")
		check("bad_status_events_%d"%bad,status_events.size()==(0 if bad==1 else 1) and (status_events.is_empty() or (status_events[0].source==old and status_events[0].target==d.life.town.restaurant.status)))
	var closed=d.duplicate(true)
	r=act(d,"sleep",{"expected_day":int(d.life.day_id)})
	check("closed_no_counter_or_wage",r.ok and r.state.life.town.restaurant.bad_days==3 and r.state.life.town.restaurant.last_metrics.wage_cash==0 and r.state.life.town.restaurant.cash==closed.life.town.restaurant.cash)
	for item in ["clam","lettuce"]:d.life.town.restaurant.slots=put(d.life.town.restaurant.slots,item,1)
	r=act(d,"open_restaurant")
	check("reopen_after_failure",r.ok and r.state.life.town.restaurant.status=="trial" and r.state.life.town.restaurant.good_days==0 and r.state.life.town.restaurant.bad_days==0 and r.state.life.town.restaurant.cash==d.life.town.restaurant.cash)
	await persistence();await boundaries();finish()
func persistence():
	var state=State.new();state.restore(ready_state());var before=state.to_data(POINT)
	var failed=Service.new(FailedSave.new()).execute(state,POINT,"open_restaurant",{},1)
	check("open_save_failure",not failed.ok and failed.code=="save_failed" and state.to_data(POINT)==before and failed.events==[])
	var save=Save.new(t.temporary_directory("P11-open"));var r=Service.new(save).execute(state,POINT,"open_restaurant",{},1)
	check("open_save",r.ok)
	if not r.ok:return
	var disk=FileAccess.get_file_as_string(save.directory+"/progress.json");var next=State.new()
	check("open_reload",next.restore(save.read_save().data) and Rules._same_payload(next.to_data(POINT),r.next_state.to_data(POINT)))
	var replay=Service.new(save).execute(next,POINT,"open_restaurant",{},1)
	check("open_disk_replay",replay.ok and replay.duplicate and replay.events==[] and FileAccess.get_file_as_string(save.directory+"/progress.json")==disk)
	var denied=Service.new(save).execute(next,POINT,"open_restaurant",{},2)
	check("open_disk_rejection",denied.code=="not_allowed" and next.to_data(POINT).life.town.restaurant.status=="trial" and FileAccess.get_file_as_string(save.directory+"/progress.json")==disk)
	r=Service.new(save).execute(next,POINT,"sleep",{"expected_day":1},2)
	check("persist_first_good_day",r.ok)
	if not r.ok:return
	next=r.next_state;before=next.to_data(POINT);disk=FileAccess.get_file_as_string(save.directory+"/progress.json")
	failed=Service.new(FailedSave.new()).execute(next,POINT,"sleep",{"expected_day":2},3)
	check("status_transition_save_failure",not failed.ok and failed.code=="save_failed" and next.to_data(POINT)==before and next.life.town.restaurant.status=="trial" and FileAccess.get_file_as_string(save.directory+"/progress.json")==disk)
	r=Service.new(save).execute(next,POINT,"sleep",{"expected_day":2},3)
	check("persist_operating",r.ok and r.next_state.life.town.restaurant.status=="operating")
	if not r.ok:return
	var operating=State.new();before=r.next_state.to_data(POINT);disk=FileAccess.get_file_as_string(save.directory+"/progress.json")
	check("operating_exact_reload",operating.restore(save.read_save().data) and Rules._same_payload(operating.to_data(POINT),before))
	replay=Service.new(save).execute(operating,POINT,"sleep",{"expected_day":2},3)
	check("operating_no_extra_sales_on_replay",replay.ok and replay.duplicate and replay.events==[] and Rules._same_payload(operating.to_data(POINT),before) and FileAccess.get_file_as_string(save.directory+"/progress.json")==disk)
func boundaries():
	var d=act(ready_state(),"open_restaurant").state
	d.life.town.restaurant.status="operating";d.life.town.restaurant.good_days=7
	var r=act(d,"sleep",{"expected_day":1})
	check("good_days_clamp",r.ok and r.state.life.town.restaurant.good_days==7)
	d=empty_depot(d);d.life.town.restaurant.bad_days=7
	r=act(d,"sleep",{"expected_day":1})
	check("bad_days_clamp",r.ok and r.state.life.town.restaurant.bad_days==7 and r.state.life.town.restaurant.status=="trial")
	d=act(ready_state(),"open_restaurant").state
	d.life.town.restaurant.employee_households=["hh_01"]
	d.life.town.restaurant.slots=put(d.life.town.restaurant.slots,"clam_salad",1)
	r=act(d,"sleep",{"expected_day":1})
	check("one_staff_three_households_good",r.ok and r.state.life.town.restaurant.last_metrics.paid_staff==1 and r.state.life.town.restaurant.last_metrics.households_served==3 and r.state.life.town.restaurant.good_days==1)
	# Three meals: two produced salads plus one supplied stew. Paid inputs cost
	# 98G, sales 102G and the single wage 4G: exactly zero profit is still good.
	d=State.new().to_data(POINT);d.life.town.restaurant.employee_households=["hh_01"]
	for entry in [["clam",2],["lettuce",3],["snail",1],["snail_stew",1]]:
		d.bag=put(d.bag,entry[0],entry[1])
		d=act(d,"supply",{"account_id":"restaurant","item_id":entry[0],"amount":entry[1]}).state
	d=act(d,"open_restaurant").state;r=act(d,"sleep",{"expected_day":1})
	check("zero_profit_is_good",r.ok and r.state.life.town.restaurant.last_metrics.cash_profit==0 and r.state.life.town.restaurant.last_metrics.households_served==3 and r.state.life.town.restaurant.good_days==1)
	d=ready_state();d.bag=put(d.bag,"clam_salad",4)
	d=act(d,"supply",{"account_id":"restaurant","item_id":"clam_salad","amount":4}).state
	d=act(d,"open_restaurant").state
	r=act(d,"sleep",{"expected_day":1})
	check("loss_is_bad_despite_served_households",r.ok and r.state.life.town.restaurant.last_metrics.paid_staff==2 and r.state.life.town.restaurant.last_metrics.households_served==5 and r.state.life.town.restaurant.last_metrics.cash_profit<0 and r.state.life.town.restaurant.bad_days==1 and r.state.life.town.restaurant.good_days==0)
	# Profit alone cannot pass without staff or at least three served households.
	d=empty_depot(act(ready_state(),"open_restaurant").state);d.life.town.restaurant.cash=0
	d.life.town.restaurant.slots=put(d.life.town.restaurant.slots,"clam_salad",4)
	r=act(d,"sleep",{"expected_day":1})
	check("no_staff_is_bad",r.ok and r.state.life.town.restaurant.last_metrics.households_served==4 and r.state.life.town.restaurant.last_metrics.cash_profit==120 and r.state.life.town.restaurant.good_days==0 and r.state.life.town.restaurant.bad_days==1)
	d=act(ready_state(),"open_restaurant").state;d.life.town.restaurant.good_days=1;d=empty_depot(d)
	r=act(d,"sleep",{"expected_day":1})
	check("bad_resets_good",r.ok and r.state.life.town.restaurant.good_days==0 and r.state.life.town.restaurant.bad_days==1)
	d=act(ready_state(),"open_restaurant").state;d.life.town.restaurant.bad_days=2
	r=act(d,"sleep",{"expected_day":1})
	check("good_resets_bad",r.ok and r.state.life.town.restaurant.good_days==1 and r.state.life.town.restaurant.bad_days==0)
	for field in ["good_days","bad_days"]:
		d=ready_state();d.life.town.restaurant[field]=8
		check("schema_counter_"+field,not Schema.validate_v6(d))
	d=ready_state();d.life.town.restaurant.enabled=true
	check("schema_status_enabled",not Schema.validate_v6(d))
	d=ready_state();d.life.action_seq=1;d.life.last_receipt={"request_id":1,"kind":"open_restaurant","args":{"unexpected":true}}
	check("schema_open_args",not Schema.validate_v6(d))
	var opened=act(ready_state(),"open_restaurant").state
	for mutation in ["cash","items","source","target","reason"]:
		d=opened.duplicate(true)
		match mutation:
			"cash":d.life.events[0].cash=1
			"items":d.life.events[0].items={"clam":1}
			"source":d.life.events[0].source="restaurant"
			"target":d.life.events[0].target="unknown"
			"reason":d.life.events[0].reason="free_money"
		check("schema_status_event_"+mutation,not Schema.validate_v6(d))
func finish():
	print("P11 restaurant checks=",t.checks.size()," failures=",t.checks.values().count(false));quit(0 if t.passed() else 1)
