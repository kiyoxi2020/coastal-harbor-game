extends SceneTree
const State=preload("res://scripts/player_state.gd")
const Rules=preload("res://scripts/simulation/life_rules.gd")
const Schema=preload("res://scripts/simulation/state_schema.gd")
const Service=preload("res://scripts/simulation/action_service.gd")
const Save=preload("res://scripts/save_service.gd")
const Inventory=preload("res://scripts/inventory/inventory_container.gd")
const Data=preload("res://scripts/harbor_data.gd")
const Support=preload("res://tests/life_test_support.gd")
const POINT=Vector2(330,250)
var t=Support.new()
var state
var save
var label="default"
var material_inputs={}
var material_outputs={}
var material_destroyed={}
var last_events=[]
func _initialize():call_deferred("run")
func check(id,ok):t.check(label+"_"+id,ok)
func put(slots,item,n):
	var inv=Inventory.new(slots.size());assert(inv.restore_slots(slots));assert(inv.add(item,n)==n);return inv.snapshot()
func count(slots,item):
	var inv=Inventory.new(slots.size());inv.restore_slots(slots);return inv.count_item(item)
func balances(d):
	var households=0
	for hh in d.life.town.households.values():households+=hh.cash
	return [int(d.life.wallet),int(d.life.accounts.market.cash),int(d.life.town.restaurant.cash),int(households),int(d.life.town.supply_depot.cash),int(d.life.town.external_fund)]
func total(d):return balances(d).reduce(func(n,v):return n+v,0)
func materials(d):
	var counts={}
	for slots in [d.bag,d.chest,d.life.accounts.market.slots,d.life.town.restaurant.slots]:
		for slot in slots:
			if slot.id!="":counts[slot.id]=int(counts.get(slot.id,0))+int(slot.amount)
	for item in d.life.town.supply_depot.stock:counts[item]=int(counts.get(item,0))+int(d.life.town.supply_depot.stock[item])
	return counts
func accumulate(target,items):
	for item in items:target[item]=int(target.get(item,0))+int(items[item])
func material_audit(before,after,events):
	var expected=materials(before)
	for event in events:
		if event.kind in ["production","craft"]:
			accumulate(material_inputs,event.inputs);accumulate(material_outputs,event.outputs)
			for item in event.inputs:expected[item]=int(expected.get(item,0))-int(event.inputs[item])
			accumulate(expected,event.outputs)
		if event.kind=="consume":
			accumulate(material_destroyed,event.items)
			for item in event.items:expected[item]=int(expected.get(item,0))-int(event.items[item])
		if event.kind in ["collect","external_restock"]:accumulate(expected,event.items)
	var actual=materials(after)
	for item in expected:
		if int(expected[item])!=int(actual.get(item,0)):return false
	for item in actual:
		if int(actual[item])!=int(expected.get(item,0)):return false
	return true
func act(kind,args={}):
	var before=state.to_data(POINT);var request=int(state.life.action_seq)+1
	var r=Service.new(save).execute(state,POINT,kind,args,request)
	check("action_%d_%s"%[request,kind],r.ok)
	if not r.ok:print("P11_ACTION_ERROR ",kind," ",args," ",r.code);return false
	check("immutable_%d"%request,state.to_data(POINT)==before)
	state=r.next_state;last_events=r.events.duplicate(true)
	var after=state.to_data(POINT)
	check("valid_money_%d"%request,Schema.validate_v6(after) and total(before)==total(after))
	check("materials_%d"%request,material_audit(before,after,r.events))
	return true
func reload_and_replay(id):
	var before=state.to_data(POINT);var disk=FileAccess.get_file_as_string(save.directory+"/progress.json");var next=State.new()
	check("reload_"+id,next.restore(save.read_save().data) and Rules._same_payload(next.to_data(POINT),before))
	var receipt=next.life.last_receipt
	var replay=Service.new(save).execute(next,POINT,receipt.kind,receipt.args,int(receipt.request_id))
	check("replay_"+id,replay.ok and replay.duplicate and replay.events==[] and Rules._same_payload(next.to_data(POINT),before) and FileAccess.get_file_as_string(save.directory+"/progress.json")==disk)
	state=next
