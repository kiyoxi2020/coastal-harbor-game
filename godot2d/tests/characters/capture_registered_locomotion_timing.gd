extends "res://tests/characters/capture_registered_actions_world.gd"
## Actual distance clock at low FPS, logical focus, public speed and restart.
var cases:Array=[]
var timing_rows:Array=[]
var timing_watch:=""
var segment:=1
func physics_sample(delta:float) -> void:
 if timing_watch=="":return
 var moved:float=trial.actor.position.distance_to(previous_position)
 traveled+=moved;previous_position=trial.actor.position
 timing_rows.append({"case":timing_watch,"segment":segment,"physics_frame":Engine.get_physics_frames(),
  "delta_f64":exact(delta),"focused":trial.focused,"speed_factor_f64":exact(trial.speed_factor),
  "phase_f64":exact(trial.phase_ms),"step_distance_f64":exact(moved),"distance_f64":exact(traveled),
  "position_f64":[exact(trial.actor.position.x),exact(trial.actor.position.y)],
  "state":trial.active_action_state(),"texture":texture_identity.get(trial.pose.texture.get_instance_id(),{}),
  "slide_collisions":trial.actor.get_slide_collision_count()})
func release_movement() -> void:
 for direction in ["south","west","east","north"]:Input.action_release("trial_walk_"+direction)
func run() -> void:
 if not evidence.begins_with("/private/tmp/coastal-") or not FileAccess.file_exists(evidence.path_join("input-contract.json")):quit(2);return
 var contract=JSON.parse_string(FileAccess.get_file_as_string(evidence.path_join("input-contract.json")))
 if not contract is Dictionary or contract.get("observer")!="locomotion-timing" or contract.get("capture_scene")!="res://dev/characters/character_motion_lane.tscn":quit(2);return
 contract_sha=FileAccess.get_sha256(evidence.path_join("input-contract.json"));started=Time.get_datetime_string_from_system(true)
 trial=load("res://dev/characters/character_motion_lane.tscn").instantiate();root.add_child(trial)
 await draw_frame();review=trial.review_panel
 s.check("native_gpu",DisplayServer.get_name()!="headless")
 s.check("same_full_player_ready",trial.head_ready and trial.head_error=="" and trial.head_library.full_package)
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
  if not clip.action_id in ["walk","run"]:continue
  for scenario in ["low-frame-rate","focus-pause","playback-rate","replay-once"]:await inspect_case(id,clip,scenario)
 timing_watch="";release_movement();finish()
func motion_segment(id:String,source_ms:float,base_speed:float) -> void:
 var before:float=traveled;var deadline=Time.get_ticks_msec()+15000
 Input.action_press("trial_walk_"+trial.facing)
 while (traveled-before)/base_speed*1000<source_ms*2 and Time.get_ticks_msec()<deadline:await draw_frame()
 s.check(timing_watch+"_segment_"+str(segment)+"_two_cycles",(traveled-before)/base_speed*1000>=source_ms*2)
 release_movement()
 for tick in range(3):await physics_frame
 await draw_frame()
func inspect_case(id:String,clip:Dictionary,scenario:String) -> void:
 timing_watch="";release_movement();trial.reset_position();trial.facing=clip.direction;trial.run_requested=clip.action_id=="run";trial.focused=true;trial.refresh_pose()
 var old_ticks=Engine.physics_ticks_per_second;var old_fps=Engine.max_fps;var old_factor:float=trial.speed_factor
 if scenario=="low-frame-rate":Engine.physics_ticks_per_second=5;Engine.max_fps=5
 if scenario=="playback-rate":trial.set_speed_factor(1.0) # The public control supports 50–100%.
 await physics_frame;await draw_frame()
 var initial:Vector2=trial.actor.position;previous_position=initial;traveled=0;segment=1
 var start=timing_rows.size();var journal_start=trial.action_event_log.size();var id_case=id+"/"+scenario;timing_watch=id_case
 var base_speed:float=trial.head_library.runtime.movement[clip.action_id].base_world_speed
 var source_ms:=0.0
 for duration in clip.durations_ms:source_ms+=float(duration)
 if scenario=="focus-pause":
  Input.action_press("trial_walk_"+clip.direction);await physics_frame;await draw_frame()
  var phase:float=trial.phase_ms;var point:Vector2=trial.actor.position
  trial.focused=false
  for tick in range(5):await physics_frame
  s.check(id_case+"_pause_retains_phase_and_position",trial.phase_ms==phase and trial.actor.position==point)
  trial.focused=true;release_movement()
 await motion_segment(id,source_ms,base_speed)
 if scenario=="replay-once":segment=2;await motion_segment(id,source_ms,base_speed)
 timing_watch=""
 s.check(id_case+"_returns_idle",trial.current_action=="idle" and trial.pose.texture==trial.head_library.full_clips["idle-"+clip.direction].textures[0])
 s.check(id_case+"_no_gameplay_events",trial.action_event_log.size()==journal_start)
 cases.append({"case":id_case,"clip":id,"scenario":scenario,"base_world_speed":base_speed,"speed_factor":trial.speed_factor,"physics_ticks_per_second":Engine.physics_ticks_per_second,"max_fps":Engine.max_fps,"pose_ids":clip.pose_ids,"durations_ms":clip.durations_ms,"initial_position_f64":[exact(initial.x),exact(initial.y)],"initial_phase_f64":exact(0.0),"physics_samples":timing_rows.slice(start),"segments":segment,"journal":trial.action_event_log.slice(journal_start),"scope":"Distance drives phase; public speed factor, not a second animation-rate multiplier. Restart releases to idle then resumes existing phase without fixture reposition or artificial clock reset."})
 trial.set_speed_factor(old_factor);Engine.physics_ticks_per_second=old_ticks;Engine.max_fps=old_fps
func finish() -> void:
 release_movement()
 save_json("report.json",{"kind":"coastal-registered-locomotion-timing-observation-v1","scope":"Same full player, eight locomotion clips times four timing scenarios. Actual deltas, positions, distance phase and loaded GPU texture identities. Logical focus, public 100% speed, stop/restart. Low FPS may skip visible poses; full normal-cycle coverage is a separate gate. No contact, OS focus, art or production approval.","loaded_input_binding":loaded_input_binding,"input_contract_sha256":contract_sha,"started_utc":started,"finished_utc":Time.get_datetime_string_from_system(true),"renderer":DisplayServer.get_name(),"checks":s.checks,"cases":cases})
 print("REGISTERED_LOCOMOTION_TIMING checks=",s.checks.size()," passed=",s.passed()," cases=",cases.size());quit(0 if s.passed() else 1)
