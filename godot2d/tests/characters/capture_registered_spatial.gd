extends "res://tests/characters/capture_registered_actions_world.gd"
## Existing harbor, existing collisions and one shared character player.
## Scenario setup positions are explicit; movement uses actual input/physics.
var routes:Array=[]
var spatial_rows:Array=[]
var spatial_watch:=""
var spatial_capture_records:Array=[]
func spatial_capture(name:String,case_id:String) -> String:
 var row=observation(case_id,"harbor-spatial-capture")
 var anchor:Vector2=trial.actor.get_global_transform_with_canvas()*Vector2.ZERO
 var origin:Vector2i=Vector2i(anchor)-Vector2i(140,245)
 row.case=case_id;row.capture_origin_px=[origin.x,origin.y]
 row.capture=actor_capture(name);spatial_capture_records.append(row)
 return row.capture
func physics_sample(delta:float) -> void:
 if spatial_watch=="":return
 var colliders:Array=[]
 var normals:Array=[]
 for i in range(trial.actor.get_slide_collision_count()):
  var collision=trial.actor.get_slide_collision(i)
  var collider=collision.get_collider()
  var normal:Vector2=collision.get_normal();normals.append([exact(normal.x),exact(normal.y)])
  colliders.append(str(collider.get_path()) if collider is Node else str(collider))
 var requested:Vector2=trial.movement_input()
 var motion:Vector2=trial.actor.get_position_delta()
 spatial_rows.append({"case":spatial_watch,"physics_frame":Engine.get_physics_frames(),
  "ticks_usec":Time.get_ticks_usec(),
  "delta_f64":exact(delta),"position_f64":[exact(trial.actor.position.x),exact(trial.actor.position.y)],
  "state":trial.active_action_state(),"texture":texture_identity.get(trial.pose.texture.get_instance_id(),{}),
  "colliders":colliders,"collision_normals_f64":normals,"requested_f64":[exact(requested.x),exact(requested.y)],
  "phase_f64":exact(trial.phase_ms),"safe_margin_f64":exact(trial.actor.safe_margin),
  "motion_delta_f64":[exact(motion.x),exact(motion.y)]})
func release_movement() -> void:
 for direction in ["south","west","east","north"]:Input.action_release("trial_walk_"+direction)
func run() -> void:
 if not evidence.begins_with("/private/tmp/coastal-") or not FileAccess.file_exists(evidence.path_join("input-contract.json")):quit(2);return
 var contract=JSON.parse_string(FileAccess.get_file_as_string(evidence.path_join("input-contract.json")))
 if not contract is Dictionary or contract.get("capture_scene")!="res://dev/characters/character_headwear_trial.tscn" or contract.get("observer")!="spatial":quit(2);return
 contract_sha=FileAccess.get_sha256(evidence.path_join("input-contract.json"));started=Time.get_datetime_string_from_system(true)
 trial=load("res://dev/characters/character_headwear_trial.tscn").instantiate();root.add_child(trial)
 await draw_frame();review=trial.review_panel
 s.check("native_gpu",DisplayServer.get_name()!="headless")
 s.check("same_full_player_ready",trial.head_ready and trial.head_error=="" and trial.head_library.full_package)
 s.check("actual_harbor_depth_sort",trial.actor.get_parent().y_sort_enabled)
 if not s.passed():finish();return
 if not bind_loaded_input(contract):finish();return
 review.set_playing(false)
 trial.get_node("TrialUI").hide() # World-only evidence; UI must not cover canopy/hat.
 for id in trial.head_library.full_clips:
  var clip:Dictionary=trial.head_library.full_clips[id]
  for i in range(clip.textures.size()):texture_identity[clip.textures[i].get_instance_id()]={"clip":id,"pose_id":clip.pose_ids[i],"rgba_sha256":rgba_hash(clip.textures[i])}
 observed_gpu_texture_ids=texture_identity
 ledger=PhysicsLedger.new();ledger.callback=physics_sample;ledger.process_physics_priority=10000;root.add_child(ledger)
 await inspect_route("tree-around",[Vector2(286,130),Vector2(330,130),Vector2(330,90),Vector2(286,90),Vector2(286,130)])
 await inspect_route("counter-around",[Vector2(362,252),Vector2(548,252),Vector2(548,184),Vector2(362,184),Vector2(362,252)])
 var door=trial.get_node("HarborExterior/DepthSortedObjects/ExteriorDoor")
 for pose in range(3):
  door.set_pose(pose);await physics_frame;await draw_frame()
  await inspect_door(pose)
 door.set_pose(0)
 for setting in [{"id":"tree-tools","position":Vector2(330,130),"facing":"west"},{"id":"counter-tools","position":Vector2(510,250),"facing":"north"},{"id":"door-tools","position":Vector2(235,190),"facing":"west"}]:
  await inspect_tools(setting)
 release_movement();spatial_watch=""
 await inspect_ground_targets()
 finish()
