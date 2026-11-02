extends "res://dev/characters/character_wardrobe_trial.gd"
const HeadLibrary=preload("res://dev/characters/character_headwear_samples.gd")
const HEAD_LABELS={"bare":"裸头","hair":"栗色短发","hat":"草帽","hair_hat":"短发＋草帽"}
var head_library=HeadLibrary.new()
var head_error:=""
var head_ready:=false
var head_state:="bare"
var head_catalog_override:=""
var full_density:=Vector2.ONE
var registered_density_bound:=false
var action_instance_id:=0
var action_instance_key:=""
var action_event_log:Array=[]
var action_event_seen:Dictionary={}
var pending_locomotion_action:=""
var stable_remaining_ms:=0.0
@onready var head_label:Label=$TrialUI/Headwear/Margin/Rows/Selection
func _ready() -> void:
 var construction_requested:=false
 for argument in OS.get_cmdline_user_args():
  if argument.begins_with("--construction-suite="):
   head_catalog_override=argument.trim_prefix("--construction-suite=");construction_requested=true
  if argument.begins_with("--head-catalog="):head_catalog_override=argument.trim_prefix("--head-catalog=")
 var project:=ProjectSettings.globalize_path("res://..").simplify_path()
 var catalog:=head_catalog_override if head_catalog_override!="" else project.path_join("art/characters/reviews/headwear/catalog.json")
 var header:Variant=JSON.parse_string(FileAccess.get_file_as_string(catalog)) if FileAccess.file_exists(catalog) else null
 var construction_header:bool=header is Dictionary and header.get("kind")=="coastal-character-construction-review-v1"
 var legacy_construction:bool=construction_header and (header.get("schema_version") is int or header.get("schema_version") is float) and header.get("schema_version")==1
 var candidate_header:bool=header is Dictionary and header.get("kind")=="coastal-character-construction-candidate-v1"
 var body_header:bool=header is Dictionary and header.get("kind")=="coastal-body-character-review-v1"
 var full_requested:bool=body_header or candidate_header or (construction_header and header.get("schema_version")==2) or (construction_requested and not legacy_construction)
 if full_requested:
  # A complete package is validated before setting up the shared scene. Never
  # bootstrap its action state from legacy locomotion/farming/wardrobe data.
  var loaded:=head_library.load_samples(project,catalog)
  initialize_trial_shell()
  if loaded and uses_registered_package() and install_registered_package():return
  head_error=head_library.error if not loaded else "全动作包安装失败。"
  load_error=head_error;head_label.text="发帽加载失败："+head_error;pose.visible=false
  for button in $TrialUI/Samples/Margin/Rows/Buttons.get_children():button.disabled=true
  for button in $TrialUI/Headwear/Margin/Rows/Buttons.get_children():button.disabled=true
  return
 super._ready()
 get_window().title="潮港旧屋 · 动态发帽抽样"
 $TrialUI/Panel/Margin/Rows/Instructions.text="动态发帽体验 · 右上选动作、右下选发帽 · R回起点 · 左侧暂停/逐帧"
 $TrialUI/Samples/Margin/Rows/Title.text="动态发帽 · 四组动作抽样"
 $TrialUI/Samples/Margin/Rows/Buttons.get_node("walk-west").hide()
 $TrialUI/Panel/Margin/Rows/Scope.text="右上选动作、右下选发帽；左侧暂停/逐帧。方向键跑步，F浇水 / G锄地 / H收获。仅所选方向，无存档。"
 if sample_error!="" or load_error!="":head_error=sample_error if sample_error!="" else load_error
 elif not head_library.load_samples(project,catalog):head_error=head_library.error
 if head_error=="" and uses_registered_package():
  if not install_full_package():head_error="全动作包安装失败。"
  else:return
 if head_error=="" and head_library.suite_kind=="coastal-character-construction-review-v1":
  # Replace inherited wardrobe sample entries before exposing any construction
  # selection. The actual motion library still supplies the frozen clock/pose map.
  sample_library.samples=[]
  for head in head_library.samples:
   var sample:Dictionary=head.duplicate(false)
   sample.textures=head.textures_by_state.bare;sample.idle_texture=head.idle_by_state.bare
   sample_library.samples.append(sample)
  if not apply_samples():head_error=sample_error
 if head_error!="":
  load_error=head_error;head_label.text="发帽加载失败："+head_error
  for button in $TrialUI/Samples/Margin/Rows/Buttons.get_children():button.disabled=true
  for button in $TrialUI/Headwear/Margin/Rows/Buttons.get_children():button.disabled=true
  return
 var available:Array=[]
 for sample in head_library.samples:available.append(sample.id)
 for button in $TrialUI/Samples/Margin/Rows/Buttons.get_children():
  button.visible=button.name in available;button.disabled=not button.name in available
 $TrialUI/Samples/Margin/Rows/Title.text="西向锄地 · 四种发帽" if head_library.suite_kind!="" else "动态发帽 · 四组动作抽样"
 if head_library.suite_kind!="":$TrialUI/Panel/Margin/Rows/Scope.text="西向锄地四姿态与匹配站姿；右下选择发帽，左侧暂停/逐帧。G锄地，R回起点。无存档。"
 for state in HeadLibrary.STATES:
  $TrialUI/Headwear/Margin/Rows/Buttons.get_node(state).pressed.connect(select_head_state.bind(state))
 head_ready=true
 select_sample("hoe-west" if head_library.suite_kind!="" else "run-east")
 select_head_state("hair_hat")
