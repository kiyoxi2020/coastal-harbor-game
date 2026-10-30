extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
const HeadLibrary=preload("res://dev/characters/character_headwear_samples.gd")
const Construction=preload("res://dev/characters/character_construction_samples.gd")
var s=Support.new()
func _initialize() -> void:call_deferred("run")
func run() -> void:
 var project=""
 for argument in OS.get_cmdline_user_args():
  if argument.begins_with("--fixture-project="):project=argument.trim_prefix("--fixture-project=")
 s.check("isolated_fixture",project.begins_with("/private/tmp/coastal-"))
 if not s.passed():quit(1);return
 var loader=HeadLibrary.new()
 s.check("actual_padded_build_loads",loader.load_samples(project,project.path_join("art/characters/reviews/full/review.json")))
 if not s.passed():print("ENVELOPE_ERROR ",loader.error);quit(1);return
 var trial=load("res://dev/characters/character_headwear_trial.tscn").instantiate()
 trial.head_catalog_override="/private/tmp/coastal-envelope-no-legacy.json"
 root.add_child(trial);trial.set_physics_process(false);trial.head_library=loader
 s.check("same_full_player_installs",trial.install_full_package())
 var construction=Construction.new()
 var suite=JSON.parse_string(FileAccess.get_file_as_string(project.path_join("art/characters/reviews/full/review.json")))
 var manifest=JSON.parse_string(FileAccess.get_file_as_string(project.path_join(suite.manifest.manifest)))
 var head=JSON.parse_string(FileAccess.get_file_as_string(project.path_join("art/characters/"+manifest.recipe)))
 var body=JSON.parse_string(FileAccess.get_file_as_string(project.path_join("art/characters/"+head.base_recipe.file)))
 var initial:Vector2=trial.actor.position
 for canonical in body.clips:
  var id:String=canonical.action_id+"-"+canonical.direction;var actual:Dictionary=loader.full_clips[id]
  s.check(id+"_canvas",actual.canvas_px==Vector2(canonical.canvas_px[0]+24,canonical.canvas_px[1]))
  s.check(id+"_root",actual.root_anchor_px==Vector2(canonical.root_anchor_px[0]+24,canonical.root_anchor_px[1]))
  trial.cancel_farming_sample();trial.facing=canonical.direction
  if canonical.action_id in ["hoe","water","harvest"]:s.check(id+"_starts",trial.start_farming_sample(canonical.action_id))
  else:trial.current_action=canonical.action_id;trial.phase_ms=0;trial.refresh_pose()
  var root_px=Vector2(canonical.root_anchor_px[0],canonical.root_anchor_px[1])
  var expected:Vector2=trial.actor.global_position-root_px*trial.full_density*float(canonical.display_scale)
  var observed:Vector2=trial.pose.to_global(Vector2(24,0)+trial.pose.offset)
  s.check(id+"_canonical_world_position_unchanged",observed.distance_to(expected)<0.0001 and trial.actor.position==initial)
  trial.review_panel.select_clip(canonical.direction,canonical.action_id)
  var view=trial.review_panel.motion_view
  var point:Vector2=view.position+Vector2(24,0)*view.scale
  var target:Vector2=trial.review_panel.full_preview_root-root_px*trial.review_panel.full_preview_density*float(canonical.display_scale)
  s.check(id+"_canonical_preview_position_unchanged",point.distance_to(target)<0.0001 and view.texture==actual.textures[0])
 for bad in [null,[-1,0,0,0],[0.5,0,0,0],[true,0,0,0],[513,0,0,0],[0,0,0]]:
  s.check("invalid_"+str(bad),construction.output_geometry(body.clips[0],{"output_padding_px":bad}).is_empty())
 print("CONSTRUCTION_ENVELOPE checks=",s.checks.size()," passed=",s.passed())
 quit(0 if s.passed() else 1)
