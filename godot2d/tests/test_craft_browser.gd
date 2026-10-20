extends SceneTree
const S=preload("res://tests/life_test_support.gd")
var s=S.new()
func _initialize():
 var exists=ResourceLoader.exists("res://scripts/ui/craft_browser.gd")
 s.check("browser_module",exists)
 if not exists:quit(1);return
 var browser=load("res://scripts/ui/craft_browser.gd")
 var recipes=load("res://scripts/simulation/recipe_catalog.gd")
 var data=s.make_state()
 s.check("cooking_two",browser.filtered_ids(data,recipes.all(),"cooking","",false)==["clam_salad","snail_stew"])
 s.check("processing_one",browser.filtered_ids(data,recipes.all(),"processing","",false)==["marine_fertilizer"])
 s.check("query_name",browser.filtered_ids(data,recipes.all(),"cooking","番茄",false)==["snail_stew"])
 s.check("query_ingredient",browser.filtered_ids(data,recipes.all(),"cooking","生菜",false)==["clam_salad"])
 s.check("empty_results",browser.filtered_ids(data,recipes.all(),"cooking","没有这道菜",false).is_empty())
 s.check("short_filter",browser.filtered_ids(data,recipes.all(),"cooking","",true).is_empty())
 var state=load("res://scripts/player_state.gd").new()
 state.bag.add("clam",30);state.bag.add("lettuce",24)
 data=state.to_data(Vector2(330,250))
 var before=data.duplicate(true)
 s.check("cap20",browser.max_batches(data,"clam_salad")==20)
 s.check("query_readonly",data==before)
 # One batch fails capacity; two batches consume full ingredient stacks and work.
 for i in range(24):data.bag[i]={"id":"tomato_seed","amount":99}
 data.bag[0]={"id":"clam","amount":2};data.bag[1]={"id":"lettuce","amount":2}
 s.check("non_monotonic_capacity",browser.max_batches(data,"clam_salad")==2)
 s.check("available_via_two_batches",browser.filtered_ids(data,recipes.all(),"cooking","",true)==["clam_salad"])
 print("CRAFT_BROWSER ",s.checks.size()," passed=",s.passed())
 quit(0 if s.passed() else 1)
