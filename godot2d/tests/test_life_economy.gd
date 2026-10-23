extends SceneTree
const State=preload("res://scripts/player_state.gd")
const Rules=preload("res://scripts/simulation/life_rules.gd")
const Service=preload("res://scripts/simulation/action_service.gd")
const Save=preload("res://scripts/save_service.gd")
const Inventory=preload("res://scripts/inventory/inventory_container.gd")
const Support=preload("res://tests/life_test_support.gd")
const POINT=Vector2(330,250)
var t=Support.new()
var Town
class FailedSave extends RefCounted:
	func write_save(_data):return false
func _initialize():call_deferred("run")
func check(id,ok):t.check(id,ok)
func act(d,kind,args):return Rules.plan(d,kind,args,int(d.life.action_seq)+1)
func put(slots,item,n):
	var inv=Inventory.new(slots.size());assert(inv.restore_slots(slots));assert(inv.add(item,n)==n);return inv.snapshot()
func count(slots,item):
	var inv=Inventory.new(slots.size());inv.restore_slots(slots);return inv.count_item(item)
func fixture():
	var d=State.new().to_data(POINT)
	if not d.life.has("town"):return d
	d.life.town.restaurant.enabled=true;d.life.town.restaurant.status="trial"
	for item in ["clam","lettuce","snail","tomato"]:d.life.town.restaurant.slots=put(d.life.town.restaurant.slots,item,2 if item in ["clam","lettuce"] else 1)
	return d
func total(d):
	var town=d.life.town
	var n=d.life.wallet+d.life.accounts.market.cash+town.restaurant.cash+town.supply_depot.cash+town.external_fund
	for hh in town.households.values():n+=hh.cash
	return n
func material_totals(d):
	var result={}
	for slots in [d.bag,d.chest,d.life.accounts.market.slots,d.life.town.restaurant.slots]:
		for slot in slots:
			if slot.id!="":result[slot.id]=int(result.get(slot.id,0))+int(slot.amount)
	for item in d.life.town.supply_depot.stock:result[item]=int(result.get(item,0))+int(d.life.town.supply_depot.stock[item])
	return result
func materials_match(before,d,events):
	var expected=material_totals(before)
	for e in events:
		if e.kind=="production":
			for item in e.inputs:expected[item]=int(expected.get(item,0))-int(e.inputs[item])
			for item in e.outputs:expected[item]=int(expected.get(item,0))+int(e.outputs[item])
		if e.kind=="consume":
			for item in e.items:expected[item]=int(expected.get(item,0))-int(e.items[item])
		if e.kind=="external_restock":
			for item in e.items:expected[item]=int(expected.get(item,0))+int(e.items[item])
	var actual=material_totals(d)
	for item in expected:
		if int(actual.get(item,0))!=int(expected[item]):return false
	for item in actual:
		if int(actual[item])!=int(expected.get(item,0)):return false
	return true
func balances(d):
	var h=0
	for hh in d.life.town.households.values():h+=hh.cash
	return [int(d.life.wallet),int(d.life.accounts.market.cash),int(d.life.town.restaurant.cash),int(h),int(d.life.town.supply_depot.cash),int(d.life.town.external_fund)]
func reject(d,kind,args,code,id):
	var before=d.duplicate(true);var r=act(d,kind,args)
	check(id,not r.ok and r.code==code and r.state=={} and r.events==[] and d==before)
