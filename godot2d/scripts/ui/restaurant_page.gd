extends Control
const Rules=preload("res://scripts/simulation/life_rules.gd")
const Catalog=preload("res://scripts/inventory/item_catalog.gd")
const Inventory=preload("res://scripts/inventory/inventory_container.gd")
const Navigation=preload("res://scripts/ui/keyboard_navigation.gd")
const ITEMS=["clam","snail","lettuce","tomato","clam_salad","snail_stew"]
const STATUS_NAMES={"closed":"暂停营业","trial":"试营业","operating":"正式营业"}
const REASON_NAMES={"missing_inputs":"缺少配方原料","inventory_full":"餐馆库存空间不足","depot_empty":"补给仓已无此原料","household_budget":"家庭预算不足","external_fund_exhausted":"民生基金耗尽","insufficient_staff":"人手不足","no_staff":"尚无已付薪员工","insufficient_funds":"经营资金不足","insufficient_stock":"原料不足","no_inputs":"原料不足","no_customers":"没有可消费家庭","household_funds":"家庭预算不足","no_meals":"成品不足","unmet_food":"部分家庭未吃到餐食"}
var journal
var item_id:="clam"
var submitting:=false
var wait_release:=false
var request_id:=0
var request_kind:=""
var request_args:Dictionary={}
var message:=""
var catalog:=Catalog.new()
func _ready() -> void:
	journal=get_parent().get_parent()
	for index in ITEMS.size():
		var button=$Surface/SupplyItems.get_child(index)
		button.pressed.connect(select_item.bind(ITEMS[index]))
		button.focus_entered.connect(select_item.bind(ITEMS[index]))
	$Surface/Quantity.value_changed.connect(func(_amount):render())
	$Surface/FundingAmount.value_changed.connect(func(_amount):render())
	for field in [$Surface/Quantity,$Surface/FundingAmount]:
		field.get_line_edit().focus_mode=Control.FOCUS_ALL
		field.get_line_edit().editable=true
	$Surface/Supply.pressed.connect(submit.bind("supply"))
	$Surface/Fund.pressed.connect(submit.bind("fund_restaurant"))
	$Surface/Open.pressed.connect(submit.bind("open_restaurant"))
	$Surface/Close.pressed.connect(close)
	$Surface/Return.pressed.connect(return_to_item)
	$Surface/Minus.pressed.connect(adjust.bind("Quantity",-1))
	$Surface/Plus.pressed.connect(adjust.bind("Quantity",1))
	$Surface/FundingLess.pressed.connect(adjust.bind("FundingAmount",-1))
	$Surface/FundingMore.pressed.connect(adjust.bind("FundingAmount",1))
func open() -> void:
	request_id=0
	request_kind=""
	request_args={}
	message=""
	wait_release=Input.is_action_pressed("inspect")
func select_item(id:String) -> void:
	if submitting or id not in ITEMS:return
	if item_id!=id:message=""
	item_id=id
	render()
func adjust(field:String,amount:int) -> void:
	if not submitting:$Surface.get_node(field).value+=amount
func payload(kind:String) -> Dictionary:
	if kind=="supply":return {"account_id":"restaurant","item_id":item_id,"amount":int($Surface/Quantity.value)}
	if kind=="fund_restaurant":return {"amount":int($Surface/FundingAmount.value)}
	return {}
