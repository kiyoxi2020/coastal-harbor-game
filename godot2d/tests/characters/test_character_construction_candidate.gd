extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
const Library=preload("res://dev/characters/character_headwear_samples.gd")
var s=Support.new()
func _initialize() -> void:call_deferred("run")
func save(path:String,data:Variant) -> void:
 var f=FileAccess.open(path,FileAccess.WRITE);f.store_string(JSON.stringify(data));f.close()
func run() -> void:
 var project=""
 for argument in OS.get_cmdline_user_args():
  if argument.begins_with("--fixture-project="):project=argument.trim_prefix("--fixture-project=")
 s.check("temporary_fixture",project.begins_with("/private/tmp/coastal-"))
 if not s.passed():quit(1);return
 var path=project.path_join("art/characters/reviews/candidate/review.json")
 var library=Library.new()
 s.check("bounded_candidate_loads",library.load_samples(project,path))
 if not s.passed():print("CANDIDATE_ERROR ",library.error);quit(1);return
 s.check("candidate_never_full",not library.full_package and library.get("candidate_package")==true)
 s.check("actual_two_clips_only",library.full_clips.size()==2 and library.canonical_idle.keys()==["west"] and library.samples.size()==1)
 var original=FileAccess.get_file_as_string(path);var bad=JSON.parse_string(original)
 bad.kind="coastal-character-construction-review-v1";bad.schema_version=2;bad.scope="review-only";bad.erase("capabilities");save(path,bad)
 var rejector=Library.new()
 s.check("partial_cannot_masquerade_as_full",not rejector.load_samples(project,path))
 var f=FileAccess.open(path,FileAccess.WRITE);f.store_string(original);f.close()
 var trial=load("res://dev/characters/character_headwear_trial.tscn").instantiate()
 trial.head_catalog_override="/private/tmp/coastal-missing-candidate-review.json"
 root.add_child(trial);trial.set_physics_process(false);trial.head_library=library
 s.check("shared_registered_installer",trial.has_method("install_registered_package"))
 if not s.passed():quit(1);return
 s.check("installs_actual_subset",trial.call("install_registered_package"))
 s.check("cannot_use_full_installer",not trial.install_full_package())
 s.check("truthful_scope_label",trial.get_node("TrialUI/Samples/Margin/Rows/Title").text.contains("2/24"))
 s.check("fixed_hair_hat",trial.head_state=="hair_hat" and not trial.select_head_state("bare"))
 s.check("registered_status_identity",trial.status.text.contains("海军条纹衫") and not trial.status.text.contains("诊断稿"))
 trial.focused=true
 Input.action_press("trial_walk_west");var before=trial.actor.position
 trial._physics_process(0.05);Input.action_release("trial_walk_west")
 s.check("registered_west_walk_moves",trial.actor.position.x<before.x and trial.current_action=="walk")
 trial._physics_process(0.05)
 s.check("same_canonical_idle",trial.pose.texture==library.full_clips["idle-west"].textures[0])
 trial.run_requested=true;Input.action_press("trial_walk_west");before=trial.actor.position
 trial._physics_process(0.05);Input.action_release("trial_walk_west");trial.run_requested=false
 s.check("missing_run_rejected_without_fallback",trial.actor.position==before and trial.motion_error!="")
 s.check("missing_farm_rejected",not trial.start_farming_sample("hoe"))
 trial.review_panel.select_clip("west","walk")
 s.check("preview_actual_subset_texture",trial.review_panel.motion_view.texture==library.full_clips["walk-west"].textures[0])
 print("CONSTRUCTION_CANDIDATE checks=",s.checks.size()," passed=",s.passed())
 quit(0 if s.passed() else 1)
