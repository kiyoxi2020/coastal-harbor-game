extends Control
const Rules=preload("res://scripts/simulation/life_rules.gd")
const Catalog=preload("res://scripts/inventory/item_catalog.gd")
const Inventory=preload("res://scripts/inventory/inventory_container.gd")
const BUY := ["lettuce_seed","tomato_seed"]
const SELL := ["clam","snail","kelp","lettuce","tomato"]
const ITEMS := ["lettuce_seed","tomato_seed","clam","snail","kelp","lettuce","tomato"]
var journal
var direction:="buy"
var item_id:="lettuce_seed"
var submitting:=false
var wait_release:=false
var request_id:=0
var request_args:Dictionary={}
var message:=""
var catalog:=Catalog.new()
func _ready() -> void:
	journal=get_parent().get_parent()
	$Surface/BuyTab.pressed.connect(select_direction.bind("buy"))
	$Surface/SellTab.pressed.connect(select_direction.bind("sell"))
	$Surface/Quantity.value_changed.connect(func(_v):render())
	$Surface/Submit.pressed.connect(submit)
	$Surface/Close.pressed.connect(func():
		if not submitting:journal.dismiss())
	$Surface/ReturnItem.pressed.connect(return_to_item)
	$Surface/Plus.pressed.connect(func():$Surface/Quantity.value+=1)
	$Surface/Minus.pressed.connect(func():$Surface/Quantity.value-=1)
	for index in range(18):
		$Surface/Items.get_child(index).pressed.connect(select_slot.bind(index))
func selected_button() -> Button:
	var ids=BUY if direction=="buy" else SELL
	return $Surface/Items.get_child(maxi(0,ids.find(item_id)))
func action_buttons() -> Array:
	return [$Surface/Minus,$Surface/Plus,$Surface/Submit,$Surface/ReturnItem,$Surface/Info]
func enter_actions() -> void:
	if submitting:return
	for button in [$Surface/Plus,$Surface/Minus,$Surface/Submit,$Surface/ReturnItem]:
		if not button.disabled:
			button.grab_focus()
			return
func return_to_item() -> void:
	if not submitting:selected_button().grab_focus()
func back() -> void:
	if submitting:return
	var focus=get_viewport().gui_get_focus_owner()
	if focus!=null and $Surface/Items.is_ancestor_of(focus):journal.dismiss()
	else:return_to_item()
func cycle_region(reverse:bool) -> void:
	if submitting:return
	var focus=get_viewport().gui_get_focus_owner()
	var region=0
	if focus in action_buttons() or focus==$Surface/Quantity or $Surface/Quantity.is_ancestor_of(focus):region=1
	elif focus in [$Surface/BuyTab,$Surface/SellTab,$Surface/Close]:region=2
	var next=posmod(region+(-1 if reverse else 1),3)
	match next:
		0:return_to_item()
		1:enter_actions()
		2:($Surface/BuyTab if direction=="buy" else $Surface/SellTab).grab_focus()
func open() -> void:
	request_id=0
	request_args={}
	message=""
	wait_release=Input.is_action_pressed("inspect")
	render()
func select_slot(index:int) -> void:
	var ids=BUY if direction=="buy" else SELL
	if index<ids.size():select_item(ids[index])
func select_direction(value:String) -> void:
	if submitting:return
	direction=value
	item_id=BUY[0] if direction=="buy" else SELL[0]
	message=""
	render()
func select_item(id:String) -> void:
	if submitting or id not in (BUY if direction=="buy" else SELL):return
	item_id=id
	message=""
	render()
func payload() -> Dictionary:
	return {"direction":direction,"account_id":"market","item_id":item_id,"amount":int($Surface/Quantity.value)}