func start(name,data={}):
	label=name;state=State.new();save=Save.new(t.temporary_directory("P11-"+name))
	if not data.is_empty():check("restore_fixture",state.restore(data))
	material_inputs={};material_outputs={};material_destroyed={}
func run():
	await default_path();await funded_recovery();await old_save_recovery();await zero_source();finish()
func default_path():
	start("default")
	var actions=[
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
		["supply",{"account_id":"restaurant","item_id":"lettuce","amount":1}],
		["open_restaurant",{}]]
	for action in actions:
		if not act(action[0],action[1]):return
	check("trial_before_sleep",state.life.town.restaurant.status=="trial" and state.life.town.restaurant.good_days==0 and state.life.town.restaurant.last_metrics.households_served==0)
	var continuous=0;var peak=0
	for day in range(3,17):
		if not act("sleep",{"expected_day":day}):return
		var town=state.life.town;var metric=town.restaurant.last_metrics
		check("source_day_%d"%day,metric.day_id==day and state.life.day_id==day+1 and state.life.last_settled_day==day and town.daily_metrics.size()==day)
		check("conservation_%d"%day,total(state.to_data(POINT))==12400)
		check("daily_nonnegative_%d"%day,balances(state.to_data(POINT)).all(func(v):return v>=0) and town.households.values().all(func(h):return h.cash>=0) and materials(state.to_data(POINT)).values().all(func(n):return n>=0))
		check("daily_sales_%d"%day,metric.paid_staff==2 and metric.batches==4 and metric.households_served==4 and metric.sales_cash==120 and metric.cash_profit==32)
		continuous=continuous+1 if metric.households_served>0 else 0;peak=maxi(continuous,peak)
		check("status_%d"%day,town.restaurant.status==("trial" if day==3 else "operating") and town.restaurant.good_days==mini(day-2,7))
		print("P11_DAILY ",JSON.stringify({"day":day,"balances":balances(state.to_data(POINT)),"metric":metric,"inputs":material_inputs,"outputs":material_outputs,"destroyed":material_destroyed}))
		if day in [3,7,10]:reload_and_replay("day_%d"%day)
	check("at_least_seven_sales",peak>=7)
	var d=state.to_data(POINT);var town=d.life.town
	check("exact_endpoint",d.life.day_id==17 and balances(d)==[115,1495,748,392,610,9040])
	check("individual_households",town.households.values().map(func(h):return int(h.cash))==[88,118,62,62,62])
	check("market_inputs",[count(d.life.accounts.market.slots,"clam"),count(d.life.accounts.market.slots,"snail"),count(d.life.accounts.market.slots,"lettuce"),count(d.life.accounts.market.slots,"tomato")]==[0,4,0,4])
	check("depot_inputs",Rules._same_payload(town.supply_depot.stock,{"clam":5,"snail":56,"lettuce":5,"tomato":56}))
	check("remaining_inventory",state.bag.count_item("lettuce")==2 and state.bag.count_item("clam")==0 and town.restaurant.slots.all(func(s):return s.id=="") and count(d.life.accounts.market.slots,"lettuce_seed")==20 and count(d.life.accounts.market.slots,"tomato_seed")==20)
	check("all_unique_metrics",town.daily_metrics.map(func(m):return int(m.day_id))==range(1,17))
	check("food_rolling_not_cumulative",town.food_history.size()==7 and town.food_history.reduce(func(n,e):return n+e.served,0)==28 and town.food_history.reduce(func(n,e):return n+e.total,0)==35)
	check("cumulative_production",material_inputs=={"clam":56,"lettuce":56} and material_outputs=={"lettuce":3,"clam_salad":56} and material_destroyed=={"lettuce_seed":1,"clam_salad":56})
	print("P11_ENDPOINT ",JSON.stringify({"day":d.life.day_id,"balances":balances(d),"total":total(d),"food_served":28,"food_total":35,"depot":town.supply_depot,"cumulative_inputs":material_inputs,"cumulative_outputs":material_outputs,"cumulative_destroyed":material_destroyed}))
