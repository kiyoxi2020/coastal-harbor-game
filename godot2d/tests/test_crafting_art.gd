extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
var s=Support.new()
func _initialize():call_deferred("run")
func run():
 var scene=load("res://scenes/ui/pages/craft_page.tscn").instantiate()
 s.check("kitchen_uses_image_background",scene.has_node("Surface/Artwork") and scene.get_node("Surface/Artwork").texture!=null)
 s.check("dynamic_card_source",ResourceLoader.exists("res://scenes/ui/components/recipe_card.tscn") and scene.has_node("Surface/RecipesScroll/Recipes"))
 scene.free()
 var tools=load("res://scenes/ui/farm_tools.tscn").instantiate()
 s.check("fertilizer_real_icon",tools.get_node("Panel/Tools/Fertilize").icon!=null)
 tools.free()
 print("CRAFT_ART ",s.checks.size()," passed=",s.passed())
 quit(0 if s.passed() else 1)
