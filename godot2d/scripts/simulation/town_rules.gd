extends RefCounted
const Schema=preload("res://scripts/simulation/state_schema.gd")
const Inventory=preload("res://scripts/inventory/inventory_container.gd")
const Recipes=preload("res://scripts/simulation/recipe_catalog.gd")
const Accounts=preload("res://scripts/simulation/account_transactions.gd")
const INPUTS=["clam","snail","lettuce","tomato"]
const DEPOT_PRICES={"clam":4,"snail":5,"lettuce":6,"tomato":10}
const INPUT_PRICES={"clam":8,"snail":10,"lettuce":12,"tomato":20}
const MEAL_PRICES={"clam_salad":30,"snail_stew":42}

static func _failure(code:String) -> Dictionary:
	return {"ok":false,"code":code,"state":{},"events":[]}
static func _event(day:int,kind:String,source:String,target:String,items:Dictionary,cash:int,reason:String) -> Dictionary:
	return {"day_id":day,"kind":kind,"source":source,"target":target,"items":items.duplicate(true),"cash":cash,"reason":reason}
static func _inventory(slots:Array):
	var inv=Inventory.new(slots.size())
	return inv if inv.restore_slots(slots) else null
static func _reason(metrics:Dictionary,code:String) -> void:
	if not metrics.reasons.has(code):metrics.reasons.append(code)

static func settle(data:Dictionary,source_day:int) -> Dictionary:
	if not Schema.validate_current(data) or not data.life.has("town"):return _failure("invalid_state")
	if source_day!=data.life.day_id or (not data.life.town.restaurant.last_metrics.is_empty() and source_day<=data.life.town.restaurant.last_metrics.day_id):return _failure("invalid_day")
	var candidate=data.duplicate(true)
	var town:Dictionary=candidate.life.town
	var restaurant:Dictionary=town.restaurant
	var metrics={"day_id":source_day,"paid_staff":0,"batches":0,"produced":{},"sold":{},"sales_cash":0,"purchase_cash":0,"wage_cash":0,"cash_profit":0,"households_served":0,"households_total":0,"unmet_households":[],"reasons":[]}
	var events:Array=[]
	var eligible:Array=[]
	var ids:Array=town.households.keys();ids.sort()
	# Purchase costs already paid by successful supply commands on the source day.
	for event in candidate.life.events:
		if event.day_id==source_day and event.kind in ["transfer","transfer_summary"] and event.reason=="restaurant_supply" and event.source=="restaurant":metrics.purchase_cash+=int(event.cash)
	for id in ids:
		var hh:Dictionary=town.households[id]
		if hh.eligible_from_day>source_day:continue
		eligible.append(id)
		var amount=mini(12,int(town.external_fund))
		if amount>0:
			if hh.cash>Accounts.MAX_CASH-amount:return _failure("invalid_state")
			town.external_fund-=amount;hh.cash+=amount
			events.append(_event(source_day,"transfer","external_fund",id,{},amount,"external_livelihood"))
		if amount<12:_reason(metrics,"external_fund_exhausted")
	metrics.households_total=eligible.size()
	if restaurant.enabled:
		for id in restaurant.employee_households:
			if restaurant.cash<4:break
			var code:=Accounts.move_cash(candidate,"restaurant",id,4)
			if code!="ok":return _failure(code)
			metrics.paid_staff+=1;metrics.wage_cash+=4
			events.append(_event(source_day,"transfer","restaurant",id,{},4,"wages"))
		if metrics.paid_staff==0:_reason(metrics,"no_staff")
	var market:Dictionary=candidate.life.accounts.market
	var depot:Dictionary=town.supply_depot
	var market_inventory=_inventory(market.slots)
	for item in INPUTS:
		var need=maxi(0,4-market_inventory.count_item(item))
		if need==0:continue
		var amount=mini(need,mini(int(depot.stock[item]),int(market.cash)/int(DEPOT_PRICES[item])))
		amount=mini(amount,market_inventory.space_for(item))
		if int(depot.stock[item])==0:_reason(metrics,"depot_empty")
		if amount==0:continue
		var cost=int(amount)*int(DEPOT_PRICES[item])
		var code:=Accounts.move_cash(candidate,"market","supply_depot",cost)
		if code!="ok":return _failure(code)
		depot.stock[item]-=amount
		if market_inventory.add(item,amount)!=amount:return _failure("invalid_state")
		events.append(_event(source_day,"purchase","market","supply_depot",{item:amount},cost,"market_restock"))
	market.slots=market_inventory.snapshot()
	if restaurant.enabled:
		for _batch in range(int(metrics.paid_staff)*2):
			var made=false
			var failures:Array=[]
			for recipe_id in ["clam_salad","snail_stew"]:
				var batch=_produce(candidate,recipe_id,source_day)
				if not batch.ok:
					failures.append(batch.code);continue
				candidate=batch.state
				town=candidate.life.town;restaurant=town.restaurant
				metrics.batches+=1
				metrics.produced[recipe_id]=int(metrics.produced.get(recipe_id,0))+1
				metrics.purchase_cash+=batch.cost
				events.append_array(batch.events)
				made=true;break
			if not made:
				for code in failures:_reason(metrics,code)
				break
	var meals=_inventory(restaurant.slots)
	for offset in range(eligible.size()):
		var id:String=eligible[(int(town.consumption_cursor)+offset)%eligible.size()]
		var served=false
		if restaurant.enabled:
			for meal in ["clam_salad","snail_stew"]:
				if meals.count_item(meal)<1:continue
				if Accounts.cash(candidate,id)<MEAL_PRICES[meal]:
					_reason(metrics,"household_budget");continue
				var code:=Accounts.move_cash(candidate,id,"restaurant",MEAL_PRICES[meal])
				if code!="ok":return _failure(code)
				if not meals.remove_item(meal,1):return _failure("invalid_state")
				metrics.sold[meal]=int(metrics.sold.get(meal,0))+1
				metrics.sales_cash+=MEAL_PRICES[meal];metrics.households_served+=1
				events.append(_event(source_day,"transfer",id,"restaurant",{meal:1},MEAL_PRICES[meal],"household_meal"))
				events.append(_event(source_day,"consume",id,"consumed",{meal:1},0,"household_meal"))
				served=true;break
		if not served:metrics.unmet_households.append(id)
	restaurant.slots=meals.snapshot()
	town.consumption_cursor=(int(town.consumption_cursor)+1)%eligible.size() if not eligible.is_empty() else 0
	metrics.cash_profit=metrics.sales_cash-metrics.purchase_cash-metrics.wage_cash
	if restaurant.enabled:
		var previous_status:String=restaurant.status
		var good_day:bool=metrics.paid_staff>=1 and metrics.households_served>=3 and metrics.cash_profit>=0
		restaurant.good_days=mini(7,int(restaurant.good_days)+1) if good_day else 0
		restaurant.bad_days=0 if good_day else mini(7,int(restaurant.bad_days)+1)
		if restaurant.status=="trial" and restaurant.good_days>=2:restaurant.status="operating"
		elif restaurant.status=="operating" and restaurant.bad_days>=2:restaurant.status="trial"
		elif restaurant.status=="trial" and restaurant.bad_days>=3:
			restaurant.status="closed";restaurant.enabled=false
		if restaurant.status!=previous_status:
			events.append(_event(source_day,"restaurant_status",previous_status,restaurant.status,{},0,"good_days" if good_day else "bad_days"))
	restaurant.last_metrics=metrics.duplicate(true)
	town.daily_metrics.append(metrics.duplicate(true))
	if town.daily_metrics.size()>30:town.daily_metrics=town.daily_metrics.slice(-30)
	town.food_history.append({"day_id":source_day,"served":metrics.households_served,"total":metrics.households_total})
	if town.food_history.size()>7:town.food_history=town.food_history.slice(-7)
	for item in restaurant.supply_quota:restaurant.supply_quota[item]=4
	return {"ok":true,"code":"ok","state":candidate,"events":events}