func funded_recovery():
	var d=State.new().to_data(POINT);d.life.town.restaurant.cash=0
	for item in ["clam","lettuce"]:d.bag=put(d.bag,item,5)
	start("recovery",d)
	if not act("fund_restaurant",{"amount":28}):return
	check("fund_28",state.life.wallet==72 and state.life.town.restaurant.cash==28)
	for item in ["clam","lettuce"]:
		if not act("supply",{"account_id":"restaurant","item_id":item,"amount":1}):return
	check("paid_inputs",state.life.wallet==92 and state.life.town.restaurant.cash==8)
	if not act("open_restaurant") or not act("sleep",{"expected_day":1}):return
	var metric=state.life.town.restaurant.last_metrics
	check("one_meal_real_recovery",state.life.town.restaurant.cash==30 and metric.paid_staff==2 and metric.wage_cash==8 and metric.batches==1 and metric.sales_cash==30 and metric.purchase_cash==20 and metric.cash_profit==2)
	check("funding_does_not_fake_good_day",metric.households_served==1 and state.life.town.restaurant.status=="trial" and state.life.town.restaurant.good_days==0 and state.life.town.restaurant.bad_days==1)
	if not act("fund_restaurant",{"amount":80}):return
	for item in ["clam","lettuce"]:
		if not act("supply",{"account_id":"restaurant","item_id":item,"amount":4}):return
	for day in [2,3]:
		if not act("sleep",{"expected_day":day}):return
	check("recovery_two_good_days",state.life.town.restaurant.status=="operating" and state.life.town.restaurant.good_days==2 and state.life.town.restaurant.bad_days==0)
	reload_and_replay("operating")
func frozen_act(d,kind,args):
	var r=Rules.plan(d,kind,args,int(d.life.action_seq)+1)
	check("v4_action_%d_%s"%[int(d.life.action_seq)+1,kind],r.ok and (not r.ok or Schema.validate_v4(r.state)))
	return r.state if r.ok else {}
