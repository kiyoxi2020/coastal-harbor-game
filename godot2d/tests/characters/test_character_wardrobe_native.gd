extends "res://tests/characters/test_character_farming_24_native.gd"
## Real GPU rendering with deterministic control signals and logical input actions.
## This does not validate OS mouse/keyboard delivery or WM focus restoration.
func focus() -> void:
 if is_instance_valid(trial):trial.focused=true
 await process_frame
 if is_instance_valid(trial):trial.focused=true
func click(button:Button) -> void:
 if button.toggle_mode:button.button_pressed=not button.button_pressed
 button.pressed.emit();await process_frame
func run() -> void:
 if not evidence.begins_with("/private/tmp/coastal-"):quit(2);return
 DirAccess.make_dir_recursive_absolute(evidence.path_join("boards"));DirAccess.make_dir_recursive_absolute(evidence.path_join("sequence"))
 var contract:=evidence.path_join("input-contract.json")
 if not FileAccess.file_exists(contract):printerr("pre-capture contract required");quit(2);return
 input_contract_sha256=FileAccess.get_sha256(contract);started_utc=Time.get_datetime_string_from_system(true)
 trial=load("res://dev/characters/character_wardrobe_trial.tscn").instantiate();root.add_child(trial);review=trial.review_panel
 await focus()
 check("real_gpu",DisplayServer.get_name()!="headless");check("five_samples_loaded",trial.sample_library.samples.size()==5 and trial.sample_error=="")
 if not s.passed():finish();return
 check("sample_controls_fit",fits(trial.get_node("TrialUI/Samples")));check("motion_panel_fits",fits(review))
 for sample in trial.sample_library.samples:
  await inspect_sample(sample)
 finish()
