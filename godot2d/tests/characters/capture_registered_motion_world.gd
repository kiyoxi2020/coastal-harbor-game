extends "res://tests/characters/capture_registered_candidate.gd"
## Ten uninterrupted world cycles on an isolated paving lane, same player.
## Original harbor collision/occlusion acceptance remains a separate scenario.
class PhysicsLedger extends Node:
 var callback:Callable
 func _physics_process(delta:float) -> void:callback.call(delta)

var physics_rows:Array=[]
var watching:=""
var traveled:=0.0
var previous_position:=Vector2.ZERO
var texture_identity:Dictionary={}
var ledger:PhysicsLedger
var current_clip:Dictionary={}
var world_seen:Dictionary={}
var sampled_clips:Dictionary={}
var capture_every_rendered_frame:=false

func rgba_hash(texture:Texture2D) -> String:
 var image=texture.get_image();image.convert(Image.FORMAT_RGBA8)
 var hash=HashingContext.new();hash.start(HashingContext.HASH_SHA256);hash.update(image.get_data());return hash.finish().hex_encode()
func physics_sample(delta:float) -> void:
 if watching=="":return
 var moved:float=trial.actor.position.distance_to(previous_position)
 traveled+=moved;previous_position=trial.actor.position
 var state:Dictionary=trial.active_action_state()
 physics_rows.append({"clip":watching,"physics_frame":Engine.get_physics_frames(),
  "delta_f64":exact(delta),"state":state,"phase_f64":exact(trial.phase_ms),
  "distance_f64":exact(traveled),"step_distance_f64":exact(moved),
  "position":[trial.actor.position.x,trial.actor.position.y],
  "position_f64":[exact(trial.actor.position.x),exact(trial.actor.position.y)],
  "slide_collisions":trial.actor.get_slide_collision_count(),
  "texture":texture_identity.get(trial.pose.texture.get_instance_id(),{})})
func run() -> void:
 if not evidence.begins_with("/private/tmp/coastal-") or not FileAccess.file_exists(evidence.path_join("input-contract.json")):quit(2);return
 var contract=JSON.parse_string(FileAccess.get_file_as_string(evidence.path_join("input-contract.json")))
 if not contract is Dictionary:quit(2);return
 contract_sha=FileAccess.get_sha256(evidence.path_join("input-contract.json"));started=Time.get_datetime_string_from_system(true)
 trial=load("res://dev/characters/character_motion_lane.tscn").instantiate();root.add_child(trial)
 await draw_frame();review=trial.review_panel
 s.check("native_gpu",DisplayServer.get_name()!="headless")
 s.check("same_registered_player_ready",trial.head_ready and trial.head_error=="" and trial.uses_registered_package())
 if not s.passed():print("MOTION_LOAD_ERROR ",trial.head_error);finish();return
 if not bind_loaded_input(contract):finish();return
 review.set_playing(false)
 # Precompute actual loaded GPU texture identities outside timed observation.
 for id in trial.head_library.full_clips:
  var clip:Dictionary=trial.head_library.full_clips[id]
  for i in range(clip.textures.size()):
   texture_identity[clip.textures[i].get_instance_id()]={"clip":id,"pose_id":clip.pose_ids[i],"rgba_sha256":rgba_hash(clip.textures[i])}
 observed_gpu_texture_ids=texture_identity
 ledger=PhysicsLedger.new();ledger.callback=physics_sample;ledger.process_physics_priority=10000;root.add_child(ledger)
 capture("lane-overview")
 for id in trial.head_library.full_clips:
  var clip:Dictionary=trial.head_library.full_clips[id]
  if clip.action_id in ["walk","run"]:await inspect_motion(id,clip)
 watching="";finish()
func actor_capture(name:String) -> String:
 var image:Image=root.get_texture().get_image()
 var anchor:Vector2=trial.actor.get_global_transform_with_canvas()*Vector2.ZERO
 var rect=Rect2i(Vector2i(anchor)-Vector2i(140,245),Vector2i(280,300))
 s.check(name+"_inside_viewport",Rect2i(Vector2i.ZERO,image.get_size()).encloses(rect))
 pending_images[name+".png"]=image.get_region(rect);return name+".png"
