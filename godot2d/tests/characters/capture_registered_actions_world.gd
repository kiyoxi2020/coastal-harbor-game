extends "res://tests/characters/capture_registered_motion_world.gd"
## Shared player, real physics ticks, ten instances per registered farm clip.
## This observer records evidence; it does not certify physical tool contact.
var farm_clips:Dictionary={}
var farm_rows:Array=[]
var farm_watching:=""
var farm_instance:=0
func physics_sample(delta:float) -> void:
 super.physics_sample(delta)
 if farm_watching=="":return
 farm_rows.append({"clip":farm_watching,"instance_id":farm_instance,"physics_frame":Engine.get_physics_frames(),
  "delta_f64":exact(delta),"elapsed_f64":exact(trial.farming_elapsed_ms),
  "state":trial.active_action_state(),"position_f64":[exact(trial.actor.position.x),exact(trial.actor.position.y)],
  "texture":texture_identity.get(trial.pose.texture.get_instance_id(),{}),
  "journal_size":trial.action_event_log.size()})
 # A renderer stall can allow several physics ticks before the next draw.
 # End the instance ledger at its actual completion tick, not at that draw.
 if trial.farming_clip.is_empty():farm_watching=""
func run() -> void:
 if not evidence.begins_with("/private/tmp/coastal-") or not FileAccess.file_exists(evidence.path_join("input-contract.json")):quit(2);return
 var contract=JSON.parse_string(FileAccess.get_file_as_string(evidence.path_join("input-contract.json")))
 if not contract is Dictionary or contract.get("capture_scene")!="res://dev/characters/character_motion_lane.tscn":quit(2);return
 capture_every_rendered_frame=contract.get("capture_every_rendered_frame",false)==true
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
 capture("lane-overview")
 for id in trial.head_library.full_clips:
  var clip:Dictionary=trial.head_library.full_clips[id]
  if clip.action_id in ["walk","run"]:await inspect_motion(id,clip)
  elif clip.action_id in ["hoe","water","harvest"]:await inspect_farm(id,clip)
  # Compression/IO only after a ten-cycle group has ended and watchers stopped.
  if capture_every_rendered_frame:flush_images()
 watching="";farm_watching="";finish()
func inspect_farm(id:String,clip:Dictionary) -> void:
 trial.reset_position();trial.facing=clip.direction;trial.run_requested=false;trial.focused=true;trial.refresh_pose()
 review.select_clip(clip.direction,clip.action_id);review.set_playing(false)
 await physics_frame;await draw_frame()
 var initial:Vector2=trial.actor.position;var instances:Array=[];var first_row=farm_rows.size();var first_event=trial.action_event_log.size()
 for repetition in range(10):
  var seen:Dictionary={};var frames=0
  s.check(id+str(repetition)+"_starts",trial.start_farming_sample(clip.action_id))
  var instance:int=trial.action_instance_id;instances.append(instance);farm_instance=instance;farm_watching=id
  var deadline=Time.get_ticks_msec()+30000
  while not trial.farming_clip.is_empty() and Time.get_ticks_msec()<deadline:
   await draw_frame();frames+=1
   var row=observation(id,"farm-world-ten-instances");row.instance_id=instance;row.repetition=repetition
   row.texture=texture_identity.get(trial.pose.texture.get_instance_id(),{})
   if capture_every_rendered_frame:row.capture=actor_capture(id+"-instance-"+str(repetition)+"-"+str(rows.size()))
   if row.texture.get("clip")==id:
    var pose:String=row.texture.pose_id
    if not capture_every_rendered_frame and not seen.has(pose):row.capture=actor_capture(id+"-instance-"+str(repetition)+"-"+str(rows.size()))
    seen[pose]=true
   rows.append(row)
  farm_watching=""
  s.check(id+str(repetition)+"_all_world_poses",seen.size()==clip.pose_ids.size())
  s.check(id+str(repetition)+"_stationary",trial.actor.position==initial)
  s.check(id+str(repetition)+"_matching_idle",trial.farming_clip.is_empty() and trial.current_action=="idle" and trial.pose.texture==trial.head_library.full_clips["idle-"+clip.direction].textures[0])
  if not trial.farming_clip.is_empty():trial.cancel_farming_sample();break
  await physics_frame;await draw_frame()
 farm_clips[id]={"pose_ids":clip.pose_ids,"durations_ms":clip.durations_ms,"playback_rate":trial.head_library.runtime.clips[id].playback_rate,"events":trial.head_library.runtime.clips[id].events,"instances":instances,"physics_rows":farm_rows.size()-first_row,"journal":trial.action_event_log.slice(first_event),"initial_position_f64":[exact(initial.x),exact(initial.y)]}
func finish() -> void:
 flush_images()
 save_json("report.json",{"kind":"coastal-registered-actions-world-observation-v1","scope":"Actual shared-player native GPU observation on an isolated lane: ten distance-driven world cycles per available walk/run clip and ten unique instances per available farm clip. Raw physics deltas, GPU textures and event journals. Available scope only; no tool-contact, harbor-obstacle, transition or user-approval claim.","capture_every_rendered_frame":capture_every_rendered_frame,"loaded_input_binding":loaded_input_binding,"input_contract_sha256":contract_sha,"started_utc":started,"finished_utc":Time.get_datetime_string_from_system(true),"renderer":DisplayServer.get_name(),"checks":s.checks,"clips":sampled_clips,"farm_clips":farm_clips,"physics_samples":physics_rows,"farm_physics_samples":farm_rows,"samples":rows,"output_hashes":hashes})
 print("REGISTERED_ACTIONS_WORLD checks=",s.checks.size()," passed=",s.passed()," farm_clips=",farm_clips.size());quit(0 if s.passed() else 1)