func run():
	var d=State.new().to_data(POINT)
	check("fund_action_available",act(d,"fund_restaurant",{"amount":28}).ok)
	d.bag=put(d.bag,"clam_salad",2)
	check("supply_action_available",act(d,"supply",{"account_id":"restaurant","item_id":"clam_salad","amount":2}).ok)
	check("new_game_v6",d.version==6 and d.life.has("town"))
	check("town_module",ResourceLoader.exists("res://scripts/simulation/town_rules.gd"))
	if d.version!=6 or not ResourceLoader.exists("res://scripts/simulation/town_rules.gd"):finish();return
	Town=load("res://scripts/simulation/town_rules.gd")
	d=fixture();var before=d.duplicate(true);var r=act(d,"sleep",{"expected_day":1})
	check("first_day_ok",r.ok)
	if not r.ok:print(r);finish();return
	check("immutable",d==before)
	check("first_day_balances",balances(r.state)==[100,940,372,948,100,9940])
	check("first_day_metrics",r.state.life.town.restaurant.last_metrics.paid_staff==2 and r.state.life.town.restaurant.last_metrics.batches==4 and r.state.life.town.restaurant.last_metrics.produced=={"clam_salad":4} and r.state.life.town.restaurant.last_metrics.cash_profit==72)
	check("first_day_cursor",r.state.life.town.consumption_cursor==1)
	check("food_history",r.state.life.town.food_history==[{"day_id":1,"served":4,"total":5}])
	check("event_production",r.events.filter(func(e):return e.kind=="production").size()==4)
	check("event_consume",r.events.filter(func(e):return e.kind=="consume").size()==4)
	check("single_settle",Town.settle(r.state,1).code=="invalid_day")
	for day in range(1,15):
		var material_before=d.duplicate(true)
		r=act(d,"sleep",{"expected_day":day});check("independent_day_%d"%day,r.ok)
		if not r.ok:finish();return
		d=r.state;check("conservation_%d"%day,total(d)==12400 and State.valid_data(d))
		check("material_events_%d"%day,materials_match(material_before,d,r.events))
		for id in d.life.town.households:check("hh_nonnegative_%d_%s"%[day,id],d.life.town.households[id].cash>=0)
	check("independent14",balances(d)==[100,1480,788,272,600,9160])
	check("independent_households",d.life.town.households.values().map(func(h):return h.cash)==[94,94,38,8,38])
	check("independent_stock",count(d.life.accounts.market.slots,"clam")==0 and count(d.life.accounts.market.slots,"lettuce")==0 and d.life.town.supply_depot.stock=={"clam":6,"snail":56,"lettuce":6,"tomato":56})
	check("bounded_history",d.life.town.food_history.size()==7 and d.life.town.daily_metrics.size()==14)
	budgets();transactions();event_retention();recovery();default_path();await persistence();finish()
