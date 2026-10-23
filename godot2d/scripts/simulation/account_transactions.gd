extends RefCounted
# Mutates only an exclusively owned candidate, and only after all prechecks pass.
const Inventory=preload("res://scripts/inventory/inventory_container.gd")
const MAX_CASH=1000000000

static func account(data:Dictionary,id:String) -> Dictionary:
	if id=="player":return data.life
	if id=="market":return data.life.accounts.market
	if not data.life.has("town"):return {}
	if id=="restaurant":return data.life.town.restaurant
	if id=="supply_depot":return data.life.town.supply_depot
	return data.life.town.households.get(id,{})

static func cash(data:Dictionary,id:String) -> int:
	return int(account(data,id).get("wallet" if id=="player" else "cash",0))

static func _set_cash(data:Dictionary,id:String,value:int) -> void:
	account(data,id)["wallet" if id=="player" else "cash"]=value

static func money_code(data:Dictionary,payer:String,payee:String,amount:int) -> String:
	if account(data,payer).is_empty() or account(data,payee).is_empty():return "unknown_account"
	if amount<0 or payer==payee:return "invalid_request"
	if cash(data,payer)<amount:return "insufficient_funds"
	if cash(data,payee)>MAX_CASH-amount:return "invalid_state"
	return "ok"

static func move_cash(data:Dictionary,payer:String,payee:String,amount:int) -> String:
	var code=money_code(data,payer,payee,amount)
	if code!="ok":return code
	_set_cash(data,payer,cash(data,payer)-amount)
	_set_cash(data,payee,cash(data,payee)+amount)
	return "ok"

static func _inventory(data:Dictionary,id:String):
	var slots:Array=data.bag if id=="player" else account(data,id).slots
	var inv=Inventory.new(slots.size())
	if not inv.restore_slots(slots):return null
	return inv

static func _write_slots(data:Dictionary,id:String,slots:Array) -> void:
	if id=="player":data.bag=slots
	else:account(data,id).slots=slots

# Cash flows buyer -> seller, goods seller -> buyer; quota belongs to buyer.
static func exchange(data:Dictionary,buyer:String,seller:String,item:String,amount:int,total:int,quota:Dictionary={}) -> String:
	if account(data,buyer).is_empty() or account(data,seller).is_empty():return "unknown_account"
	if amount<=0 or buyer==seller:return "invalid_request"
	var source=_inventory(data,seller)
	var target=_inventory(data,buyer)
	if source==null or target==null:return "invalid_state"
	if source.count_item(item)<amount:return "insufficient_stock"
	if target.space_for(item)<amount:return "inventory_full"
	var code=money_code(data,buyer,seller,total)
	if code!="ok":return code
	if not quota.is_empty() and int(quota.get(item,0))<amount:return "quota_exceeded"
	if not source.remove_item(item,amount) or target.add(item,amount)!=amount:return "invalid_state"
	move_cash(data,buyer,seller,total)
	_write_slots(data,seller,source.snapshot())
	_write_slots(data,buyer,target.snapshot())
	if not quota.is_empty():quota[item]-=amount
	return "ok"