func select_sample(id:String) -> void:
 # During parent setup head resources have not loaded; do not expose that selection.
 if not head_ready:
  if head_error=="":super.select_sample(id)
  return
 if id not in HeadLibrary.IDS:return
 var found:=false
 for sample in head_library.samples:
  if sample.id==id:found=true
 if not found:return
 apply_head_state(head_state)
 super.select_sample(id)
 if head_library.suite_kind!="":sample_label.text="当前：西向锄地 · 海军条纹衫\n原款长裤与棕鞋 · 四种发帽\n世界：G锄地；R回起点。"
 refresh_head_label()
func apply_head_state(state:String) -> void:
 for head in head_library.samples:
  for sample in sample_library.samples:
   if sample.id!=head.id:continue
   sample.textures=head.textures_by_state[state]
   sample.idle_texture=head.idle_by_state[state]
   var action:String=sample.data.action_id;var direction:String=sample.data.direction
   if action in ["walk","run"]:
    for i in range(4):frames.B[clips[action][direction][i]]=sample.textures[i]
   else:
    var original:Dictionary=review_panel.farming_library.get_clip(action,direction,"B")
    original.textures=sample.textures
    original.note="动态发帽抽样：检查发际、帽檐与手/工具遮挡，四状态可切换；待你验收。"
    if not farming_clip.is_empty() and selected_sample==sample.id:farming_clip.textures=sample.textures
   if selected_sample==sample.id:frames.B[clips.idle[direction][0]]=sample.idle_texture
func select_head_state(state:String) -> bool:
 if uses_registered_package():return head_ready and state==("body" if body_review_mode() else "hair_hat")
 if not head_ready or state not in HeadLibrary.STATES:return false
 head_state=state
 apply_head_state(state)
 refresh_pose();review_panel.refresh_preview();refresh_head_label()
 return true
func refresh_head_label() -> void:
 if not is_instance_valid(head_label):return
 if body_review_mode():
  head_label.text="完整身体 · 四向全动作，待视觉验收。"
  return
 head_label.text="当前："+str(HEAD_LABELS[head_state])+" · 切换保持当前动作进度\n"+("仅西锄四姿态＋站姿小样，外观待你验收。" if head_library.suite_kind!="" else "仅本次四组抽样，外观待你验收。")
 for state in HeadLibrary.STATES:
  $TrialUI/Headwear/Margin/Rows/Buttons.get_node(state).set_pressed_no_signal(state==head_state)
func movement_input() -> Vector2:
 if not head_ready:return Vector2.ZERO
 if uses_registered_package():
  return Input.get_vector("trial_walk_west","trial_walk_east","trial_walk_north","trial_walk_south") if focused else Vector2.ZERO
 return super.movement_input()
