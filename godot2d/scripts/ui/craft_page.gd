extends Control
const Recipes=preload("res://scripts/simulation/recipe_catalog.gd")
const Catalog=preload("res://scripts/inventory/item_catalog.gd")
const Browser=preload("res://scripts/ui/craft_browser.gd")
const Rules=preload("res://scripts/simulation/life_rules.gd")
const Card=preload("res://scenes/ui/components/recipe_card.tscn")
const Row=preload("res://scenes/ui/components/ingredient_row.tscn")
const Navigation=preload("res://scripts/ui/keyboard_navigation.gd")
var definitions:Dictionary=Recipes.all()
var category:="cooking"
var recipe_id:="clam_salad"
var visible_ids:Array[String]=[]
var cards:Dictionary={}
var submitting:=false
var message:=""
var rebuilding:=false
@onready var journal=get_parent().get_parent()
@onready var world=journal.get_parent()
func _ready():
	$Surface/Cooking.pressed.connect(select_category.bind("cooking"))
	$Surface/Processing.pressed.connect(select_category.bind("processing"))
	$Surface/Search.text_changed.connect(func(_text):message="";render())
	$Surface/Available.toggled.connect(func(_on):message="";render())
	$Surface/Batches.value_changed.connect(func(_value):message="";render())
	$Surface/Minus.pressed.connect(func():$Surface/Batches.value-=1)
	$Surface/Plus.pressed.connect(func():$Surface/Batches.value+=1)
	$Surface/Maximum.pressed.connect(maximum)
	$Surface/Submit.pressed.connect(submit)
	$Surface/Return.pressed.connect(return_to_recipes)
	$Surface/Close.pressed.connect(close)
func open():
	message=""
	rebuilding=true
	$Surface/Search.text=""
	$Surface/Batches.value=1
	rebuilding=false
func select_category(id:String):
	if submitting:return
	category=id
	rebuilding=true
	$Surface/Search.text=""
	$Surface/Batches.value=1
	rebuilding=false
	message=""
	render()
func select_recipe(id:String,focus_card:bool=false):
	if not definitions.has(id):return
	recipe_id=id
	category=definitions[id].category
	message=""
	render()
	if focus_card:focus_recipe(id)
func _card_focused(id:String):
	if id!=recipe_id:select_recipe(id)
	_scroll_to_card.call_deferred(id)
func _scroll_to_card(id:String):
	# Newly created grid cards receive their final positions at the next layout pass.
	if not is_inside_tree():return
	await get_tree().process_frame
	if not is_inside_tree():return
	if cards.has(id):$Surface/RecipesScroll.ensure_control_visible(cards[id])
func focus_recipe(id:String):
	if not cards.has(id):return
	select_recipe(id)
	cards[id].grab_focus()
	_scroll_to_card.call_deferred(id)
func focus_default():
	var focus=get_viewport().gui_get_focus_owner()
	if focus!=null and is_ancestor_of(focus) and Navigation.eligible(focus):return
	if cards.has(recipe_id):focus_recipe(recipe_id)
	else:$Surface/Search.grab_focus()
func _snapshot() -> Dictionary:
	return world.foraging.to_data(world.player.position)
func _maximum(data:Dictionary,id:String) -> int:
	return Browser.max_batches(data,id) if not Recipes.get_recipe(id).is_empty() else 0
func _sync_cards(data:Dictionary,ids:Array[String]):
	if ids!=visible_ids:
		for child in $Surface/RecipesScroll/Recipes.get_children():
			$Surface/RecipesScroll/Recipes.remove_child(child)
			child.queue_free()
		cards.clear()
		for id in ids:
			var card=Card.instantiate()
			card.name="Recipe_"+id
			$Surface/RecipesScroll/Recipes.add_child(card)
			card.pressed.connect(select_recipe.bind(id,false))
			card.focus_entered.connect(_card_focused.bind(id))
			cards[id]=card
		visible_ids=ids.duplicate()
	for id in ids:cards[id].bind(id,definitions[id],_maximum(data,id)>0,id==recipe_id)
func render():
	if rebuilding or not is_node_ready() or world==null:return
	var data:=_snapshot()
	var ids:=Browser.filtered_ids(data,definitions,category,$Surface/Search.text,$Surface/Available.button_pressed)
	var old_index:=maxi(0,visible_ids.find(recipe_id))
	if recipe_id not in ids:recipe_id=ids[mini(old_index,ids.size()-1)] if not ids.is_empty() else ""
	_sync_cards(data,ids)
	$Surface/Cooking.button_pressed=category=="cooking"
	$Surface/Processing.button_pressed=category=="processing"
	$Surface/Available.text="仅显示可制作 ✓" if $Surface/Available.button_pressed else "全部菜谱"
	$Surface/Count.text="%s · %d 个配方"%["料理" if category=="cooking" else "加工",ids.size()]
	$Surface/Empty.visible=ids.is_empty()
	for child in $Surface/IngredientScroll/Rows.get_children():
		$Surface/IngredientScroll/Rows.remove_child(child)
		child.queue_free()
	var valid:bool=not recipe_id.is_empty() and not definitions[recipe_id].get("placeholder",false)
	for path in ["OutputIcon","IngredientsTitle","IngredientScroll","BatchLabel","Batches","Minus","Plus","Maximum","Return","Submit"]:$Surface.get_node(path).visible=valid
	$Surface/Minus.disabled=not valid or submitting or $Surface/Batches.value<=1
	$Surface/Plus.disabled=not valid or submitting or $Surface/Batches.value>=20
	$Surface/Maximum.disabled=not valid or submitting or _maximum(data,recipe_id)==0
	$Surface/Submit.disabled=true
	$Surface/DetailTitle.text="请选择菜谱" if not valid else definitions[recipe_id].name
	$Surface/Note.text=message
	if not valid:return
	var recipe:Dictionary=definitions[recipe_id]
	var batches:=int($Surface/Batches.value)
	var output:String=recipe.outputs.keys()[0]
	var amount:int=int(recipe.outputs[output])*batches
	$Surface/OutputIcon.item_id=output
	for id in recipe.inputs:
		var row=Row.instantiate()
		$Surface/IngredientScroll/Rows.add_child(row)
		row.bind(id,world.foraging.bag.count_item(id),int(recipe.inputs[id])*batches)
	$Surface/Submit.text="制作 %d 份"%amount
	var result:Dictionary=Rules.plan(data,"craft",{"recipe_id":recipe_id,"batches":batches},int(data.life.action_seq)+1)
	$Surface/Submit.disabled=submitting or not result.ok
	if not result.ok and message=="":$Surface/Note.text=world.ACTION_MESSAGES.get(result.code,"此配方仅用于测试展示")
