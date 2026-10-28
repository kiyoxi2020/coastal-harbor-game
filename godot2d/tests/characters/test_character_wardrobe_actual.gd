extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
var s:=Support.new()
func _initialize() -> void:call_deferred("run")
func run() -> void:
 var trial=load("res://dev/characters/character_wardrobe_trial.tscn").instantiate();root.add_child(trial)
 s.check("actual_five_samples_loaded",trial.sample_library.samples.size()==5)
 s.check("json_times_match_integer_parent",trial.sample_error=="")
 s.check("initial_sample_selected",trial.selected_sample=="walk-west")
 if s.passed():
  for sample in trial.sample_library.samples:
   trial.select_sample(sample.id)
   s.check(sample.id+"_selects_matching_idle",trial.pose.texture==sample.idle_texture and trial.selected_sample==sample.id)
   trial.review_panel.set_playing(false);trial.review_panel.preview_phase_ms=0;trial.review_panel.refresh_preview()
   s.check(sample.id+"_actual_texture_overlay",trial.review_panel.motion_view.texture==sample.textures[0])
 print("WARDROBE_ACTUAL checks=",s.checks.size()," passed=",s.passed());quit(0 if s.passed() else 1)