func inspect_sample(sample:Dictionary) -> void:
 var id:String=sample.id;var action:String=sample.data.action_id;var direction:String=sample.data.direction
 await focus();await click(trial.get_node("TrialUI/Samples/Margin/Rows/Buttons/"+id))
 check(id+"_fixture_selected",trial.selected_sample==id and trial.facing==direction and trial.garment=="B" and review.review_action==action)
 var wrong:=InputEventKey.new();wrong.pressed=true;wrong.physical_keycode=KEY_G if action=="water" else KEY_F
 trial._unhandled_key_input(wrong)
 check(id+"_unsampled_tool_rejected",trial.farming_clip.is_empty() and trial.current_action=="idle")
 var opposite:="trial_walk_east" if direction=="west" else "trial_walk_west"
 Input.action_press(opposite)
 check(id+"_unsampled_direction_rejected",trial.movement_input()==Vector2.ZERO)
 Input.action_release(opposite)
 review.set_playing(false);review.preview_phase_ms=0;review.refresh_preview()
 var slot:Control=review.motion_view.get_parent();var refslot:Control=review.reference_view.get_parent()
 var canvas_end:Vector2=review.motion_view.position+sample.canvas_px*review.motion_view.scale
 check(id+"_complete_canvas_fits",review.motion_view.position.x>=0 and review.motion_view.position.y>=0 and canvas_end.x<=slot.size.x+0.01 and canvas_end.y<=slot.size.y+0.01)
 var board:=Image.create(2240,480,false,Image.FORMAT_RGBA8)
 for i in range(4):
  if i>0:review.step_frame()
  check(id+"_pose_"+str(i),review.current_pose_index()==i and review.motion_view.texture==sample.textures[i])
  var picture:Image=await snapshot(id+"-pose-"+str(i))
  var transform:Transform2D=slot.get_global_transform_with_canvas();var at:Vector2=transform*Vector2.ZERO;var size:Vector2=transform.get_scale()*slot.size
  board.blit_rect(picture,Rect2i(Vector2i(at),Vector2i(size)),Vector2i((i+1)*448,0))
  if i==0:
   var rt:Transform2D=refslot.get_global_transform_with_canvas()
   board.blit_rect(picture,Rect2i(Vector2i(rt*Vector2.ZERO),Vector2i(size)),Vector2i.ZERO)
 board.save_png(evidence.path_join("boards/"+id+".png"))
 var light_panels:Array=[]
 for target in [slot,refslot]:
  var backdrop:=ColorRect.new();backdrop.color=Color("e8e0ce");backdrop.size=target.size;backdrop.mouse_filter=Control.MOUSE_FILTER_IGNORE;target.add_child(backdrop);target.move_child(backdrop,0);light_panels.append(backdrop)
 var light_board:=Image.create(2240,480,false,Image.FORMAT_RGBA8)
 review.preview_phase_ms=0;review.refresh_preview()
 for i in range(4):
  if i>0:review.step_frame()
  var picture:Image=await snapshot(id+"-light-pose-"+str(i))
  var transform:Transform2D=slot.get_global_transform_with_canvas();var size:Vector2=transform.get_scale()*slot.size
  light_board.blit_rect(picture,Rect2i(Vector2i(transform*Vector2.ZERO),Vector2i(size)),Vector2i((i+1)*448,0))
  if i==0:
   var rt:Transform2D=refslot.get_global_transform_with_canvas()
   light_board.blit_rect(picture,Rect2i(Vector2i(rt*Vector2.ZERO),Vector2i(size)),Vector2i.ZERO)
 light_board.save_png(evidence.path_join("boards/"+id+"-light.png"))
 for backdrop in light_panels:backdrop.queue_free()
 await process_frame
 # Five sampled recipes retain matching idle across start/end and pause.
 check(id+"_matching_idle",trial.frames.B[trial.clips.idle[direction][0]]==sample.idle_texture)
 review.preview_phase_ms=0;review.set_playing(true)
 var duration:float=review.preview_duration();var last:=0.0;var elapsed:=0.0;var seen:Dictionary={};var pending:Array=[]
 var started:=Time.get_ticks_msec();var last_capture:=-100
 while elapsed<duration*10 and Time.get_ticks_msec()-started<30000:
  await process_frame;trial.focused=true
  var phase:float=review.preview_phase_ms;elapsed+=fposmod(phase-last,duration);last=phase
  var index:int=review.current_pose_index();seen[index]=true
  var row:Dictionary={"clip":id,"wall_ms":Time.get_ticks_msec(),"phase_ms":phase,"unwrapped_ms":elapsed,"pose":index}
  if Time.get_ticks_msec()-last_capture>=200:
   RenderingServer.force_draw();var picture:=root.get_texture().get_image();picture.resize(1280,720,Image.INTERPOLATE_NEAREST)
   var path:="sequence/%s-%05d.png"%[id,pending.size()];pending.append({"file":path,"image":picture});row.capture=path;last_capture=Time.get_ticks_msec()
  samples.append(row)
 review.set_playing(false)
 check(id+"_ten_panel_cycles",elapsed>=duration*10 and seen.size()==4)
 for item in pending:item.image.save_png(evidence.path_join(item.file));captures.append(item.file)
 # Exercise actual movement physics through logical input actions, not physical OS keys.
 var world_seen:Dictionary={};var world_pending:Array=[];var world_started:=Time.get_ticks_msec()
 if action in ["walk","run"]:
  trial.reset_position();trial.facing=direction;trial.run_requested=action=="run";trial.focused=true
  var input_action:="trial_walk_"+direction
  var initial:Vector2=trial.actor.position
  Input.action_press(input_action)
  while Time.get_ticks_msec()-world_started<1800:
   await physics_frame;trial.focused=true
   if trial.current_action==action:
    var index:int=trial.clips[action][direction].find(trial.current_frame())
    if not world_seen.has(index):record_world_pose(id,index,world_pending)
    world_seen[index]=true
  Input.action_release(input_action);await physics_frame;await physics_frame
  check(id+"_world_moves",trial.actor.position.distance_to(initial)>10)
  check(id+"_world_all_poses",world_seen.size()==4)
  check(id+"_stop_same_recipe_idle",trial.current_action=="idle" and trial.pose.texture==sample.idle_texture)
 else:
  trial.reset_position();trial.facing=direction;trial.focused=true
  check(id+"_world_starts",trial.start_farming_sample(action))
  var position_before:Vector2=trial.actor.position;var locked:=true
  while Time.get_ticks_msec()-world_started<int(duration+500):
   await physics_frame;trial.focused=true
   if not trial.farming_clip.is_empty():
    var index:int=trial.farming_pose_index()
    if not world_seen.has(index):record_world_pose(id,index,world_pending)
    world_seen[index]=true;locked=locked and trial.actor.position==position_before
  check(id+"_world_all_poses_locked_then_idle",world_seen.size()==4 and locked and trial.current_action=="idle" and trial.farming_clip.is_empty())
  check(id+"_ends_same_recipe_idle",trial.pose.texture==sample.idle_texture)
 for item in world_pending:item.image.save_png(evidence.path_join(item.file));captures.append(item.file)
 check(id+"_four_world_pose_captures",world_pending.size()==4)
 var end_picture:Image=await snapshot(id+"-world-end")
 var world_board:=Image.create(1300,300,false,Image.FORMAT_RGBA8)
 for item in world_pending:world_board.blit_rect(item.image,item.rect,Vector2i(item.pose*260,0))
 var origin:Vector2=trial.actor.get_global_transform_with_canvas()*Vector2.ZERO
 world_board.blit_rect(end_picture,Rect2i(Vector2i(origin)-Vector2i(130,260),Vector2i(260,300)),Vector2i(1040,0))
 world_board.save_png(evidence.path_join("boards/"+id+"-world-1x.png"))
func record_world_pose(id:String,index:int,pending:Array) -> void:
 RenderingServer.force_draw()
 var picture:=root.get_texture().get_image()
 var origin:Vector2=trial.actor.get_global_transform_with_canvas()*Vector2.ZERO
 pending.append({"file":"sequence/"+id+"-world-pose-"+str(index)+".png","image":picture,"pose":index,"rect":Rect2i(Vector2i(origin)-Vector2i(130,260),Vector2i(260,300))})
func finish() -> void:
 var clips:Dictionary={}
 if is_instance_valid(trial):
  for sample in trial.sample_library.samples:clips[sample.id]={"sample_sha256":sample.sample_sha256,"recipe":sample.data.recipe,"pose_ids":sample.pose_ids,"durations_ms":sample.durations_ms}
 var report:Dictionary={"scope":"Five explicitly sampled recipes/action-direction pairs only. Real native GPU renders; actual control signals/handlers and logical Input actions, NOT OS keyboard/mouse/focus validation. 20poses on dark/light native backgrounds, matching idle,10panelcycles each,walk/run physics and three tool one-shots with all20 world pose captures. Does not establish all wardrobe combinations or directions.","input_contract_sha256":input_contract_sha256,"started_utc":started_utc,"finished_utc":Time.get_datetime_string_from_system(true),"clips":clips,"checks":s.checks,"samples":samples,"captures":captures}
 save_json(evidence.path_join("report.json"),report);save_json(evidence.path_join("checks.json"),s.checks)
 print("WARDROBE_NATIVE checks=",s.checks.size()," passed=",s.passed()," samples=",samples.size()," captures=",captures.size());quit(0 if s.passed() else 1)
