extends SceneTree
## Run from a temporary Godot project with the strict-built full fixture as its
## sibling art library, and no legacy character libraries. This exercises _ready.
const Support=preload("res://tests/life_test_support.gd")
const Library=preload("res://dev/characters/character_headwear_samples.gd")
var s=Support.new()
func _initialize() -> void:call_deferred("run")
func run() -> void:
 var project=""
 for argument in OS.get_cmdline_user_args():
  if argument.begins_with("--fixture-project="):project=argument.trim_prefix("--fixture-project=")
 s.check("temporary_fixture_only",project.begins_with("/private/tmp/coastal-"))
 s.check("fixture_is_actual_scene_resource_root",project==ProjectSettings.globalize_path("res://..").simplify_path())
 if not s.passed():quit(1);return
 for file in ["builds/locomotion-r001/manifest.json","builds/run-r001/candidate.json","reviews/farming/catalog.json","reviews/wardrobe/catalog.json","reviews/headwear/catalog.json"]:
  s.check("legacy_absent_"+file,not FileAccess.file_exists(project.path_join("art/characters/"+file)))
 var suite=project.path_join("art/characters/reviews/full/review.json")
 var library=Library.new()
 s.check("strict_full_fixture_is_valid",library.load_samples(project,suite))
 if not s.passed():print("BOOTSTRAP_FIXTURE_ERROR ",library.error);quit(1);return
 var trial=load("res://dev/characters/character_headwear_trial.tscn").instantiate()
 trial.head_catalog_override=suite
 root.add_child(trial);trial.set_physics_process(false)
 s.check("ready_loads_full_package_without_legacy",trial.head_ready and trial.head_library.full_package)
 s.check("ready_has_no_old_loader_errors",trial.head_error=="" and trial.load_error=="" and trial.sample_error=="")
 s.check("ready_never_loaded_old_character_art",trial.artifact_digest=="" and trial.run_candidate_digest=="" and trial.sample_library.samples.is_empty())
 if not s.passed():print("BOOTSTRAP_ERROR ",trial.head_error);quit(1);return
 s.check("only_fixed_recipe_frames",trial.frames.keys()==["B"] and trial.active_sample.is_empty())
 s.check("canonical_idle_is_visible",trial.pose.visible and trial.pose.texture==trial.head_library.full_clips["idle-south"].textures[0])
 s.check("shared_preview_bound",trial.review_panel.trial==trial and trial.review_panel.visible)
 s.check("shared_farming_container_initialized",trial.review_panel.farming_library!=null)
 s.check("legacy_clothing_controls_hidden",not trial.get_node("TrialUI/Panel/Margin/Rows/Controls/Short").visible and not trial.get_node("TrialUI/Panel/Margin/Rows/Controls/Long").visible)
 for direction in ["south","west","east","north"]:
  s.check(direction+"_input_registered",InputMap.has_action("trial_walk_"+direction))
  s.check(direction+"_direction",trial.set_motion_direction(direction))
  for action in ["idle","walk","run","hoe","water","harvest"]:
   trial.review_panel.select_clip(direction,action)
   s.check(direction+action+"_actual_preview",trial.review_panel.preview_available() and trial.review_panel.motion_view.texture==trial.head_library.full_clips[action+"-"+direction].textures[0])
  for action in ["hoe","water","harvest"]:
   var count=trial.action_event_log.size()
   s.check(direction+action+"_shared_one_shot_starts",trial.start_farming_sample(action))
   trial.advance_farming_sample(0.13)
   s.check(direction+action+"_actual_world_texture",trial.pose.texture==trial.head_library.full_clips[action+"-"+direction].textures[1])
   trial.advance_farming_sample(5)
   s.check(direction+action+"_completes_once",trial.action_event_log.size()==count+2 and trial.action_event_log[-1].event_id=="complete" and trial.farming_clip.is_empty())
   s.check(direction+action+"_canonical_idle_after",trial.pose.texture==trial.head_library.full_clips["idle-"+direction].textures[0])
 trial.set_speed_factor(0.5)
 s.check("shared_speed_control",is_equal_approx(trial.speed_factor,0.5) and is_equal_approx(trial.speed_slider.value,0.5))
 Input.action_press("trial_walk_east")
 var before=trial.actor.position
 trial._physics_process(0.05)
 Input.action_release("trial_walk_east")
 s.check("shared_physics_moves_full_actor",trial.actor.position.x>before.x and trial.current_action=="walk" and trial.facing=="east")
 trial._physics_process(0.05)
 s.check("shared_stop_returns_idle",trial.pose.texture==trial.head_library.full_clips["idle-east"].textures[0])
 trial.actor.position+=Vector2(10,0)
 trial.get_node("TrialUI/Panel/Margin/Rows/Controls/Reset").pressed.emit()
 s.check("shared_reset_signal_connected",trial.actor.position==trial.get_node("Start").position)
 var idle_time=trial.idle_phase_ms
 trial.focused=false;trial._physics_process(0.5);trial.focused=true
 s.check("shared_focus_pause",trial.idle_phase_ms==idle_time)
 var original_suite=FileAccess.get_file_as_string(suite)
 var invalid=JSON.parse_string(original_suite)
 invalid.manifest.sha256="0".repeat(64)
 var handle=FileAccess.open(suite,FileAccess.WRITE);handle.store_string(JSON.stringify(invalid));handle.close()
 var rejected=load("res://dev/characters/character_headwear_trial.tscn").instantiate()
 rejected.head_catalog_override=suite
 root.add_child(rejected);rejected.set_physics_process(false)
 handle=FileAccess.open(suite,FileAccess.WRITE);handle.store_string(original_suite);handle.close()
 s.check("invalid_full_package_fails_closed",not rejected.head_ready and not rejected.head_library.full_package and rejected.head_error!="" and not rejected.pose.visible)
 s.check("invalid_full_package_does_not_fallback_to_legacy",rejected.frames.is_empty() and rejected.artifact_digest=="" and rejected.sample_error=="" and not "五个样例" in rejected.head_error)
 print("CONSTRUCTION_FULL_BOOTSTRAP checks=",s.checks.size()," passed=",s.passed())
 quit(0 if s.passed() else 1)