func setup_actor(point:Vector2) -> void:
 release_movement();trial.cancel_farming_sample();trial.reset_position();trial.actor.position=point;trial.run_requested=false;trial.focused=true
 await physics_frame;await draw_frame()
func walk_to_waypoint(point:Vector2,deadline_ms:int) -> bool:
 while trial.actor.position.distance_to(point)>1.2 and Time.get_ticks_msec()<deadline_ms:
  release_movement()
  var delta:Vector2=point-trial.actor.position
  var direction:String="east" if delta.x>0 else "west"
  if absf(delta.y)>absf(delta.x):direction="south" if delta.y>0 else "north"
  Input.action_press("trial_walk_"+direction)
  await physics_frame;await draw_frame()
 release_movement();await physics_frame;await draw_frame()
 return trial.actor.position.distance_to(point)<=1.2
func inspect_route(id:String,points:Array) -> void:
 await setup_actor(points[0]);var begin=spatial_rows.size();spatial_watch=id
 var captures:Array=[spatial_capture(id+"-start",id)]
 for i in range(1,points.size()):
  trial.run_requested=i%2==0
  s.check(id+"_waypoint_"+str(i),await walk_to_waypoint(points[i],Time.get_ticks_msec()+10000))
  captures.append(spatial_capture(id+"-waypoint-"+str(i),id))
 spatial_watch="";trial.run_requested=false
 var declared:Array=[]
 for point in points:declared.append([point.x,point.y])
 routes.append({"id":id,"setup_position":[points[0].x,points[0].y],"waypoints":declared,"physics_samples":spatial_rows.slice(begin),"captures":captures})
func inspect_door(pose:int) -> void:
 var id="door-pose-"+str(pose);await setup_actor(Vector2(209,190));var begin=spatial_rows.size();spatial_watch=id
 var captures:Array=[spatial_capture(id+"-start",id)]
 Input.action_press("trial_walk_north")
 for tick in range(65):
  await physics_frame;await draw_frame()
  if tick in [15,30,45]:captures.append(spatial_capture(id+"-tick-"+str(tick),id))
 release_movement();await physics_frame;await draw_frame();spatial_watch=""
 captures.append(spatial_capture(id+"-end",id))
 s.check(id+"_collision_or_passage",trial.actor.position.y<155 if pose==2 else trial.actor.position.y>160)
 routes.append({"id":id,"door_pose":pose,"setup_position":[209,190],"physics_samples":spatial_rows.slice(begin),"captures":captures,"final_position":[trial.actor.position.x,trial.actor.position.y]})
