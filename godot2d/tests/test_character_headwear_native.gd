extends "res://tests/test_character_wardrobe_native.gd"
## Native GPU fixtures: real control signals/logical Input actions, no OS focus claim.
var output_files:Dictionary={}
func capture_crop(name:String,control:Control) -> Image:
 await process_frame;await RenderingServer.frame_post_draw
 var screen:Image=root.get_texture().get_image()
 var transform:Transform2D=control.get_global_transform_with_canvas()
 var rect:=Rect2i(Vector2i(transform*Vector2.ZERO),Vector2i(transform.get_scale()*control.size))
 var crop:=screen.get_region(rect)
 var path:String="sequence/"+name+".png"
 check("capture_"+name,crop.save_png(evidence.path_join(path))==OK)
 output_files[path]=FileAccess.get_sha256(evidence.path_join(path));captures.append(path)
 return crop
func run() -> void:
 if not evidence.begins_with("/private/tmp/coastal-"):quit(2);return
 DirAccess.make_dir_recursive_absolute(evidence.path_join("boards"));DirAccess.make_dir_recursive_absolute(evidence.path_join("sequence"))
 var contract:=evidence.path_join("input-contract.json")
 if not FileAccess.file_exists(contract):printerr("pre-capture contract required");quit(2);return
 input_contract_sha256=FileAccess.get_sha256(contract);started_utc=Time.get_datetime_string_from_system(true)
 trial=load("res://dev/character_headwear_trial.tscn").instantiate();root.add_child(trial);review=trial.review_panel
 await focus()
 check("real_gpu",DisplayServer.get_name()!="headless")
 check("four_head_samples_loaded",trial.head_ready and trial.head_error=="" and trial.head_library.samples.size()==4)
 if not s.passed():finish();return
 check("sample_controls_fit",fits(trial.get_node("TrialUI/Samples")))
 check("head_controls_fit",fits(trial.get_node("TrialUI/Headwear")))
 check("motion_panel_fits",fits(review))
 var overview=await snapshot("overview")
 output_files["overview.png"]=FileAccess.get_sha256(evidence.path_join("overview.png"))
 for sample in trial.head_library.samples:
  for state in trial.HeadLibrary.STATES:
   await inspect_head(sample,state)
 finish()
