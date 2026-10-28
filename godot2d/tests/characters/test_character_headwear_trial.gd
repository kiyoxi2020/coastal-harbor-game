extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
var s=Support.new()
func _initialize() -> void:call_deferred("run")
func run() -> void:
 var path="res://dev/characters/character_headwear_trial.tscn"
 s.check("headwear_scene_exists",ResourceLoader.exists(path))
 if not s.passed():quit(1);return
 var trial=load(path).instantiate()
 trial.head_catalog_override="/private/tmp/coastal-headwear-no-catalog.json"
 root.add_child(trial)
 s.check("missing_catalog_rejected",trial.head_error!="" and not trial.head_ready)
 s.check("missing_catalog_blocks_movement",trial.movement_input()==Vector2.ZERO)
 s.check("missing_catalog_blocks_tools",not trial.start_farming_sample("hoe"))
 s.check("missing_catalog_blocks_selection",not trial.select_head_state("hat"))
 # Isolated synthetic textures exercise the real switch path, never visual evidence.
 trial.load_error="";trial.head_error=""
 for original in trial.sample_library.samples:
  if original.id=="walk-west":continue
  var by_state={};var idles={}
  for state in ["bare","hair","hat","hair_hat"]:
   by_state[state]=[]
   for texture in original.textures:
    by_state[state].append(ImageTexture.create_from_image(texture.get_image()))
   idles[state]=ImageTexture.create_from_image(original.idle_texture.get_image())
  trial.head_library.samples.append({"id":original.id,"textures_by_state":by_state,"idle_by_state":idles})
 trial.head_ready=true
 for sample in trial.head_library.samples:
  trial.select_sample(sample.id);trial.review_panel.set_playing(false)
  trial.review_panel.preview_phase_ms=123.0;trial.phase_ms=115.0;trial.focused=true
  if sample.id!="run-east":s.check(sample.id+"_starts_tool",trial.start_farming_sample(sample.id.split("-")[0]));trial.farming_elapsed_ms=75.0
  var world_phase=trial.phase_ms;var tool_phase=trial.farming_elapsed_ms;var panel_phase=trial.review_panel.preview_phase_ms;var position_before=trial.actor.position
  for state in ["hair","hat","hair_hat","bare"]:
   s.check(sample.id+state+"_switches",trial.select_head_state(state))
   s.check(sample.id+state+"_preserves_phase",trial.phase_ms==world_phase and trial.farming_elapsed_ms==tool_phase and trial.review_panel.preview_phase_ms==panel_phase and trial.actor.position==position_before)
   s.check(sample.id+state+"_panel_same_state",trial.review_panel.motion_view.texture==sample.textures_by_state[state][trial.review_panel.current_pose_index()])
   s.check(sample.id+state+"_idle_same_state",trial.frames.B[trial.clips.idle[trial.facing][0]]==sample.idle_by_state[state])
   if sample.id!="run-east":s.check(sample.id+state+"_tool_same_state",trial.pose.texture==sample.textures_by_state[state][trial.farming_pose_index()])
  trial.cancel_farming_sample();trial.refresh_pose()
  s.check(sample.id+"_idle_after_tool",trial.pose.texture==sample.idle_by_state.bare)
 var selected=trial.selected_sample
 trial.select_sample("walk-west")
 s.check("unsupported_sample_rejected",trial.selected_sample==selected)
 s.check("unknown_head_state_rejected",not trial.select_head_state("unknown"))
 print("HEADWEAR_TRIAL checks=",s.checks.size()," passed=",s.passed());quit(0 if s.passed() else 1)
