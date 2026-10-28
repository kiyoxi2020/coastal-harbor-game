extends "res://dev/character_wardrobe_trial.gd"
const HeadLibrary=preload("res://dev/character_headwear_samples.gd")
const HEAD_LABELS={"bare":"裸头","hair":"栗色短发","hat":"草帽","hair_hat":"短发＋草帽"}
var head_library=HeadLibrary.new()
var head_error:=""
var head_ready:=false
var head_state:="bare"
var head_catalog_override:=""
@onready var head_label:Label=$TrialUI/Headwear/Margin/Rows/Selection
func _ready() -> void:
 super._ready()
 get_window().title="潮港旧屋 · 动态发帽抽样"
 $TrialUI/Panel/Margin/Rows/Instructions.text="动态发帽体验 · 右上选动作、右下选发帽 · R回起点 · 左侧暂停/逐帧"
 $TrialUI/Samples/Margin/Rows/Title.text="动态发帽 · 四组动作抽样"
 $TrialUI/Samples/Margin/Rows/Buttons.get_node("walk-west").hide()
 $TrialUI/Panel/Margin/Rows/Scope.text="右上选动作、右下选发帽；左侧暂停/逐帧。方向键跑步，F浇水 / G锄地 / H收获。仅所选方向，无存档。"
 var project:=ProjectSettings.globalize_path("res://..")
 var catalog:=head_catalog_override if head_catalog_override!="" else project.path_join("art/design/character-motion/adult-standard-v1/headwear-sampling-v1/catalog.json")
 if sample_error!="" or load_error!="":head_error=sample_error if sample_error!="" else load_error
 elif not head_library.load_samples(project,catalog):head_error=head_library.error
 if head_error!="":
  load_error=head_error;head_label.text="发帽加载失败："+head_error
  for button in $TrialUI/Samples/Margin/Rows/Buttons.get_children():button.disabled=true
  for button in $TrialUI/Headwear/Margin/Rows/Buttons.get_children():button.disabled=true
  return
 for state in HeadLibrary.STATES:
  $TrialUI/Headwear/Margin/Rows/Buttons.get_node(state).pressed.connect(select_head_state.bind(state))
 head_ready=true
 select_sample("run-east")
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
 if not head_ready or state not in HeadLibrary.STATES:return false
 head_state=state
 apply_head_state(state)
 refresh_pose();review_panel.refresh_preview();refresh_head_label()
 return true
func refresh_head_label() -> void:
 if not is_instance_valid(head_label):return
 head_label.text="当前："+str(HEAD_LABELS[head_state])+" · 切换保持当前动作进度\n仅本次四组抽样，外观待你验收。"
 for state in HeadLibrary.STATES:
  $TrialUI/Headwear/Margin/Rows/Buttons.get_node(state).set_pressed_no_signal(state==head_state)
func movement_input() -> Vector2:
 if not head_ready:return Vector2.ZERO
 return super.movement_input()
func start_farming_sample(action:String) -> bool:
 if not head_ready or active_sample.is_empty() or action!=active_sample.data.action_id:return false
 return super.start_farming_sample(action)
func diagnostic_note(action:String,direction:String,recipe:String) -> String:
 if head_ready:return "动态发帽抽样："+str(HEAD_LABELS[head_state])+"；检查发际、帽檐与动作遮挡。"
 return super.diagnostic_note(action,direction,recipe)