func render() -> void:
	if journal==null or journal.world==null:return
	var world=journal.world
	var state=world.foraging
	var market:Dictionary=state.life.accounts.market
	var stock=Inventory.new(48)
	stock.restore_slots(market.slots)
	var buying:=direction=="buy"
	var prices:Dictionary=Rules.BUY_PRICES if buying else Rules.SELL_PRICES
	var unit:int=prices[item_id]
	$Surface/Wallet.text="   %d"%state.life.wallet
	$Surface/MerchantCash.text="鱼摊      %d"%market.cash
	$Surface/BuyTab.button_pressed=buying
	$Surface/SellTab.button_pressed=not buying
	var ids=BUY if buying else SELL
	for index in range(18):
		var row:Button=$Surface/Items.get_child(index)
		var id:String=ids[index] if index<ids.size() else ""
		var populated:=id!=""
		var count:int=(stock.count_item(id) if buying else state.bag.count_item(id)) if populated else 0
		row.visible=true
		row.button_pressed=populated and id==item_id
		row.disabled=submitting or not populated
		row.text=""
		row.get_node("Icon").item_id=id
		row.get_node("Icon").unavailable=populated and count==0
		row.get_node("Count").text=str(count) if populated else ""
		row.get_node("Price/Coin").visible=populated
		row.get_node("Price").text="%d"%prices[id] if populated else ""
		row.tooltip_text=(catalog.get_item(id).name+" · "+("库存 " if buying else "持有 ")+str(count)) if populated else ""
	$Surface/SelectedName.text=catalog.get_item(item_id).name
	$Surface/SelectedName.tooltip_text="背包 %d · 鱼摊库存 %d"%[state.bag.count_item(item_id),stock.count_item(item_id)]
	$Surface/Minus.disabled=submitting or $Surface/Quantity.value<=1
	$Surface/Plus.disabled=submitting or $Surface/Quantity.value>=99
	$Surface/UnitPrice.text="单价  %d G"%unit
	$Surface/Total.text="   %d"%(unit*int($Surface/Quantity.value))
	$Surface/Stock.text="背包 %d    鱼摊库存 %d"%[state.bag.count_item(item_id),stock.count_item(item_id)]
	$Surface/Quota.text="鱼摊种子每日补足20颗" if buying else "今日还可收购 %d 个"%market.buy_quota[item_id]
	var plan:Dictionary=Rules.plan(state.to_data(world.player.position),"trade",payload(),int(state.life.action_seq)+1)
	$Surface/Submit.disabled=submitting or not plan.ok
	$Surface/Submit.text="购买" if buying else "出售"
	$Surface/ReturnItem.disabled=submitting
	$Surface/Info.disabled=submitting
	$Surface/Close.disabled=submitting
	$Surface/BuyTab.disabled=submitting
	$Surface/SellTab.disabled=submitting
	$Surface/Quantity.editable=not submitting
	$Surface/Info.tooltip_text=$Surface/SelectedName.tooltip_text+"\n"+$Surface/Quota.text+"\n只交易背包物品；箱内物品需先取出。"
	$Surface/Note.text=message if message!="" else ("" if plan.ok else world.ACTION_MESSAGES.get(plan.code,"当前不可交易。"))
func submit() -> void:
	if submitting or wait_release or journal.mode!="trade":return
	var args:=payload()
	if request_id==0 or request_args!=args:
		request_id=int(journal.world.foraging.life.action_seq)+1
		request_args=args.duplicate(true)
	var prior_focus:Control=get_viewport().gui_get_focus_owner()
	submitting=true
	var result:Dictionary=journal.world.perform_action("trade",args,request_id)
	if result.ok:
		message=("购买" if direction=="buy" else "出售")+catalog.get_item(item_id).name+" ×%d"%args.amount
		request_id=0
		request_args={}
	else:message=journal.world.ACTION_MESSAGES.get(result.code,"操作未完成。")
	render()
	# A repeated signal in the same pending frame cannot charge a second time.
	await get_tree().process_frame
	submitting=false
	render()
	if journal.mode=="trade":
		if is_instance_valid(prior_focus) and prior_focus is Button and prior_focus.is_visible_in_tree() and not prior_focus.disabled:
			prior_focus.grab_focus()
		elif prior_focus in action_buttons():$Surface/ReturnItem.grab_focus()
		else:journal.call_deferred("_focus_default")
func _process(_delta:float) -> void:
	if visible and journal!=null and journal.mode=="trade":
		var focus=get_viewport().gui_get_focus_owner()
		var browsing=focus!=null and $Surface/Items.is_ancestor_of(focus)
		$Surface/Hint.text="WASD / 方向键选择 · E 交易操作 · Tab 切区 · Esc / B 关闭" if browsing else "WASD / 方向键选择 · E 确认 · Tab 切区 · Esc / B 返回商品"
		if submitting:$Surface/Hint.text="交易处理中…"
	if not InputMap.has_action("inspect") or not Input.is_action_pressed("inspect"):wait_release=false