func budgets():
	for cash in [3,4]:
		var d=fixture();d.life.town.restaurant.cash=cash
		var r=act(d,"sleep",{"expected_day":1})
		check("salary_%d"%cash,r.ok and r.state.life.town.restaurant.last_metrics.paid_staff==(0 if cash==3 else 1) and r.state.life.town.restaurant.last_metrics.batches==(0 if cash==3 else 2))
	var d=State.new().to_data(POINT)
	var r=act(d,"sleep",{"expected_day":1})
	check("closed_still_settles",r.ok and r.state.life.town.restaurant.cash==300 and r.state.life.town.restaurant.last_metrics.paid_staff==0 and r.state.life.accounts.market.cash==900 and r.state.life.town.households.hh_01.cash==212)
	d=fixture();d.life.town.restaurant.slots=Inventory.new(48).snapshot();d.life.town.supply_depot.stock={"clam":0,"snail":0,"lettuce":0,"tomato":0}
	r=act(d,"sleep",{"expected_day":1})
	check("missing_inputs_costs_wages",r.ok and r.state.life.town.restaurant.last_metrics.cash_profit==-8 and r.state.life.town.restaurant.last_metrics.reasons.has("missing_inputs"))
	d.life.town.supply_depot.stock.clam=1
	r=act(d,"sleep",{"expected_day":1})
	check("finite_depot",r.ok and r.state.life.town.supply_depot.stock.clam==0 and count(r.state.life.accounts.market.slots,"clam")==1)
	d=fixture();d.life.town.restaurant.slots=Inventory.new(48).snapshot();d.life.town.supply_depot.stock={"clam":0,"snail":0,"lettuce":0,"tomato":0}
	d.life.accounts.market.slots=put(d.life.accounts.market.slots,"clam",4)
	for item in ["snail","tomato"]:d.life.accounts.market.slots=put(d.life.accounts.market.slots,item,4)
	r=act(d,"sleep",{"expected_day":1})
	check("fallback_stew",r.ok and r.state.life.town.restaurant.last_metrics.produced=={"snail_stew":4} and r.state.life.town.restaurant.last_metrics.cash_profit==40)
	check("fallback_atomic",r.ok and count(r.state.life.accounts.market.slots,"snail")==0 and count(r.state.life.accounts.market.slots,"tomato")==0 and count(r.state.life.accounts.market.slots,"clam")==4 and count(r.state.life.town.restaurant.slots,"clam")==0)
	d=fixture()
	for i in range(48):d.life.town.restaurant.slots[i]={"id":"kelp","amount":99}
	d.life.town.restaurant.slots[0]={"id":"clam","amount":99};d.life.town.restaurant.slots[1]={"id":"lettuce","amount":99}
	r=act(d,"sleep",{"expected_day":1})
	check("production_capacity_rollback",r.ok and r.state.life.town.restaurant.slots==d.life.town.restaurant.slots and r.state.life.town.restaurant.last_metrics.batches==0 and r.state.life.town.restaurant.last_metrics.reasons.has("inventory_full"))
	d=fixture();d.life.town.external_fund=5
	r=act(d,"sleep",{"expected_day":1})
	check("finite_livelihood",r.ok and r.state.life.town.external_fund==0 and r.events.filter(func(e):return e.reason=="external_livelihood").size()==1)
	d=fixture();d.life.town.external_fund=0;d.life.town.households.hh_03.cash=0
	r=act(d,"sleep",{"expected_day":1})
	check("budget_unmet",r.ok and r.state.life.town.households.hh_03.cash==0 and r.state.life.town.restaurant.last_metrics.unmet_households.has("hh_03"))
func transactions():
	var d=State.new().to_data(POINT);d.bag=put(d.bag,"clam_salad",2)
	var a={"account_id":"restaurant","item_id":"clam_salad","amount":2}
	var r=act(d,"supply",a)
	check("supply_atomic",r.ok and r.state.life.wallet==148 and r.state.life.town.restaurant.cash==252 and count(r.state.life.town.restaurant.slots,"clam_salad")==2 and r.state.life.town.restaurant.supply_quota.clam_salad==2 and count(r.state.bag,"clam_salad")==0 and total(r.state)==total(d))
	check("supply_event",r.ok and r.events.size()==1 and r.events[0].source=="restaurant" and r.events[0].target=="player" and r.events[0].cash==48 and r.events[0].kind=="transfer")
	check("supply_replay",r.ok and Rules.plan(r.state,"supply",a,1).events==[])
	var slept=act(r.state,"sleep",{"expected_day":1})
	check("purchase_supply_once",slept.ok and slept.state.life.town.restaurant.last_metrics.purchase_cash==48 and slept.state.life.town.restaurant.last_metrics.cash_profit==-48 and slept.state.life.town.restaurant.supply_quota.clam_salad==4)
	reject(d,"supply",{"account_id":"wrong","item_id":"missing","amount":1},"unknown_account","account_first")
	reject(d,"supply",{"account_id":"restaurant","item_id":"missing","amount":1},"unknown_item","unknown_item")
	reject(d,"supply",{"account_id":"restaurant","item_id":"marine_fertilizer","amount":1},"not_allowed","not_food")
	for value in [0,-1,100,1.5,INF,NAN]:
		reject(d,"supply",{"account_id":"restaurant","item_id":"clam_salad","amount":value},"invalid_amount","supply_amount_"+str(value))
	for value in [true,"1"]:
		reject(d,"fund_restaurant",{"amount":value},"invalid_request","fund_type_"+str(value))
	for value in [0,-1,1001,1.5,INF,NAN]:reject(d,"fund_restaurant",{"amount":value},"invalid_amount","fund_amount_"+str(value))
	reject(d,"fund_restaurant",{"amount":101},"insufficient_funds","fund_poor")
	reject(d,"fund_restaurant",{"amount":1,"extra":true},"invalid_request","fund_extra")
	var full=d.duplicate(true)
	for i in range(48):full.life.town.restaurant.slots[i]={"id":"kelp","amount":99}
	reject(full,"supply",a,"inventory_full","supply_full")
	full=d.duplicate(true);full.life.town.restaurant.cash=0
	reject(full,"supply",a,"insufficient_funds","supply_poor")
	full=d.duplicate(true);full.life.town.restaurant.supply_quota.clam_salad=1
	reject(full,"supply",a,"quota_exceeded","supply_quota")
	full=d.duplicate(true);full.life.town.restaurant.cash=1000000000
	reject(full,"fund_restaurant",{"amount":1},"invalid_state","fund_overflow")
	r=act(d,"fund_restaurant",{"amount":28})
	check("fund_balances",r.ok and r.state.life.wallet==72 and r.state.life.town.restaurant.cash==328 and total(r.state)==total(d))
	check("fund_event",r.ok and r.events[0].reason=="restaurant_funding" and r.events[0].items=={})
	slept=act(r.state,"sleep",{"expected_day":1})
	check("fund_not_profit",slept.ok and slept.state.life.town.restaurant.last_metrics.cash_profit==0 and slept.state.life.daily_reports[-1].cash_out==28)