func render() -> void:
	if journal==null or journal.world==null or not is_node_ready():return
	var world=journal.world
	var state=world.foraging
	if not state.life.has("town"):return
	var restaurant:Dictionary=state.life.town.restaurant
	var stock=Inventory.new(restaurant.slots.size())
	stock.restore_slots(restaurant.slots)
	$Surface/Status.text="%s · 连好 %d / 连坏 %d 日"%[STATUS_NAMES.get(restaurant.status,restaurant.status),restaurant.good_days,restaurant.bad_days]
	$Surface/Cash.text="个人 %d G    餐馆 %d G"%[state.life.wallet,restaurant.cash]
	for index in ITEMS.size():
		var id:String=ITEMS[index]
		var row:Button=$Surface/SupplyItems.get_child(index)
		row.button_pressed=id==item_id
		row.disabled=submitting
		row.get_node("Icon").item_id=id
		row.get_node("Name").text=catalog.get_item(id).name
		row.get_node("Count").text="持有 %d · 收 %d G"%[state.bag.count_item(id),Rules.SUPPLY_PRICES[id]]
		row.tooltip_text="餐馆库存 %d · 今日还收 %d"%[stock.count_item(id),restaurant.supply_quota[id]]
	$Surface/SelectedName.text="%s · 收购单价 %d G"%[catalog.get_item(item_id).name,Rules.SUPPLY_PRICES[item_id]]
	$Surface/Stock.text="背包 %d · 餐馆 %d · 今日额度 %d"%[state.bag.count_item(item_id),stock.count_item(item_id),restaurant.supply_quota[item_id]]
	$Surface/Supply.text="供货 ×%d · 收入 %d G"%[int($Surface/Quantity.value),int($Surface/Quantity.value)*int(Rules.SUPPLY_PRICES[item_id])]
	$Surface/FundingTotal.text="从个人钱包支付 %d G · 不计营业收入"%int($Surface/FundingAmount.value)
	var data:Dictionary=state.to_data(world.player.position)
	var results={}
	for entry in {"Supply":"supply","Fund":"fund_restaurant","Open":"open_restaurant"}:
		var kind:String={"Supply":"supply","Fund":"fund_restaurant","Open":"open_restaurant"}[entry]
		results[kind]=Rules.plan(data,kind,payload(kind),int(state.life.action_seq)+1)
		$Surface.get_node(entry).disabled=submitting or not results[kind].ok
	$Surface/Quantity.editable=not submitting
	$Surface/FundingAmount.editable=not submitting
	for path in ["Close","Return","Minus","Plus","FundingLess","FundingMore"]:$Surface.get_node(path).disabled=submitting
	$Surface/Minus.disabled=submitting or $Surface/Quantity.value<=1
	$Surface/Plus.disabled=submitting or $Surface/Quantity.value>=99
	$Surface/FundingLess.disabled=submitting or $Surface/FundingAmount.value<=1
	$Surface/FundingMore.disabled=submitting or $Surface/FundingAmount.value>=1000
	$Surface/Open.text="复业 · 开始试营业" if not restaurant.enabled else "已开业 · 睡眠后自动经营"
	$Surface/Note.text=message
	if message=="" and not results.supply.ok:$Surface/Note.text=world.ACTION_MESSAGES.get(results.supply.code,"当前无法供货")
	var metrics:Dictionary=restaurant.last_metrics
	$Surface/Reasons.text="尚无经营日结。开业需库存可做一批料理；\n蛤蜊 + 生菜，或海螺 + 番茄各 1。"
	if not metrics.is_empty():
		var reasons:Array[String]=[]
		for reason in metrics.reasons:reasons.append(REASON_NAMES.get(reason,reason))
		$Surface/Reasons.text="第 %d 日 · 付薪 %d 人 · 服务 %d/%d 户\n收入 %d · 采购 %d · 工资 %d · 利润 %d G\n%s"%[metrics.day_id,metrics.paid_staff,metrics.households_served,metrics.households_total,metrics.sales_cash,metrics.purchase_cash,metrics.wage_cash,metrics.cash_profit,"；".join(reasons) if not reasons.is_empty() else "经营顺利"]
func submit(kind:String) -> void:
	if submitting or wait_release or journal.mode!="restaurant":return
	var args:=payload(kind)
	if request_id==0 or request_kind!=kind or request_args!=args:
		request_id=int(journal.world.foraging.life.action_seq)+1
		request_kind=kind
		request_args=args.duplicate(true)
	var prior_focus:Control=get_viewport().gui_get_focus_owner()
	submitting=true
	render()
	var result:Dictionary=journal.world.perform_action(kind,args,request_id)
	if result.ok:
		message={"supply":"供货完成 · 收款已存档","fund_restaurant":"个人注资完成 · 双方余额已保存","open_restaurant":"开始试营业 · 下次休息后生产"}[kind]
		request_id=0
		request_args={}
	else:message=journal.world.ACTION_MESSAGES.get(result.code,"操作未完成。")
	render()
	# Keep all mutation and close inputs gated through this pending frame.
	await get_tree().process_frame
	submitting=false
	render()
	if journal.mode!="restaurant":return
	if is_instance_valid(prior_focus) and _eligible(prior_focus):prior_focus.grab_focus()
	else:$Surface/Return.grab_focus()
func selected_button() -> Button:
	return $Surface/SupplyItems.get_child(ITEMS.find(item_id))
func focus_default() -> void:
	if submitting:return
	var focus=get_viewport().gui_get_focus_owner()
	if focus!=null and is_ancestor_of(focus) and _eligible(focus):return
	selected_button().grab_focus()
func return_to_item() -> void:
	if not submitting:selected_button().grab_focus()
func enter_actions() -> void:
	if submitting:return
	$Surface/Return.grab_focus()
	if not $Surface/Plus.disabled:$Surface/Plus.grab_focus()
func close() -> void:
	if not submitting:journal.dismiss()
