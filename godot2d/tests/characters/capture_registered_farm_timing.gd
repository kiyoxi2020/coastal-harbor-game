extends "res://tests/characters/capture_registered_actions_world.gd"
## Native timing scenarios on the same player; logical focus is explicit.
var timing_cases:Array=[]
var timing_rows:Array=[]
var timing_case:=""
var timing_instance:=0
var timing_scenario:="all"
func _initialize() -> void:
 for argument in OS.get_cmdline_user_args():
  if argument.begins_with("--timing-scenario="):timing_scenario=argument.trim_prefix("--timing-scenario=")
 super._initialize()
func physics_sample(delta:float) -> void:
 if timing_case=="":return
 timing_rows.append({"case":timing_case,"instance_id":timing_instance,"physics_frame":Engine.get_physics_frames(),
  "delta_f64":exact(delta),"elapsed_f64":exact(trial.farming_elapsed_ms),"focused":trial.focused,
  "state":trial.active_action_state(),"position_f64":[exact(trial.actor.position.x),exact(trial.actor.position.y)],
  "texture":texture_identity.get(trial.pose.texture.get_instance_id(),{}),"journal_size":trial.action_event_log.size()})
 if trial.farming_clip.is_empty():timing_case=""
func run() -> void:
 if not evidence.begins_with("/private/tmp/coastal-") or not FileAccess.file_exists(evidence.path_join("input-contract.json")):quit(2);return
 var contract=JSON.parse_string(FileAccess.get_file_as_string(evidence.path_join("input-contract.json")))
 if not contract is Dictionary or contract.get("capture_scene")!="res://dev/characters/character_motion_lane.tscn" or contract.get("timing_scenario","all")!=timing_scenario or not timing_scenario in ["all","low-frame-rate","focus-pause","playback-rate","replay-once"]:quit(2);return
 contract_sha=FileAccess.get_sha256(evidence.path_join("input-contract.json"));started=Time.get_datetime_string_from_system(true)
 trial=load("res://dev/characters/character_motion_lane.tscn").instantiate();root.add_child(trial)
 await draw_frame();review=trial.review_panel
 s.check("native_gpu",DisplayServer.get_name()!="headless")
 s.check("same_registered_player_ready",trial.head_ready and trial.head_error=="" and trial.uses_registered_package())
 if not s.passed():finish();return
 if not bind_loaded_input(contract):finish();return
 review.set_playing(false)
 for id in trial.head_library.full_clips:
  var clip:Dictionary=trial.head_library.full_clips[id]
  for i in range(clip.textures.size()):texture_identity[clip.textures[i].get_instance_id()]={"clip":id,"pose_id":clip.pose_ids[i],"rgba_sha256":rgba_hash(clip.textures[i])}
 observed_gpu_texture_ids=texture_identity
 ledger=PhysicsLedger.new();ledger.callback=physics_sample;ledger.process_physics_priority=10000;root.add_child(ledger)
 for id in trial.head_library.full_clips:
  var clip:Dictionary=trial.head_library.full_clips[id]
  if not clip.action_id in ["hoe","water","harvest"]:continue
  for scenario in ["low-frame-rate","focus-pause","playback-rate","replay-once"]:
   if timing_scenario=="all" or scenario==timing_scenario:await inspect_timing(id,clip,scenario)
 timing_case="";finish()
func inspect_timing(id:String,clip:Dictionary,scenario:String) -> void:
 trial.reset_position();trial.facing=clip.direction;trial.focused=true;trial.refresh_pose()
 var ticks_before=Engine.physics_ticks_per_second;var fps_before=Engine.max_fps
 if scenario=="low-frame-rate":Engine.physics_ticks_per_second=5;Engine.max_fps=5
 var config:Dictionary=trial.head_library.runtime.clips[id];var old_rate:float=config.playback_rate
 if scenario=="playback-rate":config.playback_rate=2.0
 await physics_frame;await draw_frame()
 var initial:Vector2=trial.actor.position;var event_start=trial.action_event_log.size();var row_start=timing_rows.size()
 var case_id=id+"/"+scenario
 s.check(case_id+"_starts",trial.start_farming_sample(clip.action_id))
 timing_instance=trial.action_instance_id;var instance=timing_instance;timing_case=case_id
 if scenario=="focus-pause":
  await physics_frame;await draw_frame()
  var elapsed:float=trial.farming_elapsed_ms;var event_count=trial.action_event_log.size()
  trial.focused=false
  # SceneTree emits physics_frame before nodes run; resume only after four
  # complete paused player/ledger ticks, rather than four pre-tick signals.
  for tick in range(5):await physics_frame
  s.check(case_id+"_pause_retains_clock",trial.farming_elapsed_ms==elapsed)
  s.check(case_id+"_pause_emits_nothing",trial.action_event_log.size()==event_count)
  trial.focused=true
 var deadline=Time.get_ticks_msec()+10000
 while not trial.farming_clip.is_empty() and Time.get_ticks_msec()<deadline:
  await draw_frame()
  var row=observation(id,scenario);row.texture=texture_identity.get(trial.pose.texture.get_instance_id(),{});rows.append(row)
 timing_case=""
 s.check(case_id+"_matching_idle",trial.current_action=="idle" and trial.farming_clip.is_empty() and trial.pose.texture==trial.head_library.full_clips["idle-"+clip.direction].textures[0])
 s.check(case_id+"_stationary",trial.actor.position==initial)
 var event_end=trial.action_event_log.size()
 for tick in range(3):await physics_frame
 s.check(case_id+"_no_repeat_after_completion",trial.action_event_log.size()==event_end)
 timing_cases.append({"case":case_id,"clip":id,"scenario":scenario,"instance_id":instance,"rate":config.playback_rate,"physics_ticks_per_second":Engine.physics_ticks_per_second,"max_fps":Engine.max_fps,"pose_ids":clip.pose_ids,"durations_ms":clip.durations_ms,"events":config.events,"journal":trial.action_event_log.slice(event_start),"physics_samples":timing_rows.slice(row_start),"initial_position_f64":[exact(initial.x),exact(initial.y)]})
 config.playback_rate=old_rate;Engine.physics_ticks_per_second=ticks_before;Engine.max_fps=fps_before
func finish() -> void:
 save_json("report.json",{"kind":"coastal-registered-farm-timing-observation-v1","scope":"Same-player native timing scenarios for available farm clips: actual 5Hz physics/render, logical focus pause, explicit temporary rate2, replay with unique instance and no duplicate completion. Raw actual delta/state/GPU texture/journal. No OS focus, contact, art or full-package acceptance claim.","loaded_input_binding":loaded_input_binding,"input_contract_sha256":contract_sha,"started_utc":started,"finished_utc":Time.get_datetime_string_from_system(true),"renderer":DisplayServer.get_name(),"checks":s.checks,"cases":timing_cases,"samples":rows})
 print("REGISTERED_FARM_TIMING checks=",s.checks.size()," passed=",s.passed()," cases=",timing_cases.size());quit(0 if s.passed() else 1)