func start_farming_sample(action:String) -> bool:
 if head_ready and uses_registered_package():
  if not super.start_farming_sample(action):return false
  pending_locomotion_action="";stable_remaining_ms=0
  record_action_events(-1.0,0.0,full_clip_geometry(action,facing),false)
  return true
 if not head_ready or active_sample.is_empty() or action!=active_sample.data.action_id:return false
 return super.start_farming_sample(action)
func diagnostic_note(action:String,direction:String,recipe:String) -> String:
 if uses_registered_package():return ""
 if head_ready:return "动态发帽抽样："+str(HEAD_LABELS[head_state])+"；检查发际、帽檐与动作遮挡。"
 return super.diagnostic_note(action,direction,recipe)

func refresh_status() -> void:
 if not uses_registered_package():
  super.refresh_status();return
 if not is_instance_valid(status):return
 if load_error!="":status.text=load_error;return
 if motion_error!="":status.text=motion_error;return
 if body_review_mode():
  $TrialUI/Panel/Margin/Rows/Controls/SpeedLabel.text="速度（50%–100%）"
  $TrialUI/Panel/Margin/Rows/Controls/MaxSpeed.text="当前%d%%　− / + 调节"%roundi(speed_factor*100)
 status.text=("身体评审" if body_review_mode() else "海军条纹衫")+" · %s / %s · 速度%d%%"%[current_action,facing,roundi(speed_factor*100)]
 if not farming_clip.is_empty():status.text+=" · 姿态%d/%d"%[farming_pose_index()+1,farming_clip.textures.size()]

# Installs only a validated construction library, keeping the existing world
# movement and one action clock. Inspector scale determines display density.
func uses_registered_package() -> bool:
 return head_library.full_package or head_library.candidate_package
func body_review_mode() -> bool:
 return head_library.suite_kind=="coastal-body-character-review-v1"
func install_full_package() -> bool:
 if not head_library.full_package or head_library.full_clips.size()!=24:return false
 return install_registered_package()