func event_retention():
	var d=State.new().to_data(POINT);d.life.wallet=1000;d.bag=put(d.bag,"clam_salad",1)
	var r=act(d,"supply",{"account_id":"restaurant","item_id":"clam_salad","amount":1})
	d=r.state
	for i in range(270):
		r=act(d,"fund_restaurant",{"amount":1})
		if not r.ok:check("retention_action_%d"%i,false);return
		d=r.state
	r=act(d,"sleep",{"expected_day":1})
	check("retention_purchase",r.ok and r.state.life.town.restaurant.last_metrics.purchase_cash==24)
	check("retention_player_report",r.ok and r.state.life.daily_reports[-1].cash_in==24 and r.state.life.daily_reports[-1].cash_out==270)
	check("retention_bounded_valid",r.ok and r.state.life.events.size()<=256 and State.valid_data(r.state))
func recovery():
	var d=State.new().to_data(POINT);d.life.town.restaurant.cash=0
	for item in ["clam","lettuce"]:d.bag=put(d.bag,item,1)
	var r=act(d,"fund_restaurant",{"amount":28})
	check("recover_fund",r.ok and r.state.life.wallet==72 and r.state.life.town.restaurant.cash==28)
	if not r.ok:return
	d=r.state
	for item in ["clam","lettuce"]:
		r=act(d,"supply",{"account_id":"restaurant","item_id":item,"amount":1})
		if not r.ok:check("recover_supply_"+item,false);return
		d=r.state
	check("recover_supply",d.life.wallet==92 and d.life.town.restaurant.cash==8)
	# Economic fixture only: the visible open command/state machine belongs to P11.
	d.life.town.restaurant.enabled=true;d.life.town.restaurant.status="trial"
	r=act(d,"sleep",{"expected_day":1})
	check("recover_one_meal",r.ok and r.state.life.town.restaurant.cash==30 and r.state.life.town.restaurant.last_metrics.produced=={"clam_salad":1} and r.state.life.town.restaurant.last_metrics.households_served==1 and r.state.life.town.restaurant.last_metrics.purchase_cash==20)