static func _produce(data:Dictionary,recipe_id:String,day:int) -> Dictionary:
	# All ingredient purchases and capacity checks belong to one disposable candidate.
	var candidate=data.duplicate(true)
	var recipe:Dictionary=Recipes.get_recipe(recipe_id)
	var inv=_inventory(candidate.life.town.restaurant.slots)
	var events:Array=[]
	var cost=0
	for item in recipe.inputs:
		var missing=maxi(0,int(recipe.inputs[item])-inv.count_item(item))
		if missing==0:continue
		var bill=missing*int(INPUT_PRICES[item])
		var code:=Accounts.exchange(candidate,"restaurant","market",item,missing,bill)
		if code!="ok":return _failure("missing_inputs" if code=="insufficient_stock" else code)
		cost+=bill
		events.append(_event(day,"purchase","restaurant","market",{item:missing},bill,"restaurant_inputs"))
		inv=_inventory(candidate.life.town.restaurant.slots)
	for item in recipe.inputs:
		if not inv.remove_item(item,int(recipe.inputs[item])):return _failure("invalid_state")
	for item in recipe.outputs:
		if inv.add(item,int(recipe.outputs[item]))!=int(recipe.outputs[item]):return _failure("inventory_full")
	candidate.life.town.restaurant.slots=inv.snapshot()
	var production=_event(day,"production","restaurant","restaurant",recipe.outputs,0,recipe_id)
	production.inputs=recipe.inputs.duplicate(true);production.outputs=recipe.outputs.duplicate(true)
	events.append(production)
	return {"ok":true,"code":"ok","state":candidate,"events":events,"cost":cost}
