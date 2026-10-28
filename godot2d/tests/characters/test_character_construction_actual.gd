extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
var s=Support.new()
func _initialize() -> void:call_deferred("run")
func run() -> void:
 var scene=load("res://dev/characters/character_headwear_trial.tscn")
 var legacy=scene.instantiate();root.add_child(legacy)
 s.check("legacy_default_run_east",legacy.head_ready and legacy.selected_sample=="run-east" and legacy.head_library.samples.size()==4)
 legacy.queue_free();await process_frame
 var project=ProjectSettings.globalize_path("res://..").simplify_path()
 var suite=project.path_join("art/characters/reviews/headwear-construction/review.json")
 s.check("actual_suite_exists",FileAccess.file_exists(suite))
 if not FileAccess.file_exists(suite):print("CONSTRUCTION_ACTUAL pending generated suite");quit(1);return
 var trial=scene.instantiate();trial.head_catalog_override=suite;root.add_child(trial)
 s.check("strict_actual_ready",trial.head_ready and trial.head_error=="" and trial.sample_error=="" and trial.load_error=="")
 if not s.passed():print("CONSTRUCTION_ACTUAL_ERROR ",trial.head_error);quit(1);return
 s.check("one_strict_sample",trial.head_library.samples.size()==1 and trial.sample_library.samples.size()==1 and trial.selected_sample=="hoe-west")
 s.check("four_manifest_bindings",trial.head_library.manifest_bindings.size()==4 and trial.head_library.suite_kind=="coastal-character-construction-review-v1")
 for button in trial.get_node("TrialUI/Samples/Margin/Rows/Buttons").get_children():
  s.check("bounded_button_"+button.name,button.visible==(button.name=="hoe-west") and (button.name=="hoe-west" or button.disabled))
 trial.select_sample("run-east");s.check("other_recipe_rejected",trial.selected_sample=="hoe-west")
 var sample=trial.head_library.samples[0];var review=trial.review_panel
 for state in trial.HeadLibrary.STATES:
  trial.cancel_farming_sample();trial.refresh_pose();review.set_playing(false)
  s.check(state+"_selects",trial.select_head_state(state))
  s.check(state+"_idle_matches",trial.pose.texture==sample.idle_by_state[state] and review.reference_view.texture==sample.idle_by_state[state])
  review.preview_phase_ms=0;review.refresh_preview()
  for index in range(4):
   s.check(state+str(index)+"_real_pose",review.motion_view.texture==sample.textures_by_state[state][index]);review.step_frame()
  trial.focused=true;s.check(state+"_tool_starts",trial.start_farming_sample("hoe"));trial.farming_elapsed_ms=75;trial.phase_ms=51;review.preview_phase_ms=123
  var position_before=trial.actor.position
  trial.select_head_state("bare" if state!="bare" else "hair_hat");trial.select_head_state(state)
  s.check(state+"_switch_keeps_clocks",trial.phase_ms==51 and trial.farming_elapsed_ms==75 and review.preview_phase_ms==123 and trial.actor.position==position_before)
  s.check(state+"_world_pose_matches",trial.pose.texture==sample.textures_by_state[state][trial.farming_pose_index()])
 trial.queue_free();await process_frame
 var failed=scene.instantiate();failed.head_catalog_override="/private/tmp/coastal-no-construction-suite.json";root.add_child(failed)
 s.check("failed_override_blocks",not failed.head_ready and failed.head_error!="" and not failed.start_farming_sample("hoe") and failed.movement_input()==Vector2.ZERO and not failed.select_head_state("hair"))
 print("CONSTRUCTION_ACTUAL checks=",s.checks.size()," passed=",s.passed());quit(0 if s.passed() else 1)
