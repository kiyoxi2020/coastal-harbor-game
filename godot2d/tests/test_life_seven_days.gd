extends SceneTree
const State = preload("res://scripts/player_state.gd")
const Rules = preload("res://scripts/simulation/life_rules.gd")
const Service = preload("res://scripts/simulation/action_service.gd")
const Save = preload("res://scripts/save_service.gd")
const Data = preload("res://scripts/harbor_data.gd")
const Inventory = preload("res://scripts/inventory/inventory_container.gd")
const Support = preload("res://tests/life_test_support.gd")
const POINT := Vector2(330,250)
var t = Support.new()
var state
var save
var operations := {}
func _initialize() -> void:
	call_deferred("run")
func act(kind: String, args: Dictionary) -> bool:
	var result: Dictionary = Service.new(save).execute(state,POINT,kind,args,int(state.life.action_seq)+1)
	t.check("action_%s_%s" % [state.life.action_seq+1,kind],result.ok)
	if not result.ok:
		print("ACTION_ERROR ",result.code," ",args)
		return false
	state = result.next_state
	operations[kind] = operations.get(kind,0)+1
	return true
func trade(direction: String, item: String, amount: int) -> bool:
	return act("trade",{"direction":direction,"account_id":"market","item_id":item,"amount":amount})
func reload_state(label: String) -> void:
	var before: Dictionary = state.to_data(POINT)
	var next = State.new()
	t.check(label,next.restore(save.read_save().data) and Rules._same_payload(next.to_data(POINT),before))
	state = next
func stock(item: String) -> int:
	var inventory = Inventory.new(48)
	inventory.restore_slots(state.life.accounts.market.slots)
	return inventory.count_item(item)
func start(label: String) -> void:
	state = State.new()
	var fixture = JSON.parse_string(FileAccess.get_file_as_string("res://tests/fixtures/life_save_v4.json"))
	t.check(label+"_fixture",fixture is Dictionary and state.restore(fixture))
	save = Save.new(t.temporary_directory("P07-"+label))
	operations = {}
func collect_all() -> void:
	for pickup in Data.pickups():
		if not state.collected.has(pickup.id): act("collect",{"pickup_id":pickup.id})
func sell_sea() -> void:
	for item in ["clam","snail","kelp"]:
		var n: int = state.bag.count_item(item)
		if n>0: trade("sell",item,n)
func reject(kind: String,args: Dictionary,code: String,label: String) -> void:
	var before: Dictionary = state.to_data(POINT)
	var bytes := FileAccess.get_file_as_string(save.directory+"/progress.json")
	var r: Dictionary = Service.new(save).execute(state,POINT,kind,args,int(state.life.action_seq)+1)
	t.check(label,not r.ok and r.code==code and state.to_data(POINT)==before and FileAccess.get_file_as_string(save.directory+"/progress.json")==bytes)
