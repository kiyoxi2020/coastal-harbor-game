extends Button
var recipe_id:=""
func bind(id:String,definition:Dictionary,available:bool,selected:bool):
	recipe_id=id
	var placeholder:bool=definition.get("placeholder",false)
	$Icon.visible=not placeholder
	$Icon.item_id="" if placeholder else str(definition.outputs.keys()[0])
	$Name.text="" if placeholder else str(definition.name)
	$Icon.material.set_shader_parameter("gray",not available)
	button_pressed=selected
	tooltip_text="" if placeholder else str(definition.name)