func inspect_tools(setting:Dictionary) -> void:
 await setup_actor(setting.position);trial.facing=setting.facing;trial.refresh_pose()
 for action in ["hoe","water","harvest"]:
  var id:String=setting.id+"-"+action;var begin=spatial_rows.size();spatial_watch=id;var seen:Dictionary={};var captures:Array=[]
  var config:Dictionary=trial.head_library.runtime.clips[action+"-"+setting.facing]
  var original_rate:float=config.playback_rate
  config.playback_rate=0.25 # Spatial pose visibility only; normal-speed timing is tested separately.
  s.check(id+"_starts",trial.start_farming_sample(action));var deadline=Time.get_ticks_msec()+10000
  while not trial.farming_clip.is_empty() and Time.get_ticks_msec()<deadline:
   await draw_frame()
   if trial.farming_clip.is_empty():break
   var index:int=trial.farming_pose_index()
   if not seen.has(index):seen[index]=true;captures.append(spatial_capture(id+"-pose-"+str(index),id))
  spatial_watch=""
  config.playback_rate=original_rate
  s.check(id+"_all_poses",seen.size()==trial.head_library.full_clips[action+"-"+setting.facing].pose_ids.size())
  s.check(id+"_stationary",trial.actor.position==setting.position)
  routes.append({"id":id,"spatial_observation_playback_rate":0.25,"setup_position":[setting.position.x,setting.position.y],"physics_samples":spatial_rows.slice(begin),"captures":captures})
func engine_clock_observation() -> Dictionary:
 return {"physics_ticks_per_second":Engine.physics_ticks_per_second,"physics_jitter_fix_f64":exact(Engine.physics_jitter_fix),"time_scale_f64":exact(Engine.time_scale),"max_physics_steps_per_frame":Engine.max_physics_steps_per_frame}
