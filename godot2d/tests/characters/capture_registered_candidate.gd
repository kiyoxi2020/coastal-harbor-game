extends SceneTree
## Internal observation of strict registered assets through the shared player.
## Captures visual/clock evidence; this is not the full contact acceptance gate.
const Support=preload("res://tests/life_test_support.gd")
const InputBinding=preload("res://tests/characters/registered_observation_binding.gd")
var s=Support.new()
var trial
var review
var evidence:=""
var rows:Array=[]
var hashes:Dictionary={}
var pending_images:Dictionary={}
var contract_sha:=""
var started:=""
var capture_scene:="res://dev/characters/character_headwear_trial.tscn"
var observed_gpu_texture_ids:Dictionary={}
var loaded_input_binding:Dictionary={}
func bind_loaded_input(contract:Dictionary) -> bool:
 loaded_input_binding=InputBinding.verify(trial.head_library,contract,ProjectSettings.globalize_path("res://..").simplify_path())
 loaded_input_binding.producer_script=str(get_script().resource_path)
 loaded_input_binding.capture_scene=str(trial.scene_file_path)
 var expected_script:String="res://"+str(contract.get("observer_script","")).trim_prefix("godot2d/")
 if loaded_input_binding.producer_script!=expected_script or loaded_input_binding.capture_scene!=contract.get("capture_scene"):
  loaded_input_binding.passed=false;loaded_input_binding.error="Actual producer script or scene differs"
 s.check("actual_loaded_input_matches_contract",loaded_input_binding.get("passed")==true)
 return loaded_input_binding.get("passed")==true
func actual_gpu_identity(texture:Texture2D) -> Dictionary:
 return {} if texture==null else observed_gpu_texture_ids.get(texture.get_instance_id(),{})
func bind_observed_gpu_textures() -> void:
 # Compute from actual loaded GPU images before timed observations. Never
 # infer a displayed texture identity from the requested panel pose/index.
 for id in trial.head_library.full_clips:
  var clip:Dictionary=trial.head_library.full_clips[id]
  for i in range(clip.textures.size()):
   var texture:Texture2D=clip.textures[i];var image=texture.get_image();image.convert(Image.FORMAT_RGBA8)
   var hash=HashingContext.new();hash.start(HashingContext.HASH_SHA256);hash.update(image.get_data())
   observed_gpu_texture_ids[texture.get_instance_id()]={"clip":id,"pose_id":clip.pose_ids[i],"rgba_sha256":hash.finish().hex_encode()}
func _initialize() -> void:
 for argument in OS.get_cmdline_user_args():
  if argument.begins_with("--evidence="):evidence=argument.trim_prefix("--evidence=")
  if argument.begins_with("--capture-scene="):capture_scene=argument.trim_prefix("--capture-scene=")
 call_deferred("run")
func exact(value:float) -> String:
 var bytes=PackedByteArray();bytes.resize(8);bytes.encode_double(0,value);return bytes.hex_encode()
func save_json(name:String,value:Variant) -> void:
 var f=FileAccess.open(evidence.path_join(name),FileAccess.WRITE);f.store_string(JSON.stringify(value,"  "));f.close()
func capture(name:String,control:Control=null) -> String:
 # Caller has awaited frame_post_draw: pixels and phase refer to the same frame.
 var image:Image=root.get_texture().get_image()
 if control!=null:
  var transform=control.get_global_transform_with_canvas()
  var rect=Rect2i(Vector2i(transform*Vector2.ZERO),Vector2i(transform.get_scale()*control.size))
  s.check(name+"_inside_viewport",Rect2i(Vector2i.ZERO,image.get_size()).encloses(rect))
  image=image.get_region(rect)
 var path=name+".png"
 # PNG compression and file IO occur after observation, so they cannot skip
 # short world poses or advance the clock while a frame is being saved.
 pending_images[path]=image;return path
