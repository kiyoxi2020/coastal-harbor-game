extends SceneTree
## Observer only: drives existing input actions and samples the inherited trial clock.
var evidence := ""
var repo := ProjectSettings.globalize_path("res://..").simplify_path()
var trial
var contract: Dictionary
var report := {"kind":"coastal-registered-native-observation-v1","checks":{},"samples":[],"captures":[],"output_hashes":{}}
var failures := 0
func _initialize() -> void:
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--evidence="): evidence=arg.trim_prefix("--evidence=")
 call_deferred("run")
func check(name:String,value:bool) -> void:
 report.checks[name]=value
 if not value:failures+=1;printerr(name)
func capture(name:String) -> void:
 await process_frame
 await RenderingServer.frame_post_draw
 var full=root.get_texture().get_image()
 var anchor=trial.actor.get_global_transform_with_canvas()*Vector2.ZERO
 var region=Rect2i(Vector2i(anchor)-Vector2i(160,250),Vector2i(320,320))
 if not Rect2i(Vector2i.ZERO,full.get_size()).encloses(region):check("capture_bounds_"+name,false);return
 var file=name+".png"
 full.get_region(region).save_png(evidence.path_join(file))
 report.output_hashes[file]=FileAccess.get_sha256(evidence.path_join(file))
 report.captures.append({"file":file,"pose_id":trial.frame_metadata[trial.current_frame()].pose_id,"action":trial.current_action,"phase_ms":trial.phase_ms,"physics_frame":Engine.get_physics_frames(),"sprite_scale":[trial.pose.scale.x,trial.pose.scale.y],"sprite_offset":[trial.pose.offset.x,trial.pose.offset.y],"render_transform":[trial.pose.get_global_transform_with_canvas().x.x,trial.pose.get_global_transform_with_canvas().y.y]})
func inspect_panel() -> void:
 var panel=trial.review_panel
 trial.get_node("TrialUI").show()
 panel.show()
 panel.set_playing(false)
 await process_frame
 await RenderingServer.frame_post_draw
 var overview=root.get_texture().get_image()
 overview.save_png(evidence.path_join("overview.png"))
 report.output_hashes["overview.png"]=FileAccess.get_sha256(evidence.path_join("overview.png"))
 for background in ["light","dark"]:
  var style=StyleBoxFlat.new()
  style.bg_color=Color(0.88,0.88,0.88,1) if background=="light" else Color(0.10,0.13,0.18,1)
  panel.add_theme_stylebox_override("panel",style)
  for action in ["idle","walk"]:
   panel.select_clip("west",action)
   for i in range(panel.preview_durations().size()):
    await process_frame
    await RenderingServer.frame_post_draw
    var sprite=panel.motion_view
    var transform=sprite.get_global_transform_with_canvas()
    var top_left=transform*(sprite.offset)
    var bottom_right=transform*(sprite.offset+sprite.texture.get_size())
    var box=Rect2i(Vector2i(top_left.ceil()),Vector2i(bottom_right-top_left))
    var full=root.get_texture().get_image()
    check("panel_bounds_"+background+action+str(i),Rect2i(Vector2i.ZERO,full.get_size()).encloses(box))
    var name="panel-"+background+"-"+action+"-"+str(i)+".png"
    full.get_region(box).save_png(evidence.path_join(name))
    report.output_hashes[name]=FileAccess.get_sha256(evidence.path_join(name))
    report.captures.append({"file":name,"mode":"existing-motion-panel","action":action,"pose_index":panel.current_pose_index(),"background":background,"size_px":[box.size.x,box.size.y],"source_to_screen":[transform.x.x,transform.y.y],"source_origin_px":[top_left.x,top_left.y],"capture_origin_px":[box.position.x,box.position.y]})
    panel.step_frame()
 trial.get_node("TrialUI").hide()