func install_registered_package() -> bool:
 if not uses_registered_package() or head_library.full_clips.is_empty() or head_library.canonical_idle.is_empty():return false
 initialize_trial_shell()
 cancel_farming_sample()
 if not registered_density_bound:
  full_density=pose.scale/(138.0/582.0);registered_density_bound=true
 frames={"B":[]};clips={};frame_metadata=[]
 sample_library.samples=[];active_sample={};selected_sample=""
 if review_panel.farming_library==null:
  review_panel.farming_library=load("res://dev/characters/character_farming_review.gd").new()
 review_panel.farming_library.clips.clear()
 review_panel.farming_error=""
 for id in head_library.full_clips:
  var clip:Dictionary=head_library.full_clips[id]
  var action:String=clip.action_id;var direction:String=clip.direction
  if action in ["idle","walk","run"]:
   if not clips.has(action):clips[action]={}
   var indices:Array=[]
   for i in range(clip.textures.size()):
    indices.append(frame_metadata.size())
    frames.B.append(clip.textures[i])
    frame_metadata.append({"pose_id":clip.pose_ids[i],"duration_ms":clip.durations_ms[i]})
   clips[action][direction]=indices
  else:
   var farm:Dictionary=clip.duplicate(false)
   farm.garment="B";farm.note="完整身体 · 全动作评审，待视觉验收。" if body_review_mode() else "固定短发草帽配方 · 全动作评审，待视觉验收。"
   review_panel.farming_library.clips[action+"/"+direction+"/B"]=farm
 review_panel.farming_library.catalog_version=2
 move_policy={"idle":{"base_world_speed":0,"playback_rate":1.0}}
 for action in ["walk","run"]:move_policy[action]={"base_world_speed":head_library.runtime.movement[action].base_world_speed}
 speed_factor=float(head_library.runtime.default_speed_factor)
 speed_slider.set_value_no_signal(speed_factor)
 garment="B";head_state="body" if body_review_mode() else "hair_hat";head_ready=true;head_error="";load_error="";sample_error="";motion_error=""
 schema_version=2;farming_transitions_enabled=true;facing=("south" if head_library.canonical_idle.has("south") else str(head_library.canonical_idle.keys()[0]));current_action="idle";phase_ms=0;idle_phase_ms=0
 pending_locomotion_action="";stable_remaining_ms=0;run_requested=false;action_instance_key=""
 pose.visible=true
 review_enabled=true;farming_review_enabled=true
 review_panel.bind_trial(self);review_panel.visible=true
 $TrialUI/Panel/Margin/Rows/Controls/Short.hide();$TrialUI/Panel/Margin/Rows/Controls/Long.hide()
 for button in $TrialUI/Samples/Margin/Rows/Buttons.get_children():button.hide()
 for button in $TrialUI/Headwear/Margin/Rows/Buttons.get_children():button.visible=button.name=="hair_hat";button.disabled=true
 for button in review_panel.direction_buttons+review_panel.action_buttons:button.disabled=false
 review_panel.get_node("Margin/Rows/Directions").show();review_panel.get_node("Margin/Rows/Actions").show()
 review_panel.get_node("Margin/Rows/Actions/FarmActions").show()
 get_window().title="潮港旧屋 · 固定发帽全动作评审"
 $TrialUI/Samples/Margin/Rows/Title.text="固定配方 · 四向全动作"
 sample_label.text="海军条纹衫 · 原款长裤与棕鞋\n栗色短发＋草帽 · 24动作方向"
 head_label.text="固定：栗色短发＋草帽"
 review_panel.get_node("Margin/Rows/Views/Reference/Label").text="配方站姿"
 review_panel.get_node("Margin/Rows/Help").text="左侧选择动作、暂停或逐帧；方向键控制世界角色。C显示或收起对照。"
 $TrialUI/Panel/Margin/Rows/Instructions.text="方向键移动 · Shift跑步 · F浇水 / G锄地 / H收获 · R回起点"
 $TrialUI/Panel/Margin/Rows/Scope.text="左侧四向六动作对照、暂停/逐帧；世界动作单独控制。评审版本，无存档。"
 $TrialUI/Headwear.visible=not body_review_mode()
 if body_review_mode():
  get_window().title="潮港旧屋 · 身体全动作评审"
  $TrialUI/Samples/Margin/Rows/Title.text="完整身体 · 四向全动作"
  sample_label.text="身体源图 · 四向六动作\n完整身体与工具表现，待视觉验收"
  head_label.text="完整身体"
  review_panel.get_node("Margin/Rows/Views/Reference/Label").text="身体站姿"
 if head_library.candidate_package:
  get_window().title="潮港旧屋 · 内部动作验收"
  $TrialUI/Samples/Margin/Rows/Title.text="内部动作验收 · %d/24"%head_library.full_clips.size()
  sample_label.text="海军条纹衫 · 原款长裤与棕鞋\n栗色短发＋草帽 · 本次已登记%d/24"%head_library.full_clips.size()
  $TrialUI/Panel/Margin/Rows/Scope.text="内部批次：仅启用已登记动作/方向。左侧暂停/逐帧；世界角色单独控制。无存档。"
  $TrialUI/Panel/Margin/Rows/Instructions.text="方向键控制已登记移动 · R回起点 · 左侧选择已登记动作"
 review_panel.select_clip(facing,"idle")
 update_registered_controls()
 refresh_pose()
 return true
func full_clip_geometry(action:String,direction:String) -> Dictionary:
 return head_library.full_clips.get(action+"-"+direction,{}) if uses_registered_package() else {}
func _physics_process(delta:float) -> void:
 if uses_registered_package():
  if not focused:
   actor.velocity=Vector2.ZERO
   return
  if farming_clip.is_empty():
   move_policy.idle.playback_rate=float(head_library.runtime.clips["idle-"+facing].playback_rate)
   var requested:=movement_input()
   if run_requested and not requested.is_zero_approx() and not has_motion_garment("run",direction_from_vector(requested),garment):
    actor.velocity=Vector2.ZERO;current_action="idle";motion_error="此方向跑步尚未登记。";refresh_pose();return
   var wanted:="run" if run_requested else "walk"
   if requested.is_zero_approx():pending_locomotion_action="";stable_remaining_ms=0
   elif pending_locomotion_action!="":
    stable_remaining_ms-=maxf(delta,0.0)*1000.0
    actor.velocity=Vector2.ZERO
    if stable_remaining_ms>0:refresh_pose();return
    delta=maxf(0.0,-stable_remaining_ms/1000.0)
    pending_locomotion_action="";phase_ms=0
   elif current_action in ["walk","run"] and wanted!=current_action:
    pending_locomotion_action=wanted
    stable_remaining_ms=float(head_library.runtime.locomotion_transition.duration_ms)
    current_action="idle";idle_phase_ms=0;phase_ms=0;actor.velocity=Vector2.ZERO
    refresh_pose();return
 super._physics_process(delta)