func observation(id:String,mode:String) -> Dictionary:
 var state:Dictionary=trial.active_action_state()
 var global:Transform2D=trial.pose.get_global_transform()
 var cpu:Transform2D=trial.pose.get_global_transform_with_canvas()
 var canvas:Transform2D=cpu*global.affine_inverse()
 var snapped:bool=root.snap_2d_transforms_to_pixel
 if snapped:global.origin=global.origin.round()
 var rendered:Transform2D=canvas*global
 var actor_anchor:Vector2=trial.actor.get_global_transform_with_canvas()*Vector2.ZERO
 var actor_crop_origin:Vector2i=Vector2i(actor_anchor)-Vector2i(140,245)
 return {"clip":id,"mode":mode,"ticks_usec":Time.get_ticks_usec(),
  "process_frame":Engine.get_process_frames(),"physics_frame":Engine.get_physics_frames(),
  "process_delta_f64":exact(review.get_process_delta_time()),
  "physics_delta_f64":exact(trial.get_physics_process_delta_time()),
  "panel_phase_f64":exact(review.preview_phase_ms),"panel_phase_ms":review.preview_phase_ms,
  "panel_pose":review.current_pose_index(),"world_state":state,
  "panel_texture":actual_gpu_identity(review.motion_view.texture),
  "world_texture":actual_gpu_identity(trial.pose.texture),
  "world_elapsed_f64":exact(float(state.elapsed_ms)),
  "actor_position":[trial.actor.position.x,trial.actor.position.y],
  "actor_capture_origin_px":[actor_crop_origin.x,actor_crop_origin.y],
  "actor_position_f64":[exact(trial.actor.position.x),exact(trial.actor.position.y)],
  "pose_position":[trial.pose.position.x,trial.pose.position.y],
  "pose_scale":[trial.pose.scale.x,trial.pose.scale.y],
  "snap_2d_transforms_to_pixel":snapped,
  "render_source_to_screen":[rendered.x.x,rendered.x.y,rendered.y.x,rendered.y.y,rendered.origin.x,rendered.origin.y],
  "sprite_offset":[trial.pose.offset.x,trial.pose.offset.y],
  "texture_size_px":[trial.pose.texture.get_width(),trial.pose.texture.get_height()]}
func draw_frame() -> void:
 await process_frame
 trial.focused=true
 await RenderingServer.frame_post_draw
func run() -> void:
 if not evidence.begins_with("/private/tmp/coastal-"):quit(2);return
 var contract=evidence.path_join("input-contract.json")
 if not FileAccess.file_exists(contract):quit(2);return
 var inputs=JSON.parse_string(FileAccess.get_file_as_string(contract))
 if not inputs is Dictionary or inputs.get("capture_scene","res://dev/characters/character_headwear_trial.tscn")!=capture_scene or not capture_scene in ["res://dev/characters/character_headwear_trial.tscn","res://dev/characters/character_motion_lane.tscn"]:quit(2);return
 contract_sha=FileAccess.get_sha256(contract);started=Time.get_datetime_string_from_system(true)
 trial=load(capture_scene).instantiate();root.add_child(trial)
 await draw_frame();review=trial.review_panel
 s.check("native_gpu",DisplayServer.get_name()!="headless")
 s.check("registered_ready",trial.head_ready and trial.head_error=="" and trial.uses_registered_package())
 if s.passed() and not bind_loaded_input(inputs):finish();return
 if not s.passed():finish();return
 bind_observed_gpu_textures()
 review.set_playing(false)
 capture("overview")
 for id in trial.head_library.full_clips:
  await inspect_clip(id,trial.head_library.full_clips[id])
 finish()
