extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
var s=Support.new()
func _initialize() -> void:call_deferred("run")
func run() -> void:
 var trial=load("res://dev/character_headwear_trial.tscn").instantiate();root.add_child(trial)
 s.check("four_actual_headwear_samples",trial.head_ready and trial.head_library.samples.size()==4)
 s.check("actual_load_no_error",trial.head_error=="" and trial.sample_error=="" and trial.load_error=="")
 if not s.passed():print("HEADWEAR_ERROR ",trial.head_error," / ",trial.sample_error," / ",trial.load_error)
 if s.passed():
  for sample in trial.head_library.samples:
   trial.select_sample(sample.id);trial.review_panel.set_playing(false)
   for state in trial.HeadLibrary.STATES:
    s.check(sample.id+state+"_state_selects",trial.select_head_state(state))
    s.check(sample.id+state+"_idle_matches",trial.pose.texture==sample.idle_by_state[state])
    trial.review_panel.preview_phase_ms=0;trial.review_panel.refresh_preview()
    for index in range(4):
     s.check(sample.id+state+str(index)+"_same_real_pose",trial.review_panel.motion_view.texture==sample.textures_by_state[state][index])
     trial.review_panel.step_frame()
 print("HEADWEAR_ACTUAL checks=",s.checks.size()," passed=",s.passed());quit(0 if s.passed() else 1)
