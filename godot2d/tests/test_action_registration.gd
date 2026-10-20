extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
var s:=Support.new()
func _initialize() -> void:
	var data: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/player-unified-v4/metadata.json"))
	s.check("all_120_frames",data.frames.size()==120)
	s.check("one_canvas_and_root",Vector2(data.canvas[0],data.canvas[1])==Vector2(384,384) and Vector2(data.anchor[0],data.anchor[1])==Vector2(192,336) and is_equal_approx(data.world_scale,0.15))
	for action in ["walk","run","hoe","water","harvest"]:
		for direction in ["south","west","east","north"]:
			var group: Dictionary=data.groups[action+"_"+direction]
			var valid:=true
			for i in range(6):
				var frame: Dictionary=data.frames[action+"_"+direction+"_"+str(i)]
				valid=valid and frame.canvas_anchor==data.anchor and is_equal_approx(frame.normalization,group.normalization)
			s.check(action+direction+"_fixed_registration",valid)
	print("ACTION_REGISTRATION checks=",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
