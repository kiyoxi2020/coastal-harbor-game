extends SceneTree
const State = preload("res://scripts/player_state.gd")
const Rules = preload("res://scripts/simulation/life_rules.gd")
const Support = preload("res://tests/life_test_support.gd")
var s := Support.new()
func _initialize() -> void:
	var state = State.new()
	var data: Dictionary = state.to_data(Vector2(330,250))
	s.check("current_v4", data.version == 4)
	s.check("sixteen_independent_cells", data.life.plots.size() == 16 and data.life.plots.has("garden_a:0:0") and data.life.plots.has("garden_b:3:1"))
	var result := Rules.plan(data, "hoe", {"cell_id":"garden_a:0:0"}, 1)
	s.check("hoe_single_cell", result.ok)
	if result.ok:
		data = result.state
		s.check("only_target_tilled", data.life.plots["garden_a:0:0"].tilled and not data.life.plots["garden_a:1:0"].tilled)
		result = Rules.plan(data,"water",{"cell_id":"garden_a:0:0"},2)
		s.check("water_empty_soil",result.ok)
		if result.ok:
			data = result.state
			state.restore(data)
			state.bag.add("lettuce_seed",2)
			data = state.to_data(Vector2(330,250))
			result = Rules.plan(data,"plant",{"cell_id":"garden_a:0:0","crop_id":"lettuce"},3)
			s.check("plant_preserves_water", result.ok and result.state.life.plots["garden_a:0:0"].watered)
	print("GRID checks=",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