func default_path():
	var state=State.new()
	var save=Save.new(t.temporary_directory("P10-default"))
	var actions:Array=[
		["trade",{"direction":"buy","account_id":"market","item_id":"lettuce_seed","amount":1}],
		["hoe",{"cell_id":"garden_a:0:0"}],
		["plant",{"cell_id":"garden_a:0:0","crop_id":"lettuce"}],
		["water",{"cell_id":"garden_a:0:0"}],
		["sleep",{"expected_day":1}],
		["water",{"cell_id":"garden_a:0:0"}],
		["sleep",{"expected_day":2}],
		["harvest",{"cell_id":"garden_a:0:0"}],
		["collect",{"pickup_id":"clam_a"}],
		["supply",{"account_id":"restaurant","item_id":"clam","amount":1}],
		["supply",{"account_id":"restaurant","item_id":"lettuce","amount":1}]]
	for index in range(actions.size()):
		var r=Service.new(save).execute(state,POINT,actions[index][0],actions[index][1],int(state.life.action_seq)+1)
		check("default_action_%d"%index,r.ok)
		if not r.ok:return
		state=r.next_state
	# P10 backend enablement fixture; no P11 open command or visual acceptance.
	state.life.town.restaurant.enabled=true;state.life.town.restaurant.status="trial"
	for day in range(3,17):
		var r=Service.new(save).execute(state,POINT,"sleep",{"expected_day":day},int(state.life.action_seq)+1)
		check("default_night_%d"%day,r.ok)
		if not r.ok:return
		state=r.next_state
		check("default_conservation_%d"%day,total(state.to_data(POINT))==12400)
		if day in [3,7,10]:
			var next=State.new()
			check("default_reload_%d"%day,next.restore(save.read_save().data) and Rules._same_payload(next.to_data(POINT),state.to_data(POINT)))
			state=next
	var d=state.to_data(POINT)
	check("default_exact14",balances(d)==[115,1495,748,392,610,9040] and d.life.day_id==17)
	check("default_individual_budgets",d.life.town.households.values().map(func(h):return h.cash)==[88,118,62,62,62])
	check("default_depot",Rules._same_payload(d.life.town.supply_depot.stock,{"clam":5,"snail":56,"lettuce":5,"tomato":56}))
	check("default_remaining_food",state.bag.count_item("lettuce")==2 and count(d.life.town.restaurant.slots,"clam_salad")==0)
	check("default_rolling_food",d.life.town.food_history.reduce(func(n,e):return n+e.served,0)==28 and d.life.town.daily_metrics.size()==16)
func persistence():
	for kind in ["fund_restaurant","supply","sleep"]:
		var state=State.new();state.bag.add("clam_salad",2)
		var args={"amount":28} if kind=="fund_restaurant" else ({"account_id":"restaurant","item_id":"clam_salad","amount":2} if kind=="supply" else {"expected_day":1})
		var before=state.to_data(POINT)
		var failed=Service.new(FailedSave.new()).execute(state,POINT,kind,args,1)
		check("save_fail_"+kind,failed.code=="save_failed" and state.to_data(POINT)==before)
		var save=Save.new(t.temporary_directory("P10-"+kind))
		var r=Service.new(save).execute(state,POINT,kind,args,1)
		check("save_"+kind,r.ok)
		if not r.ok:print("SAVE_DIAGNOSTIC ",kind," ",r.code," ",save.last_error)
		if not r.ok:continue
		var disk=FileAccess.get_file_as_string(save.directory+"/progress.json")
		var restored=State.new();check("reload_"+kind,restored.restore(save.read_save().data))
		var replay=Service.new(save).execute(restored,POINT,kind,args,1)
		check("replay_"+kind,replay.ok and replay.duplicate and replay.events==[] and FileAccess.get_file_as_string(save.directory+"/progress.json")==disk)
		var bad=Service.new(save).execute(restored,POINT,"fund_restaurant",{"amount":0},2)
		check("disk_atomic_"+kind,not bad.ok and FileAccess.get_file_as_string(save.directory+"/progress.json")==disk)
func finish():
	print("P10 checks=",t.checks.size()," failures=",t.checks.values().count(false));quit(0 if t.passed() else 1)