func inspect_clip(id:String,clip:Dictionary) -> void:
 var action:String=clip.action_id;var direction:String=clip.direction
 review.select_clip(direction,action);review.set_playing(false)
 var slot:Control=review.motion_view.get_parent()
 for background in ["dark","light"]:
  var backdrop:ColorRect
  if background=="light":
   backdrop=ColorRect.new();backdrop.color=Color("e8e0ce");backdrop.size=slot.size
   backdrop.mouse_filter=Control.MOUSE_FILTER_IGNORE;slot.add_child(backdrop);slot.move_child(backdrop,0)
  var phase:=0.0
  for i in range(clip.pose_ids.size()):
   review.preview_phase_ms=phase;review.refresh_preview();await draw_frame()
   s.check(id+background+str(i)+"_actual_texture",review.current_pose_index()==i and review.motion_view.texture==clip.textures[i])
   var row=observation(id,"stopped-"+background)
   row.capture=capture("stills/"+id+"-"+background+"-"+str(i),slot);rows.append(row)
   phase+=float(clip.durations_ms[i])
  if backdrop!=null:backdrop.queue_free();await draw_frame()
 if action=="idle":
  trial.reset_position();trial.actor.position=Vector2(330,230);trial.facing=direction;trial.refresh_pose()
  var idle_seen:Dictionary={};var idle_deadline=Time.get_ticks_msec()+10000
  while idle_seen.size()<clip.pose_ids.size() and Time.get_ticks_msec()<idle_deadline:
   await draw_frame()
   var idle_row=observation(id,"world-idle")
   var idle_texture:Dictionary=idle_row.world_texture
   var index:int=clip.pose_ids.find(idle_texture.get("pose_id",""))
   if idle_texture.get("clip")==id and index>=0 and not idle_seen.has(index):
    idle_seen[index]=true;idle_row.capture=capture("world/"+id+"-pose-"+str(index));rows.append(idle_row)
  s.check(id+"_all_actual_world_idle_poses",idle_seen.size()==clip.pose_ids.size())
  return
 review.preview_phase_ms=0;review.refresh_preview();await draw_frame()
 var elapsed:=0.0;var last:=0.0;var seen:Dictionary={}
 var deadline=Time.get_ticks_msec()+30000
 review.set_playing(true)
 while elapsed<review.preview_duration()*10 and Time.get_ticks_msec()<deadline:
  await draw_frame()
  var current:float=review.preview_phase_ms
  elapsed+=fposmod(current-last,review.preview_duration());last=current
  var row=observation(id,"panel-continuous");row.unwrapped_ms=elapsed
  var index:int=review.current_pose_index();seen[index]=true
  if rows.size()%8==0:row.capture=capture(id+"-panel-"+str(rows.size()),slot)
  rows.append(row)
 review.set_playing(false)
 s.check(id+"_ten_panel_cycles",elapsed>=review.preview_duration()*10 and seen.size()==clip.pose_ids.size())
 trial.reset_position();trial.actor.position=Vector2(330,230);trial.facing=direction;trial.run_requested=action=="run";trial.focused=true;trial.refresh_pose()
 var initial:Vector2=trial.actor.position;var world_seen:Dictionary={}
 var begin=Time.get_ticks_msec();var world_duration=review.preview_duration()/float(trial.head_library.runtime.clips[id].playback_rate)
 if action in ["walk","run"]:
  world_duration/=trial.speed_factor;Input.action_press("trial_walk_"+direction)
 else:s.check(id+"_world_start",trial.start_farming_sample(action))
 while Time.get_ticks_msec()-begin<world_duration+250:
  await draw_frame()
  var row=observation(id,"world-continuous")
  if trial.current_action==action:
   var actual:Dictionary=row.world_texture
   var frame:int=clip.pose_ids.find(actual.get("pose_id",""))
   if actual.get("clip")==id and frame>=0 and not world_seen.has(frame):
    world_seen[frame]=true;row.capture=capture("world/"+id+"-pose-"+str(frame))
  rows.append(row)
 if action in ["walk","run"]:Input.action_release("trial_walk_"+direction)
 trial.run_requested=false
 await physics_frame;await physics_frame;await draw_frame()
 s.check(id+"_world_all_poses",world_seen.size()==clip.pose_ids.size())
 s.check(id+"_world_motion_policy",trial.actor.position.distance_to(initial)>1 if action in ["walk","run"] else trial.actor.position==initial)
 s.check(id+"_returns_matching_idle",trial.current_action=="idle" and trial.pose.texture==trial.head_library.full_clips["idle-"+direction].textures[0])
func finish() -> void:
 for path in pending_images:
  DirAccess.make_dir_recursive_absolute(evidence.path_join(path).get_base_dir())
  s.check(path+"_saved",pending_images[path].save_png(evidence.path_join(path))==OK)
  hashes[path]=FileAccess.get_sha256(evidence.path_join(path))
 pending_images.clear()
 save_json("report.json",{"kind":"coastal-registered-native-observation-v1",
  "scope":"Internal registered subset visual/clock observation: native GPU dark/light poses, ten panel cycles and one world cycle per nonidle clip. Logical inputs and focused fixture. Full 24-cell transitions, ten world cycles, strict contacts, OS input and user approval are not asserted.",
  "loaded_input_binding":loaded_input_binding,"input_contract_sha256":contract_sha,"started_utc":started,"finished_utc":Time.get_datetime_string_from_system(true),
  "renderer":DisplayServer.get_name(),"scene":capture_scene,"checks":s.checks,"samples":rows,"output_hashes":hashes})
 print("REGISTERED_NATIVE checks=",s.checks.size()," passed=",s.passed()," rows=",rows.size()," captures=",hashes.size())
 quit(0 if s.passed() else 1)