func inspect_head(sample:Dictionary,state:String) -> void:
 var id:String=sample.id+"-"+state;var action:String=sample.data.action_id;var direction:String=sample.data.direction
 await focus();await click(trial.get_node("TrialUI/Samples/Margin/Rows/Buttons/"+sample.id))
 review.set_playing(false);review.preview_phase_ms=0;review.refresh_preview()
 await click(trial.get_node("TrialUI/Headwear/Margin/Rows/Buttons/"+state))
 check(id+"_selected",trial.selected_sample==sample.id and trial.head_state==state and review.review_action==action)
 check(id+"_idle_matches",trial.pose.texture==sample.idle_by_state[state] and review.reference_view.texture==sample.idle_by_state[state])
 var slot:Control=review.motion_view.get_parent();var refslot:Control=review.reference_view.get_parent()
 var end:Vector2=review.motion_view.position+sample.canvas_px*review.motion_view.scale
 check(id+"_canvas_fits",review.motion_view.position.x>=0 and review.motion_view.position.y>=0 and end.x<=slot.size.x+0.01 and end.y<=slot.size.y+0.01)
 for background in ["dark","light"]:
  var backdrops:Array=[]
  if background=="light":
   for target in [slot,refslot]:
    var backdrop:=ColorRect.new();backdrop.color=Color("e8e0ce");backdrop.size=target.size;backdrop.mouse_filter=Control.MOUSE_FILTER_IGNORE;target.add_child(backdrop);target.move_child(backdrop,0);backdrops.append(backdrop)
  review.preview_phase_ms=0;review.refresh_preview()
  var first:Image=await capture_crop(id+"-"+background+"-idle",refslot)
  var board:=Image.create(first.get_width()*5,first.get_height(),false,Image.FORMAT_RGBA8)
  board.blit_rect(first,Rect2i(Vector2i.ZERO,first.get_size()),Vector2i.ZERO)
  for i in range(4):
   if i>0:review.step_frame()
   check(id+"_"+background+"_pose_"+str(i),review.current_pose_index()==i and review.motion_view.texture==sample.textures_by_state[state][i])
   var picture:Image=await capture_crop(id+"-"+background+"-pose-"+str(i),slot)
   board.blit_rect(picture,Rect2i(Vector2i.ZERO,picture.get_size()),Vector2i((i+1)*first.get_width(),0))
  var path:String="boards/"+id+"-"+background+".png";board.save_png(evidence.path_join(path));output_files[path]=FileAccess.get_sha256(evidence.path_join(path))
  for backdrop in backdrops:backdrop.queue_free()
  await process_frame
 review.preview_phase_ms=0;review.set_playing(true)
 var duration:float=review.preview_duration();var last:=0.0;var elapsed:=0.0;var seen:Dictionary={}
 var started:=Time.get_ticks_msec();var last_capture:=-100;var frame_number:=0
 while elapsed<duration*10 and Time.get_ticks_msec()-started<30000:
  await process_frame;trial.focused=true
  var phase:float=review.preview_phase_ms;elapsed+=fposmod(phase-last,duration);last=phase
  var index:int=review.current_pose_index();seen[index]=true
  var row:Dictionary={"clip":sample.id,"state":state,"wall_ms":Time.get_ticks_msec(),"phase_ms":phase,"unwrapped_ms":elapsed,"pose":index}
  samples.append(row)
  if Time.get_ticks_msec()-last_capture>=180:
   RenderingServer.force_draw();var screen:Image=root.get_texture().get_image()
   var transform:Transform2D=slot.get_global_transform_with_canvas()
   var crop:=screen.get_region(Rect2i(Vector2i(transform*Vector2.ZERO),Vector2i(transform.get_scale()*slot.size)))
   var path:String="sequence/%s-cycle-%04d.png"%[id,frame_number];row.capture=path;crop.save_png(evidence.path_join(path));captures.append(path);output_files[path]=FileAccess.get_sha256(evidence.path_join(path));frame_number+=1;last_capture=Time.get_ticks_msec()
 review.set_playing(false)
 check(id+"_ten_panel_cycles",elapsed>=duration*10 and seen.size()==4)
 # Check state selection in the middle of a real world action, restoring it without resetting.
 trial.reset_position();trial.facing=direction;trial.focused=true
 var initial:Vector2=trial.actor.position;var world_seen:Dictionary={};var world_started:=Time.get_ticks_msec()
 if action=="run":Input.action_press("trial_walk_"+direction)
 else:check(id+"_tool_starts",trial.start_farming_sample(action))
 var changed:=false
 while Time.get_ticks_msec()-world_started<int(1600 if action=="run" else duration+300):
  await physics_frame;trial.focused=true
  var index:int=-1
  if action=="run" and trial.current_action=="run":index=trial.clips.run[direction].find(trial.current_frame())
  elif not trial.farming_clip.is_empty():index=trial.farming_pose_index()
  if index>=0 and not world_seen.has(index):
   RenderingServer.force_draw();var image:Image=root.get_texture().get_image();var origin:Vector2=trial.actor.get_global_transform_with_canvas()*Vector2.ZERO
   var crop:=image.get_region(Rect2i(Vector2i(origin)-Vector2i(150,270),Vector2i(300,320)))
   var path:String="sequence/"+id+"-world-"+str(index)+".png";crop.save_png(evidence.path_join(path));output_files[path]=FileAccess.get_sha256(evidence.path_join(path));captures.append(path);world_seen[index]=true
  if index>=0 and not changed:
   var clock:float=trial.phase_ms;var tool_clock:float=trial.farming_elapsed_ms
   trial.select_head_state("bare" if state!="bare" else "hair_hat");trial.select_head_state(state)
   check(id+"_live_switch_keeps_clock",clock==trial.phase_ms and tool_clock==trial.farming_elapsed_ms)
   changed=true
 if action=="run":Input.action_release("trial_walk_"+direction)
 await physics_frame;await physics_frame
 check(id+"_all_world_poses",world_seen.size()==4)
 check(id+"_motion_policy",trial.actor.position.distance_to(initial)>10 if action=="run" else trial.actor.position==initial)
 check(id+"_ends_matching_idle",trial.current_action=="idle" and trial.pose.texture==sample.idle_by_state[state])
func finish() -> void:
 var clips:Dictionary={}
 if is_instance_valid(trial):
  for sample in trial.head_library.samples:clips[sample.id]={"sample_sha256":sample.sample_sha256,"pose_ids":sample.pose_ids,"durations_ms":sample.durations_ms,"states":trial.HeadLibrary.STATES}
 var report:Dictionary={"scope":"Four sampled headwear action/direction recipes, four head states. Native GPU dark/light stopped poses, ten panel cycles per state, world run physics and tool one-shots, live state switches. Signals/handlers/logical Input actions; focused fixture true. No OS keyboard/mouse or WM focus verification, no user visual acceptance.","input_contract_sha256":input_contract_sha256,"started_utc":started_utc,"finished_utc":Time.get_datetime_string_from_system(true),"catalog_sha256":trial.head_library.catalog_sha256 if is_instance_valid(trial) else "","clips":clips,"checks":s.checks,"samples":samples,"captures":captures,"output_hashes":output_files}
 save_json(evidence.path_join("report.json"),report)
 print("HEADWEAR_NATIVE checks=",s.checks.size()," passed=",s.passed()," samples=",samples.size()," captures=",captures.size());quit(0 if s.passed() else 1)