func inspect_ground_targets() -> void:
 # Predeclared setup only. No actor/part adjustment during an action.
 var candidate_path="res://tests/characters/all_actions_ground_target_candidates.json"
 var candidates:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(candidate_path))
 var output=evidence+"-ground"
 DirAccess.make_dir_recursive_absolute(output)
 DirAccess.copy_absolute(evidence.path_join("input-contract.json"),output.path_join("input-contract.json"))
 var plot=trial.get_node("HarborExterior/DepthSortedObjects/GardenA")
 var cases:Array=[];var ground_hashes:Dictionary={};var checks:Array=[]
 for candidate in candidates.cases:
  var id:String=candidate.id;var direction:String=id.get_slice("-",1)
  var action:String=id.get_slice("-",0);var center:Vector2=plot.cell_center(candidate.cell_id)
  var offset=Vector2(candidate.standing_offset[0],candidate.standing_offset[1])
  await setup_actor(center-offset);trial.facing=direction;trial.refresh_pose()
  plot.refresh({candidate.cell_id:{"tilled":action=="water","watered":false,"crop_id":"","growth":0}})
  await physics_frame;await draw_frame()
  var begin=spatial_rows.size();spatial_watch="ground-"+id
  var start:Vector2=trial.actor.global_position
  var ray=PhysicsRayQueryParameters2D.create(start,center,1,[trial.actor.get_rid()])
  var ray_hit:bool=not trial.get_world_2d().direct_space_state.intersect_ray(ray).is_empty()
  var forward:Vector2={"north":Vector2.UP,"south":Vector2.DOWN,"east":Vector2.RIGHT,"west":Vector2.LEFT}[direction]
  var forward_cell:String=plot.cell_at(start+forward*12)
  var started_action:bool=trial.start_farming_sample(action)
  var captured:Dictionary={};var deadline=Time.get_ticks_msec()+10000
  while not trial.farming_clip.is_empty() and Time.get_ticks_msec()<deadline:
   await draw_frame()
   var identity:Dictionary=actual_gpu_identity(trial.pose.texture)
   if identity.get("pose_id")==candidate.pose_id and captured.is_empty():
    var row=observation(id,"native-ground-target-alignment")
    row.capture_origin_px=row.actor_capture_origin_px
    row.capture=actor_capture("ground-"+id)
    var transform:Transform2D=trial.pose.global_transform
    var point=Vector2(candidate.source_point_px[0]+0.5,candidate.source_point_px[1]+0.5)+trial.pose.offset
    var world:Vector2=transform*point
    var m:Array=row.render_source_to_screen
    var screen=Transform2D(Vector2(m[0],m[1]),Vector2(m[2],m[3]),Vector2(m[4],m[5]))*point
    captured={"capture_record":row,"source_to_world_f64":[exact(transform.x.x),exact(transform.x.y),exact(transform.y.x),exact(transform.y.y),exact(transform.origin.x),exact(transform.origin.y)],"point_world_f64":[exact(world.x),exact(world.y)],"point_screen_f64":[exact(screen.x),exact(screen.y)],"point_cell_id":plot.cell_at(world)}
  spatial_watch=""
  checks.append({"name":id+"_started","passed":started_action})
  checks.append({"name":id+"_legal_target","passed":not ray_hit and start.distance_to(center)<=24 and forward_cell==candidate.cell_id})
  checks.append({"name":id+"_actual_pose_and_target","passed":not captured.is_empty() and captured.get("point_cell_id")==candidate.cell_id})
  checks.append({"name":id+"_stationary","passed":trial.actor.global_position==start})
  if not captured.is_empty():
   var png:String=captured.capture_record.capture
   var saved:bool=pending_images[png].save_png(output.path_join(png))==OK
   pending_images.erase(png);checks.append({"name":id+"_png_saved","passed":saved})
   ground_hashes[png]=FileAccess.get_sha256(output.path_join(png))
  captured.merge({"candidate_id":id,"actor_start_f64":[exact(start.x),exact(start.y)],"target_selection_mode":"keyboard-forward-12","forward_probe_cell_id":forward_cell,"target":{"cell_id":candidate.cell_id,"node_path":str(plot.get_path()),"center_f64":[exact(center.x),exact(center.y)],"cell_bounds_world":[center.x-8,center.y-8,16,16]},"distance_f64":exact(start.distance_to(center)),"ray_hit":ray_hit,"physics_samples":spatial_rows.slice(begin),"source_ground_contact_proven":false})
  cases.append(captured)
 var report={"kind":"coastal-native-ground-target-alignment-observation-v1","scope":"Actual visible tool/splash point projected inside a reachable existing plot cell from predeclared stationary setup. No soil-plane, physical impact, hidden contact, gameplay transaction or user approval claim.","engine_clock":engine_clock_observation(),"input_contract_sha256":contract_sha,"loaded_input_binding":loaded_input_binding,"renderer":DisplayServer.get_name(),"candidate_file":candidate_path,"candidate_sha256":FileAccess.get_sha256(candidate_path),"checks":checks,"cases":cases,"output_hashes":ground_hashes}
 var file=FileAccess.open(output.path_join("report.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
 for check in checks:s.check("ground_"+check.name,check.passed)
func finish() -> void:
 release_movement()
 for path in pending_images:
  s.check(path+"_saved",pending_images[path].save_png(evidence.path_join(path))==OK);hashes[path]=FileAccess.get_sha256(evidence.path_join(path))
 pending_images.clear()
 save_json("report.json",{"kind":"coastal-registered-harbor-spatial-observation-v1","scope":"Actual existing harbor and shared full player: physical paths around tree/counter, three door leaf poses and collisions, tools beside real obstacles. Explicit setup between scenarios, input/physics within routes. Raw GPU/positions retained for independent visual review. No gameplay target validity, room transition, OS input, user approval or production claim.","engine_clock":engine_clock_observation(),"loaded_input_binding":loaded_input_binding,"input_contract_sha256":contract_sha,"started_utc":started,"finished_utc":Time.get_datetime_string_from_system(true),"renderer":DisplayServer.get_name(),"checks":s.checks,"routes":routes,"capture_records":spatial_capture_records,"output_hashes":hashes})
 print("REGISTERED_HARBOR_SPATIAL checks=",s.checks.size()," passed=",s.passed());quit(0 if s.passed() else 1)
