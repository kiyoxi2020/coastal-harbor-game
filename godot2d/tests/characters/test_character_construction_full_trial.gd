extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
const Library=preload("res://dev/characters/character_headwear_samples.gd")
var s=Support.new()
func _initialize() -> void:call_deferred("run")
func run() -> void:
 var project=""
 for argument in OS.get_cmdline_user_args():
  if argument.begins_with("--fixture-project="):project=argument.trim_prefix("--fixture-project=")
 s.check("temporary_fixture_only",project.begins_with("/private/tmp/coastal-"))
 if not s.passed():quit(1);return
 var library=Library.new()
 s.check("wrapper_loads_real_full_package",library.load_samples(project,project.path_join("art/characters/reviews/full/review.json")))
 var trial=load("res://dev/characters/character_headwear_trial.tscn").instantiate()
 trial.head_catalog_override="/private/tmp/coastal-no-head-catalog.json"
 root.add_child(trial);trial.set_physics_process(false)
 s.check("full_package_install_entry",trial.has_method("install_full_package"))
 if not s.passed():print("FULL_TRIAL_ERROR ",library.error);quit(1);return
 trial.head_library=library
 trial.review_panel.get_node("Margin/Rows/Actions/FarmActions").hide()
 s.check("installs_validated_package",trial.install_full_package())
 s.check("all_six_action_buttons_visible",trial.review_panel.get_node("Margin/Rows/Actions/FarmActions").visible and trial.review_panel.action_buttons.all(func(button):return button.is_visible_in_tree()))
 s.check("fixed_head_only",trial.head_state=="hair_hat" and not trial.select_head_state("bare"))
 s.check("old_samples_removed",trial.active_sample.is_empty())
 s.check("only_fixed_recipe_frames",trial.frames.keys()==["B"])
 var idle_before=trial.idle_phase_ms
 trial.focused=false;trial._physics_process(0.5)
 s.check("unfocused_world_clock_pauses",trial.idle_phase_ms==idle_before)
 trial.focused=true
 Input.action_press("trial_walk_east")
 var before=trial.actor.position
 trial._physics_process(0.05)
 Input.action_release("trial_walk_east")
 s.check("world_moves_with_full_package",trial.actor.position.x>before.x and trial.current_action=="walk" and trial.facing=="east")
 trial._physics_process(0.05)
 s.check("release_returns_matching_idle",trial.current_action=="idle" and trial.pose.texture==library.full_clips["idle-east"].textures[0])
 s.check("event_journal_available",trial.get("action_event_log") is Array)
 s.check("one_active_action_state",trial.has_method("active_action_state"))
 if not s.passed():quit(1);return
 var idle_instance=trial.active_action_state().instance_id
 trial.current_action="walk";trial.run_requested=true
 Input.action_press("trial_walk_east")
 trial._physics_process(0.01)
 s.check("walk_run_uses_declared_stable_idle",trial.current_action=="idle")
 var held=trial.actor.position
 trial._physics_process(0.04)
 s.check("stable_transition_holds_position",trial.actor.position==held and trial.current_action=="idle")
 trial._physics_process(0.2)
 s.check("stable_transition_enters_run",trial.current_action=="run")
 s.check("locomotion_state_has_new_instance",trial.active_action_state().instance_id>idle_instance and trial.active_action_state().action=="run" and trial.active_action_state().direction=="east")
 Input.action_release("trial_walk_east");trial.run_requested=false;trial.reset_position()
 for direction in ["south","west","east","north"]:
  s.check(direction+"_direction",trial.set_motion_direction(direction))
  for action in ["walk","run"]:
   s.check(direction+action+"_select",trial.set_locomotion_action(action))
   trial.phase_ms=130;trial.refresh_pose()
   s.check(direction+action+"_actual_package_texture",trial.pose.texture==library.full_clips[action+"-"+direction].textures[1])
  for action in ["hoe","water","harvest"]:
   var events_before=trial.action_event_log.size()
   s.check(direction+action+"_starts",trial.start_farming_sample(action))
   trial.advance_farming_sample(0.13)
   s.check(direction+action+"_actual_package_texture",trial.pose.texture==library.full_clips[action+"-"+direction].textures[1])
   var elapsed=trial.farming_elapsed_ms;trial.focused=false;trial.advance_farming_sample(0.4)
   s.check(direction+action+"_focus_pause",trial.farming_elapsed_ms==elapsed)
   trial.focused=true;trial.advance_farming_sample(5)
   s.check(direction+action+"_returns_canonical_idle",trial.farming_clip.is_empty() and trial.pose.texture==library.full_clips["idle-"+direction].textures[0])
   s.check(direction+action+"_one_contact_one_completion",trial.action_event_log.size()==events_before+2 and trial.action_event_log[-2].event_id=="contact" and trial.action_event_log[-1].event_id=="complete" and trial.action_event_log[-1].instance_id==trial.action_event_log[-2].instance_id)
  for action in ["idle","walk","run","hoe","water","harvest"]:
   trial.review_panel.select_clip(direction,action);trial.review_panel.set_playing(false)
   s.check(direction+action+"_preview_available",trial.review_panel.preview_available())
   s.check(direction+action+"_preview_package_texture",trial.review_panel.motion_view.texture==library.full_clips[action+"-"+direction].textures[0])
 var instances:Dictionary={}
 for event in trial.action_event_log:
  if event.event_id=="complete":instances[event.instance_id]=true
 s.check("replays_have_distinct_instances",instances.size()==12)
 trial.facing="west";trial.head_library.runtime.clips["hoe-west"].playback_rate=2.0
 var event_count=trial.action_event_log.size()
 s.check("rate_test_starts",trial.start_farming_sample("hoe"))
 trial.advance_farming_sample(0.03)
 s.check("rate_applies_to_authoritative_elapsed",is_equal_approx(trial.farming_elapsed_ms,60.0))
 trial.focused=false;trial.advance_farming_sample(5);trial.focused=true
 s.check("pause_emits_no_events",trial.action_event_log.size()==event_count)
 trial.advance_farming_sample(5)
 var completed_count=trial.action_event_log.size()
 trial.advance_farming_sample(5)
 s.check("low_frame_rate_no_duplicate_completion",completed_count==event_count+2 and trial.action_event_log.size()==completed_count)
 print("CONSTRUCTION_FULL_TRIAL checks=",s.checks.size()," passed=",s.passed())
 quit(0 if s.passed() else 1)