func run() -> void:
 if not evidence.begins_with("/private/tmp/coastal-") or "\\" in evidence or ":" in evidence or DisplayServer.get_name()=="headless":printerr("fresh isolated directory and native GPU required");quit(2);return
 for part in evidence.split("/").slice(1):
  if part in ["",".",".."]:quit(2);return
 var guard=load("res://dev/characters/character_construction_samples.gd").new()
 if not guard.no_links(evidence) or not guard.no_links(evidence.path_join("input-contract.json")):quit(2);return
 var files=DirAccess.get_files_at(evidence)
 if files!=PackedStringArray(["input-contract.json"]) or not DirAccess.get_directories_at(evidence).is_empty():quit(2);return
 contract=JSON.parse_string(FileAccess.get_file_as_string(evidence.path_join("input-contract.json")))
 if contract.get("kind")!="coastal-registered-native-input-v1":quit(2);return
 for file in contract.files:
  if FileAccess.get_sha256(repo.path_join(file))!=contract.files[file]:printerr("input changed: "+file);quit(2);return
 trial=load("res://dev/characters/character_registered_trial.tscn").instantiate()
 root.add_child(trial)
 await process_frame
 check("loaded",trial.load_error=="" and trial.frames.has("B"))
 if failures>0:finish();return
 trial.get_node("TrialUI").hide()
 trial.focused=true
 trial.set_garment("B")
 await physics_frame
 await process_frame
 check("real_gpu",DisplayServer.get_name()!="headless")
 check("matching_idle",trial.current_action=="idle" and trial.frame_metadata[trial.current_frame()].pose_id=="idle_west_0")
 await inspect_panel()
 await capture("idle-before")
 var seen:Dictionary={};var cycles=0;var previous=0.0;var start=trial.actor.position;var elapsed=0.0
 Input.action_press("trial_walk_west")
 for i in range(1200):
  await physics_frame
  await process_frame
  trial.focused=true
  if trial.current_action!="walk":continue
  if trial.phase_ms+0.01<previous:cycles+=1
  previous=trial.phase_ms
  var index=trial.current_frame();var meta=trial.frame_metadata[index]
  report.samples.append({"physics_frame":Engine.get_physics_frames(),"pose_id":meta.pose_id,"duration_ms":meta.duration_ms,"phase_ms":trial.phase_ms,"position":[trial.actor.position.x,trial.actor.position.y],"texture_matches":trial.pose.texture==trial.frames.B[index]})
  if not seen.has(meta.pose_id):
   seen[meta.pose_id]=true
   await capture("walk-"+meta.pose_id)
  if cycles>=10:break
 Input.action_release("trial_walk_west")
 await physics_frame
 await process_frame
 var stop=trial.actor.position
 await capture("idle-after")
 check("ten_actual_world_cycles",cycles>=10)
 check("all_six_walk_poses",seen.size()==6)
 check("movement_distance",start.x-stop.x>220.0 and absf(start.y-stop.y)<0.1)
 check("stop_uses_matching_idle",trial.current_action=="idle" and trial.frame_metadata[trial.current_frame()].pose_id=="idle_west_0")
 var phase=trial.phase_ms
 for i in range(12):await physics_frame
 check("stopped_world_clock",is_equal_approx(phase,trial.phase_ms) and trial.actor.position.is_equal_approx(stop))
 var exact=true
 for row in report.samples:exact=exact and row.texture_matches
 check("actual_frame_texture_identity",exact)
 trial.set_garment("A");await capture("original-idle")
 trial.set_garment("B");await capture("sweater-idle")
 check("review_switch_preserves_position",trial.actor.position.is_equal_approx(stop))
 for file in contract.files:check("unchanged:"+file,FileAccess.get_sha256(repo.path_join(file))==contract.files[file])
 report.cycles=cycles;report.walk_pose_ids=seen.keys();report.world_distance=start.distance_to(stop)
 finish()
func finish() -> void:
 report.scope="Review-only west six walk poses plus matching idle, ten actual-distance-driven inherited world cycles and stopped clock. Logical Input actions; no OS keyboard, physical foot-contact, other directions/actions, dynamic mixed wardrobe, release or export claim."
 report.input_contract_sha256=FileAccess.get_sha256(evidence.path_join("input-contract.json"))
 report.viewport_px=[root.get_texture().get_width(),root.get_texture().get_height()]
 report.window_px=[DisplayServer.window_get_size().x,DisplayServer.window_get_size().y]
 report.renderer={"display_server":DisplayServer.get_name(),"method":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name()}
 var out=FileAccess.open(evidence.path_join("report.json"),FileAccess.WRITE);out.store_string(JSON.stringify(report,"  "));out.close()
 print("REGISTERED_NATIVE checks=",report.checks.size()," failures=",failures," samples=",report.samples.size())
 quit(0 if failures==0 else 1)