func maximum():
	if recipe_id=="" or submitting:return
	var amount:=_maximum(_snapshot(),recipe_id)
	if amount>0:$Surface/Batches.value=amount
func submit():
	if submitting or recipe_id=="" or $Surface/Submit.disabled:return
	submitting=true
	var result:Dictionary=world.perform_action("craft",{"recipe_id":recipe_id,"batches":int($Surface/Batches.value)},int(world.foraging.life.action_seq)+1)
	submitting=false
	message="制作完成 · 已存档" if result.ok else world.ACTION_MESSAGES.get(result.code,"制作失败")
	render()
	if not $Surface/Return.visible:return_to_recipes()
	elif $Surface/Submit.disabled:$Surface/Return.grab_focus()
	else:$Surface/Submit.grab_focus()
func enter_actions():
	if not $Surface/Return.visible:$Surface/Cooking.grab_focus();return
	if recipe_id!="" and not $Surface/Plus.disabled:$Surface/Plus.grab_focus()
	else:$Surface/Return.grab_focus()
func return_to_recipes():
	if cards.has(recipe_id):focus_recipe(recipe_id)
	else:$Surface/Search.grab_focus()
func close():
	if submitting:return
	if world.save_progress():journal.dismiss()
	else:message="保存失败，请重试。";render()
func _region(focus:Control) -> String:
	if focus!=null and $Surface/RecipesScroll.is_ancestor_of(focus):return "grid"
	if focus in [$Surface/Minus,$Surface/Plus,$Surface/Maximum,$Surface/Return,$Surface/Submit]:return "actions"
	return "filters"
func back():
	if submitting:return
	if visible_ids.is_empty():close();return
	var focus=get_viewport().gui_get_focus_owner()
	if _region(focus)!="grid":return_to_recipes()
	else:close()
func cycle_region(reverse:bool):
	var regions=["grid","actions","filters"]
	var index:int=regions.find(_region(get_viewport().gui_get_focus_owner()))
	var next:String=regions[posmod(index+(-1 if reverse else 1),regions.size())]
	if next=="grid":return_to_recipes()
	elif next=="actions":enter_actions()
	else:$Surface/Cooking.grab_focus()
func handle_key(event:InputEventKey) -> bool:
	var key:int=event.physical_keycode if event.physical_keycode!=0 else event.keycode
	var focus:=get_viewport().gui_get_focus_owner()
	if event.echo and key not in [KEY_LEFT,KEY_RIGHT,KEY_UP,KEY_DOWN,KEY_W,KEY_A,KEY_S,KEY_D]:return true
	if focus==$Surface/Search:
		if key==KEY_ESCAPE:
			if cards.has(recipe_id):return_to_recipes()
			else:$Surface/Cooking.grab_focus()
			return true
		if key==KEY_TAB:cycle_region(event.shift_pressed);return true
		return false
	if key==KEY_TAB:cycle_region(event.shift_pressed);return true
	if key in [KEY_ESCAPE,KEY_B]:back();return true
	if key in [KEY_E,KEY_ENTER,KEY_KP_ENTER]:
		if _region(focus)=="grid":enter_actions()
		elif focus is Button and not focus.disabled:focus.pressed.emit()
		return true
	var directions={KEY_LEFT:Vector2i.LEFT,KEY_A:Vector2i.LEFT,KEY_RIGHT:Vector2i.RIGHT,KEY_D:Vector2i.RIGHT,KEY_UP:Vector2i.UP,KEY_W:Vector2i.UP,KEY_DOWN:Vector2i.DOWN,KEY_S:Vector2i.DOWN}
	if not directions.has(key):return false
	var direction:Vector2i=directions[key]
	if _region(focus)=="grid":
		var index:int=visible_ids.find(recipe_id)
		var next:int=index+direction.x+direction.y*3
		if direction.x!=0 and next/3!=index/3:return true
		if next>=0 and next<visible_ids.size():focus_recipe(visible_ids[next])
	else:
		var controls:Array=[$Surface/Minus,$Surface/Plus,$Surface/Maximum,$Surface/Return,$Surface/Submit] if _region(focus)=="actions" else [$Surface/Cooking,$Surface/Processing,$Surface/Search,$Surface/Available,$Surface/Close]
		var eligible:Array=[]
		for control in controls:
			if Navigation.eligible(control):eligible.append(control)
		var index:int=eligible.find(focus)
		if not eligible.is_empty():
			if _region(focus)=="actions" and direction.y>0 and not $Surface/Submit.disabled:$Surface/Submit.grab_focus()
			elif _region(focus)=="actions" and direction.y<0:enter_actions()
			else:eligible[posmod(index+(1 if direction.x>0 or direction.y>0 else -1),eligible.size())].grab_focus()
	return true