func _quantity_field(focus:Control) -> SpinBox:
	for field in [$Surface/Quantity,$Surface/FundingAmount]:
		if focus==field or (focus!=null and field.is_ancestor_of(focus)):return field
	return null
func _eligible(control:Control) -> bool:
	var field:=_quantity_field(control)
	return field.editable and field.is_visible_in_tree() if field!=null else Navigation.eligible(control)
func _commit_quantity(focus:Control) -> void:
	var field:=_quantity_field(focus)
	if field!=null:
		var text:String=field.get_line_edit().text
		if text.is_valid_int():field.value=int(text)
		field.get_line_edit().text=str(int(field.value))
func _region(focus:Control) -> int:
	if focus!=null and $Surface/SupplyItems.is_ancestor_of(focus):return 0
	if focus in [$Surface/FundingLess,$Surface/FundingMore,$Surface/Fund] or _quantity_field(focus)==$Surface/FundingAmount:return 2
	if focus in [$Surface/Open,$Surface/Close]:return 3
	return 1
func back() -> void:
	if submitting:return
	if _region(get_viewport().gui_get_focus_owner())==0:close()
	else:return_to_item()
func cycle_region(reverse:bool) -> void:
	if submitting:return
	_commit_quantity(get_viewport().gui_get_focus_owner())
	var next:=posmod(_region(get_viewport().gui_get_focus_owner())+(-1 if reverse else 1),4)
	match next:
		0:return_to_item()
		1:enter_actions()
		2:$Surface/FundingAmount.get_line_edit().grab_focus()
		3:
			if not $Surface/Open.disabled:$Surface/Open.grab_focus()
			else:$Surface/Close.grab_focus()
func handle_key(event:InputEventKey) -> bool:
	var key:int=event.physical_keycode if event.physical_keycode!=0 else event.keycode
	if submitting:return true
	var directions={KEY_LEFT:Vector2i.LEFT,KEY_A:Vector2i.LEFT,KEY_RIGHT:Vector2i.RIGHT,KEY_D:Vector2i.RIGHT,KEY_UP:Vector2i.UP,KEY_W:Vector2i.UP,KEY_DOWN:Vector2i.DOWN,KEY_S:Vector2i.DOWN}
	if event.echo and not directions.has(key):return true
	if key in [KEY_E,KEY_ENTER,KEY_KP_ENTER] and wait_release:return true
	var focus=get_viewport().gui_get_focus_owner()
	var field:=_quantity_field(focus)
	if focus is LineEdit and field!=null and (key>=KEY_0 and key<=KEY_9 or key>=KEY_KP_0 and key<=KEY_KP_9 or key in [KEY_BACKSPACE,KEY_DELETE,KEY_HOME,KEY_END]):return false
	_commit_quantity(focus)
	if key==KEY_TAB:cycle_region(event.shift_pressed);return true
	if key in [KEY_ESCAPE,KEY_B]:back();return true
	if key in [KEY_E,KEY_ENTER,KEY_KP_ENTER]:
		if field!=null:
			($Surface/Fund if field==$Surface/FundingAmount else $Surface/Supply).grab_focus()
		elif _region(focus)==0:enter_actions()
		elif focus is Button and not focus.disabled:focus.pressed.emit()
		return true
	if not directions.has(key):return false
	var direction:Vector2i=directions[key]
	if field!=null and direction.x!=0:
		field.value+=direction.x
	elif _region(focus)==0:
		var index:int=ITEMS.find(item_id)
		var next:int=index+direction.x+direction.y*3
		if next>=0 and next<ITEMS.size() and (direction.x==0 or next/3==index/3):
			$Surface/SupplyItems.get_child(next).grab_focus()
	else:
		var groups=[[],[$Surface/Minus,$Surface/Quantity,$Surface/Plus,$Surface/Supply,$Surface/Return],[$Surface/FundingLess,$Surface/FundingAmount,$Surface/FundingMore,$Surface/Fund],[$Surface/Open,$Surface/Close]]
		var eligible:Array=[]
		for control in groups[_region(focus)]:
			if _eligible(control):eligible.append(control)
		if not eligible.is_empty():eligible[posmod(eligible.find(focus)+(1 if direction.x>0 or direction.y>0 else -1),eligible.size())].grab_focus()
	return true
func _process(_delta:float) -> void:
	if not Input.is_action_pressed("inspect"):wait_release=false
	if visible and journal!=null and journal.mode=="restaurant":
		$Surface/Help.text="WASD / 方向键 · E 确认 · Tab 切区 · Esc / B "+("关闭" if _region(get_viewport().gui_get_focus_owner())==0 else "返回商品")
		if submitting:$Surface/Help.text="正在保存，请稍候…"