func advance_farming_sample(delta:float) -> void:
 if not uses_registered_package():super.advance_farming_sample(delta);return
 if farming_clip.is_empty() or not focused:return
 var clip:=full_clip_geometry(current_action,facing)
 var before:=farming_elapsed_ms
 var rate:=float(head_library.runtime.clips[current_action+"-"+facing].playback_rate)
 var after:=before+maxf(delta,0.0)*1000.0*rate
 var duration:=0.0
 for value in clip.durations_ms:duration+=float(value)
 record_action_events(before,minf(after,duration),clip,after>=duration)
 super.advance_farming_sample(maxf(delta,0.0)*rate)
func record_action_events(before:float,after:float,clip:Dictionary,complete:bool) -> void:
 var config:Dictionary=head_library.runtime.clips[clip.action_id+"-"+clip.direction]
 for event in config.events:
  if float(event.at_ms)>before and float(event.at_ms)<=after and not action_event_seen.has(event.event_id):
   action_event_seen[event.event_id]=true
   action_event_log.append({"instance_id":action_instance_id,"event_id":event.event_id,"loop":0,"at_ms":event.at_ms,"action":clip.action_id,"direction":clip.direction,"pose_id":event.pose_id})
 if complete and not action_event_seen.has("complete"):
  action_event_seen.complete=true
  action_event_log.append({"instance_id":action_instance_id,"event_id":"complete","loop":0,"at_ms":after,"action":clip.action_id,"direction":clip.direction})
func refresh_pose() -> void:
 if uses_registered_package() and head_ready:
  var key:=current_action+"/"+facing
  if key!=action_instance_key:
   action_instance_key=key;action_instance_id+=1;action_event_seen.clear()
  var clip:=full_clip_geometry(current_action,facing)
  if not clip.is_empty():pose.scale=full_density*float(clip.display_scale);pose.offset=-clip.root_anchor_px
 super.refresh_pose()
func _unhandled_key_input(event:InputEvent) -> void:
 if not uses_registered_package():super._unhandled_key_input(event);return
 if event is InputEventKey and event.physical_keycode==KEY_SHIFT:run_requested=event.pressed;return
 if not event is InputEventKey or not event.pressed or event.echo:return
 match event.physical_keycode:
  KEY_F:start_farming_sample("water")
  KEY_G:start_farming_sample("hoe")
  KEY_H:start_farming_sample("harvest")
  KEY_R:reset_position()
  KEY_C:toggle_review()
  KEY_ESCAPE:get_tree().quit()

func active_action_state() -> Dictionary:
 var elapsed:=farming_elapsed_ms if not farming_clip.is_empty() else (phase_ms if current_action in ["walk","run"] else idle_phase_ms)
 var rate:=speed_factor if current_action in ["walk","run"] else 1.0
 if uses_registered_package() and current_action not in ["walk","run"]:rate=float(head_library.runtime.clips[current_action+"-"+facing].playback_rate)
 return {"action":current_action,"direction":facing,"elapsed_ms":elapsed,"playback_rate":rate,"instance_id":action_instance_id}

func update_registered_controls() -> void:
 if not uses_registered_package() or not head_ready:return
 for button in review_panel.direction_buttons:
  button.disabled=not head_library.canonical_idle.has(str(button.name).to_lower())
 for i in range(review_panel.action_buttons.size()):
  review_panel.action_buttons[i].disabled=not head_library.full_clips.has(review_panel.ACTIONS[i]+"-"+review_panel.review_direction)
