extends Panel
func bind(id:String,held:int,needed:int):
	$Icon.item_id=id
	$Name.text=preload("res://scripts/inventory/item_catalog.gd").ITEMS[id].name
	$Count.text="%d / %d"%[held,needed]
