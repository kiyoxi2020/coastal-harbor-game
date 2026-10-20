extends "res://tests/test_life_crafting_native.gd"
func _initialize():
 native_evidence="/private/tmp/coastal-P09-art-native"
 native_save="/private/tmp/coastal-P09-art-native-save"
 call_deferred("run")
func finish():
 if not support.passed():super.finish();return
 for i in range(5):await process_frame
 var tools=w.get_node("FarmTools")
 tools.select_tool("water")
 var button=tools.get_node("Panel/Tools/Fertilize")
 check("toolbar_same_fertilizer",button.icon==preload("res://scripts/ui/trade_item.gd").PRODUCTS.marine_fertilizer and button.text=="5 ×1")
 await capture("07-fertilizer-toolbar")
 w.journal.show_page("bag")
 await capture("08-shared-product-icons")
 check("bag_counts",w.foraging.bag.count_item("clam_salad")==1 and w.foraging.bag.count_item("snail_stew")==2 and w.foraging.bag.count_item("marine_fertilizer")==1)
 super.finish()