func run() -> void:
	start("baseline")
	trade("buy","lettuce_seed",1)
	trade("buy","tomato_seed",1)
	for cell in ["garden_a:0:0","garden_b:0:0"]:
		act("hoe",{"cell_id":cell})
		act("plant",{"cell_id":cell,"crop_id":"lettuce" if cell.contains("a:") else "tomato"})
	for day in range(1,8):
		for cell in ["garden_a:0:0","garden_b:0:0"]:
			var plot: Dictionary = state.life.plots[cell]
			if day == (3 if cell.contains("a:") else 5): act("harvest",{"cell_id":cell})
			elif not plot.crop_id.is_empty(): act("water",{"cell_id":cell})
		collect_all()
		sell_sea()
		for item in ["lettuce","tomato"]:
			if state.bag.count_item(item)>0: trade("sell",item,state.bag.count_item(item))
		reload_state("midday_%d" % day)
		act("sleep",{"expected_day":day})
		reload_state("sleep_reload_%d" % day)
		t.check("day_report_%d" % day,state.life.daily_reports[-1].day_id==day and state.life.daily_reports[-1].pickups==6 and state.life.daily_reports[-1].cash_in==48+(36 if day==3 else (60 if day==5 else 0)) and state.life.daily_reports[-1].cash_out==(13 if day==1 else 0))
	t.check("seven_days_exact",state.life.day_id==8 and state.life.last_settled_day==7 and state.life.wallet==519 and state.life.accounts.market.cash==581)
	t.check("history",state.total_collected==42 and state.discovered.size()==3 and state.collected.is_empty() and state.life.daily_reports.size()==7)
	t.check("market_inventory",stock("clam")==14 and stock("snail")==14 and stock("kelp")==14 and stock("lettuce")==3 and stock("tomato")==3 and stock("lettuce_seed")==20 and stock("tomato_seed")==20)
	for cell in state.life.plots:
		var p: Dictionary = state.life.plots[cell]
		t.check("end_plot_"+cell,p.crop_id=="" and p.tilled==(cell in ["garden_a:0:0","garden_b:0:0"]))
	for item in ["clam","snail","kelp","lettuce","tomato"]:
		t.check("empty_bag_quota_"+item,state.bag.count_item(item)==0 and state.life.accounts.market.buy_quota[item]==12)
	start("full16")
	collect_all()
	sell_sea()
	trade("buy","lettuce_seed",8)
	trade("buy","tomato_seed",8)
	for cell in state.life.plots:
		act("hoe",{"cell_id":cell})
		act("plant",{"cell_id":cell,"crop_id":"lettuce" if cell.begins_with("garden_a") else "tomato"})
	for day in range(1,8):
		for cell in state.life.plots:
			var p: Dictionary = state.life.plots[cell]
			if day == (3 if cell.begins_with("garden_a") else 5): act("harvest",{"cell_id":cell})
			elif not p.crop_id.is_empty(): act("water",{"cell_id":cell})
		if day>1: collect_all(); sell_sea()
		for item in ["lettuce","tomato"]:
			var amount: int = state.bag.count_item(item)
			if amount>12: reject("trade",{"direction":"sell","account_id":"market","item_id":item,"amount":amount},"quota_exceeded","quota_"+item)
			if amount>0: trade("sell",item,mini(amount,12))
		act("sleep",{"expected_day":day})
		reload_state("full_reload_%d" % day)
	t.check("full_yield",stock("lettuce")==24 and stock("tomato")==24)
	t.check("full_money",state.life.wallet==1100 and state.life.accounts.market.cash==0 and state.life.wallet+state.life.accounts.market.cash==1100)
	t.check("full_operations",operations.hoe==16 and operations.plant==16 and operations.water==48 and operations.harvest==16)
	print("FULL16_OPERATIONS ",operations)
	# All cash has moved to player; new day's quota alone cannot fund purchases.
	act("collect",{"pickup_id":"clam_a"})
	reject("trade",{"direction":"sell","account_id":"market","item_id":"clam","amount":1},"insufficient_funds","market_cash_refusal")
	await boundaries()
	print("P07 checks=",t.checks.size()," passed=",t.passed())
	quit(0 if t.passed() else 1)

func boundaries() -> void:
	start("recovery")
	state.life.wallet=0
	act("collect",{"pickup_id":"clam_a"})
	trade("sell","clam",1)
	trade("buy","lettuce_seed",1)
	t.check("zero_funds_recovery",state.life.wallet==3 and state.bag.count_item("lettuce_seed")==1)
	start("full_harvest")
	state.life.plots["garden_a:0:0"].merge({"tilled":true,"crop_id":"lettuce","growth":2,"watered":false},true)
	state.bag.add("kelp",24*99)
	save.write_save(state.to_data(POINT))
	reject("harvest",{"cell_id":"garden_a:0:0"},"inventory_full","full_harvest_atomic")
	state.bag.remove_item("kelp",99)
	act("harvest",{"cell_id":"garden_a:0:0"})
	t.check("harvest_once",state.bag.count_item("lettuce")==3 and state.life.plots["garden_a:0:0"].crop_id=="")
	for version in [1,2]:
		var raw = JSON.parse_string(FileAccess.get_file_as_string("res://tests/fixtures/life_save_v%d.json" % version))
		state=State.new()
		t.check("legacy_restore_%d" % version,state.restore(raw) and state.player_name==raw.player_name and state.location==raw.get("location","harbor") and Rules._same_payload(state.bag.snapshot(),raw.bag) and Rules._same_payload(state.chest.snapshot(),raw.chest))
		save=Save.new(t.temporary_directory("P07-legacy"))
		act("sleep",{"expected_day":1})
		reload_state("legacy_continue_%d" % version)