func inspect_motion(id:String,clip:Dictionary) -> void:
 watching="";trial.reset_position();trial.facing=clip.direction;trial.run_requested=clip.action_id=="run";trial.focused=true;trial.refresh_pose()
 review.select_clip(clip.direction,clip.action_id);review.set_playing(false)
 await draw_frame()
 previous_position=trial.actor.position;traveled=0;world_seen={};watching=id;current_clip=clip
 var base_speed:float=trial.head_library.runtime.movement[clip.action_id].base_world_speed
 var source_duration:=0.0
 for duration in clip.durations_ms:source_duration+=float(duration)
 var deadline=Time.get_ticks_msec()+30000
 var first:Vector2=trial.actor.position;var start_row=physics_rows.size();var draw_count:=0
 Input.action_press("trial_walk_"+clip.direction)
 while traveled/base_speed*1000<source_duration*10 and Time.get_ticks_msec()<deadline:
  await draw_frame();draw_count+=1
  var row=observation(id,"world-ten-cycles")
  var texture:Dictionary=texture_identity.get(trial.pose.texture.get_instance_id(),{})
  row.texture=texture
  var transform:Transform2D=trial.pose.get_global_transform_with_canvas()
  row.source_to_screen=[transform.x.x,transform.x.y,transform.y.x,transform.y.y,transform.origin.x,transform.origin.y]
  row.sprite_offset=[trial.pose.offset.x,trial.pose.offset.y]
  row.source_elapsed_ms=traveled/base_speed*1000
  if capture_every_rendered_frame:row.capture=actor_capture(id+"-world-"+str(rows.size()))
  if texture.get("clip")==id:
   var pose:String=texture.pose_id
   if not capture_every_rendered_frame and (not world_seen.has(pose) or draw_count%8==0):
    row.capture=actor_capture(id+"-world-"+str(rows.size()))
   world_seen[pose]=true
  rows.append(row)
 Input.action_release("trial_walk_"+clip.direction);watching="";trial.run_requested=false
 # Rendering can run much faster than physics. Wait for actual input-release
 # processing, rather than assuming three draw frames include a physics tick.
 await physics_frame;await physics_frame;await draw_frame()
 var ending=observation(id,"released-to-idle")
 ending.texture=texture_identity.get(trial.pose.texture.get_instance_id(),{})
 ending.capture=actor_capture(id+"-ending-idle");rows.append(ending)
 s.check(id+"_ten_uninterrupted_world_cycles",traveled/base_speed*1000>=source_duration*10)
 s.check(id+"_all_actual_world_textures",world_seen.size()==clip.pose_ids.size())
 var collisions:=0
 for row in physics_rows.slice(start_row):collisions+=int(row.slide_collisions)
 s.check(id+"_open_lane_unblocked",collisions==0)
 s.check(id+"_physical_travel",trial.actor.position.distance_to(first)>source_duration*base_speed*9/1000)
 s.check(id+"_matching_idle_after",trial.current_action=="idle" and trial.pose.texture==trial.head_library.full_clips["idle-"+clip.direction].textures[0])
 sampled_clips[id]={"pose_ids":clip.pose_ids,"durations_ms":clip.durations_ms,"base_world_speed":base_speed,"speed_factor":trial.speed_factor,"initial_position_f64":[exact(first.x),exact(first.y)],"distance":traveled,"source_elapsed_ms":traveled/base_speed*1000,"physics_samples":physics_rows.size()-start_row}
func flush_images() -> void:
 for path in pending_images:
  DirAccess.make_dir_recursive_absolute(evidence.path_join(path).get_base_dir())
  s.check(path+"_saved",pending_images[path].save_png(evidence.path_join(path))==OK)
  hashes[path]=FileAccess.get_sha256(evidence.path_join(path))
 pending_images.clear()
func finish() -> void:
 flush_images()
 save_json("report.json",{"kind":"coastal-registered-motion-world-observation-v1",
  "scope":"Ten continuous physics-driven world cycles per actual registered walk/run clip on an isolated lane using existing paving and the same player. Native GPU texture identities, exact physics deltas and source-to-screen transforms recorded. No strict contact, original harbor obstacle, full24 farming/transition or user visual approval claim.",
  "loaded_input_binding":loaded_input_binding,"input_contract_sha256":contract_sha,"started_utc":started,"finished_utc":Time.get_datetime_string_from_system(true),
  "renderer":DisplayServer.get_name(),"checks":s.checks,"clips":sampled_clips,"physics_samples":physics_rows,"samples":rows,"output_hashes":hashes})
 print("REGISTERED_WORLD_NATIVE checks=",s.checks.size()," passed=",s.passed()," physics_rows=",physics_rows.size()," captures=",hashes.size())
 quit(0 if s.passed() else 1)
