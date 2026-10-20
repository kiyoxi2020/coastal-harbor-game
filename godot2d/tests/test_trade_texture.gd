extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
var s=Support.new()
func _initialize():call_deferred("run")
func run():
	var page=load("res://scenes/ui/pages/trade_page.tscn").instantiate()
	var surface=page.get_node("Surface")
	s.check("gpt_background",surface.has_node("Background") and surface.get_node("Background").get("texture") is Texture2D)
	s.check("no_code_decor",not surface.has_node("Decor"))
	for name in ["BuyTab","SellTab","Submit","Minus","Plus","Close","Info"]:
		var button=surface.get_node(name)
		s.check("texture_"+name,button.get_theme_stylebox("normal") is StyleBoxTexture)
	for i in range(18):
		var button=surface.get_node("Items").get_child(i)
		s.check("texture_slot_"+str(i),button.get_theme_stylebox("normal") is StyleBoxTexture and button.get_theme_stylebox("pressed") is StyleBoxTexture)
	s.check("texture_coin",surface.get_node("Wallet/Coin") is TextureRect)
	page.free()
	print("TRADE_TEXTURE ",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