func old_save_recovery():
	label="migration"
	var d=JSON.parse_string(FileAccess.get_file_as_string("res://tests/fixtures/life_save_v4.json"))
	for pickup in Data.pickups():d=frozen_act(d,"collect",{"pickup_id":pickup.id})
	for item in ["clam","snail","kelp"]:d=frozen_act(d,"trade",{"direction":"sell","account_id":"market","item_id":item,"amount":count(d.bag,item)})
	for item in ["lettuce_seed","tomato_seed"]:d=frozen_act(d,"trade",{"direction":"buy","account_id":"market","item_id":item,"amount":8})
	for cell in Schema.cell_ids():
		d=frozen_act(d,"hoe",{"cell_id":cell});d=frozen_act(d,"plant",{"cell_id":cell,"crop_id":"lettuce" if cell.begins_with("garden_a") else "tomato"})
	for day in range(1,8):
		for cell in Schema.cell_ids():
			if day==(3 if cell.begins_with("garden_a") else 5):d=frozen_act(d,"harvest",{"cell_id":cell})
			elif d.life.plots[cell].crop_id!="":d=frozen_act(d,"water",{"cell_id":cell})
		if day>1:
			for pickup in Data.pickups():d=frozen_act(d,"collect",{"pickup_id":pickup.id})
			for item in ["clam","snail","kelp"]:d=frozen_act(d,"trade",{"direction":"sell","account_id":"market","item_id":item,"amount":count(d.bag,item)})
		for item in ["lettuce","tomato"]:
			if count(d.bag,item)>0:d=frozen_act(d,"trade",{"direction":"sell","account_id":"market","item_id":item,"amount":mini(12,count(d.bag,item))})
		d=frozen_act(d,"sleep",{"expected_day":day})
	check("p07_exact_money",d.life.wallet==1100 and d.life.accounts.market.cash==0)
	check("p07_stock_preserved",count(d.life.accounts.market.slots,"clam")==14 and count(d.life.accounts.market.slots,"snail")==14 and count(d.life.accounts.market.slots,"kelp")==14 and count(d.life.accounts.market.slots,"lettuce")==24 and count(d.life.accounts.market.slots,"tomato")==24)
	# Rebuild and persist this run's actual frozen-v4 snapshot before migration.
	var path=t.temporary_directory("P11-v4-migration");DirAccess.make_dir_recursive_absolute(path)
	var file=FileAccess.open(path+"/progress.json",FileAccess.WRITE);file.store_string(JSON.stringify(d));file.close()
	var snapshot=FileAccess.get_file_as_bytes(path+"/progress.json");var old_market=d.life.accounts.market.duplicate(true)
	start("migration");save=Save.new(path)
	var read=save.read_save();check("v4_disk_migration",read.ok and state.restore(read.data) and state.life.town.initial_endowment.day_id==8 and state.life.wallet==1100 and Rules._same_payload(state.life.accounts.market,old_market))
	check("migration_read_keeps_original",FileAccess.get_file_as_bytes(path+"/progress.json")==snapshot)
	if not act("collect",{"pickup_id":"clam_a"}):return
	if not act("supply",{"account_id":"restaurant","item_id":"clam","amount":1}):return
	check("real_restaurant_return",state.life.wallet==1108 and state.life.town.restaurant.cash==292 and state.life.accounts.market.cash==0 and total(state.to_data(POINT))==12400)
	if not act("fund_restaurant",{"amount":20}):return
	reload_and_replay("one_time_endowment")
	check("migration_no_free_reset",state.life.town.restaurant.cash==312 and state.life.wallet==1088 and state.life.accounts.market.cash==0 and Rules._same_payload(state.life.accounts.market.slots,old_market.slots) and state.life.town.initial_endowment.day_id==8)
	# Newly planted lettuce gives the other ingredient through production actions.
	if not act("trade",{"direction":"buy","account_id":"market","item_id":"lettuce_seed","amount":1}):return
	if not act("plant",{"cell_id":"garden_a:0:0","crop_id":"lettuce"}):return
	for day in [8,9]:
		if not act("water",{"cell_id":"garden_a:0:0"}) or not act("sleep",{"expected_day":day}):return
	if not act("harvest",{"cell_id":"garden_a:0:0"}) or not act("supply",{"account_id":"restaurant","item_id":"lettuce","amount":1}) or not act("open_restaurant"):return
	check("migrated_can_reopen",state.life.town.restaurant.status=="trial" and state.life.town.restaurant.good_days==0)
	reload_and_replay("migrated_open")
func zero_source():
	var d=State.new().to_data(POINT);d.life.wallet=0;d.life.accounts.market.cash=0;d.life.accounts.market.slots=Inventory.new(48).snapshot()
	d.life.town.restaurant.cash=0;d.life.town.external_fund=0;d.life.town.supply_depot.cash=0;d.life.town.supply_depot.stock={"clam":0,"snail":0,"lettuce":0,"tomato":0}
	for hh in d.life.town.households.values():hh.cash=0
	start("zero",d);check("persist_fixture",save.write_save(state.to_data(POINT)))
	for action in [["fund_restaurant",{"amount":1},"insufficient_funds"],["supply",{"account_id":"restaurant","item_id":"clam","amount":1},"insufficient_stock"],["open_restaurant",{},"insufficient_stock"]]:
		var before=state.to_data(POINT);var disk=FileAccess.get_file_as_bytes(save.directory+"/progress.json")
		var r=Service.new(save).execute(state,POINT,action[0],action[1],1)
		check("no_source_"+action[0],not r.ok and r.code==action[2] and state.to_data(POINT)==before and FileAccess.get_file_as_bytes(save.directory+"/progress.json")==disk)
	if not act("sleep",{"expected_day":1}):return
	check("zero_stays_zero",total(state.to_data(POINT))==0 and state.life.town.restaurant.status=="closed" and state.life.town.restaurant.last_metrics.households_served==0)
func finish():
	print("P11 fourteen days checks=",t.checks.size()," failures=",t.checks.values().count(false));quit(0 if t.passed() else 1)
