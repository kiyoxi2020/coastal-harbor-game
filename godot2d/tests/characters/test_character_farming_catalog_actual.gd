extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
var s:=Support.new()
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var loader=load("res://dev/characters/character_farming_review.gd").new()
	var project:=ProjectSettings.globalize_path("res://..")
	var path:=project.path_join("art/characters/reviews/farming/catalog.json")
	s.check("actual_24_pinned_catalog_load",loader.load_catalog(project,path))
	if loader.clips.size()!=24:printerr(loader.error);quit(1);return
	for action in ["hoe","water","harvest"]:
		for direction in ["south","west","east","north"]:
			for garment in ["A","B"]:
				var clip: Dictionary=loader.get_clip(action,direction,garment)
				s.check(action+direction+garment+"_real_complete",clip.textures.size()==4 and clip.pose_ids.size()==4 and clip.durations_ms.size()==4 and clip.direction==direction and clip.garment==garment)
	print("FARMING_ACTUAL checks=",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
