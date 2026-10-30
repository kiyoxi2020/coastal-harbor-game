extends "res://tests/characters/capture_registered_actions_world.gd"
## Executes the frozen full-capture transition list through real input/physics.
var transitions:Array=[]
var transition_rows:Array=[]
var transition_watch:=""
var last_native_draw:=0
var finishing:=false
func draw_frame() -> void:
 await super.draw_frame();last_native_draw=Time.get_ticks_msec()
func draw_watchdog() -> void:
 if not finishing and Time.get_ticks_msec()-last_native_draw>30000:
  s.check("native_draw_wait_timeout",false);finish()
func physics_sample(delta:float) -> void:
 if transition_watch=="":return
 transition_rows.append({"transition":transition_watch,"physics_frame":Engine.get_physics_frames(),
  "delta_f64":exact(delta),"state":trial.active_action_state(),
  "position_f64":[exact(trial.actor.position.x),exact(trial.actor.position.y)],
  "phase_f64":exact(trial.phase_ms),"stable_remaining_f64":exact(trial.stable_remaining_ms),
  "pending_locomotion_action":trial.pending_locomotion_action,
  "texture":texture_identity.get(trial.pose.texture.get_instance_id(),{})})
func release_movement() -> void:
 for direction in ["south","west","east","north"]:Input.action_release("trial_walk_"+direction)
func wait_for_action(action:String,direction:String) -> bool:
 var deadline=Time.get_ticks_msec()+10000
 while (trial.current_action!=action or trial.facing!=direction) and Time.get_ticks_msec()<deadline:await draw_frame()
 return trial.current_action==action and trial.facing==direction
func run() -> void:
 if not evidence.begins_with("/private/tmp/coastal-") or not FileAccess.file_exists(evidence.path_join("input-contract.json")):quit(2);return
 var contract=JSON.parse_string(FileAccess.get_file_as_string(evidence.path_join("input-contract.json")))
 if not contract is Dictionary or contract.get("capture_scene")!="res://dev/characters/character_motion_lane.tscn" or not contract.get("transitions") is Array or contract.transitions.is_empty():quit(2);return
 contract_sha=FileAccess.get_sha256(evidence.path_join("input-contract.json"));started=Time.get_datetime_string_from_system(true)
 trial=load("res://dev/characters/character_motion_lane.tscn").instantiate();root.add_child(trial)
 last_native_draw=Time.get_ticks_msec()
 var watchdog=Timer.new();watchdog.wait_time=2.0;watchdog.timeout.connect(draw_watchdog);root.add_child(watchdog);watchdog.start()
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
 for transition in contract.transitions:
  if not transition is String:quit(2);return
  await inspect_transition(transition)
 release_movement();transition_watch="";finish()
func inspect_transition(id:String) -> void:
 save_json("progress.json",{"transition":id,"completed":transitions.size(),"ticks_usec":Time.get_ticks_usec(),"phase":"started"})
 var ends=id.split("-to-")
 if ends.size()!=2:s.check(id+"_valid",false);return
 var source=ends[0].split("-");var target=ends[1].split("-")
 if source.size()!=2 or target.size()!=2 or not trial.head_library.full_clips.has(ends[0]) or not trial.head_library.full_clips.has(ends[1]):s.check(id+"_available",false);return
 transition_watch="";release_movement();trial.reset_position();trial.run_requested=false;trial.facing=source[1];trial.focused=true;trial.refresh_pose()
 await physics_frame;await draw_frame()
 if source[0] in ["walk","run"]:
  trial.run_requested=source[0]=="run";Input.action_press("trial_walk_"+source[1])
  s.check(id+"_source_enters",await wait_for_action(source[0],source[1]))
 elif source[0] in ["hoe","water","harvest"]:s.check(id+"_source_starts",trial.start_farming_sample(source[0]))
 await physics_frame;await draw_frame()
 var initial=observation(ends[0],"transition-source");initial.texture=texture_identity.get(trial.pose.texture.get_instance_id(),{})
 s.check(id+"_actual_source",initial.texture.get("clip")==ends[0])
 var row_start=transition_rows.size();var event_start=trial.action_event_log.size();transition_watch=id
 release_movement()
 if target[0] in ["walk","run"]:
  trial.run_requested=target[0]=="run";Input.action_press("trial_walk_"+target[1])
 elif target[0] in ["hoe","water","harvest"]:s.check(id+"_target_starts",trial.start_farming_sample(target[0]))
 s.check(id+"_target_enters",await wait_for_action(target[0],target[1]))
 for tick in range(3):await physics_frame
 await draw_frame();transition_watch=""
 var final=observation(ends[1],"transition-target");final.texture=texture_identity.get(trial.pose.texture.get_instance_id(),{})
 s.check(id+"_actual_target",final.texture.get("clip")==ends[1])
 final.capture=actor_capture("transition-"+id)
 transitions.append({"id":id,"source":initial,"target":final,"physics_samples":transition_rows.slice(row_start),"journal":trial.action_event_log.slice(event_start)})
 save_json("progress.json",{"transition":id,"completed":transitions.size(),"ticks_usec":Time.get_ticks_usec(),"phase":"complete"})
func finish() -> void:
 if finishing:return
 finishing=true
 for path in pending_images:
  s.check(path+"_saved",pending_images[path].save_png(evidence.path_join(path))==OK);hashes[path]=FileAccess.get_sha256(evidence.path_join(path))
 pending_images.clear()
 save_json("report.json",{"kind":"coastal-registered-transition-observation-v1","scope":"Full-plan registered transitions using shared player, logical input and real physics on isolated lane. Raw state/clock/position/GPU texture and events. No OS input, physical contact, harbor or visual approval claim.","loaded_input_binding":loaded_input_binding,"input_contract_sha256":contract_sha,"started_utc":started,"finished_utc":Time.get_datetime_string_from_system(true),"renderer":DisplayServer.get_name(),"checks":s.checks,"transitions":transitions,"output_hashes":hashes})
 print("REGISTERED_TRANSITIONS checks=",s.checks.size()," passed=",s.passed()," transitions=",transitions.size());quit(0 if s.passed() else 1)
