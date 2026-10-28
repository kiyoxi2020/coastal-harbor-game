extends "res://dev/character_walk_trial.gd"
const SAMPLE_LABELS={"walk-west":"西向走路 · 条纹衫与牛仔裤","run-east":"东向跑步 · 砖红毛衣与搭扣鞋","hoe-west":"西向锄地 · 海军条纹衫","water-south":"南向浇水 · 牛仔裤与搭扣鞋","harvest-north":"北向收获 · 蓝长袖与牛仔裤"}
const CLOTHES_LABELS={"top03":"海军条纹衫","top04":"砖红毛衣","pants02":"深蓝牛仔裤","shoes04":"棕色搭扣鞋"}
const SampleLibrary=preload("res://dev/character_wardrobe_samples.gd")
var sample_library=SampleLibrary.new()
var sample_error:=""
var selected_sample:=""
var active_sample:Dictionary={}
var sample_catalog_path:=""
@onready var sample_label:Label=$TrialUI/Samples/Margin/Rows/Selection
func _ready() -> void:
 var project:=ProjectSettings.globalize_path("res://..")
 var base:=project.path_join("art/design/character-motion/adult-standard-v1")
 art_root=base.path_join("locomotion-v1");run_candidate_root=base.path_join("run-four-directions-v1")
 run_diagnostics_enabled=true;review_enabled=true;farming_review_enabled=true;farming_transitions_enabled=true
 farming_catalog_path=base.path_join("farming-four-directions-v1/catalog-color-v2.json")
 sample_catalog_path=base.path_join("wardrobe-sampling-v1/catalog.json")
 super._ready()
 if not sample_library.load_samples(project,sample_catalog_path):
  sample_error=sample_library.error;sample_label.text="抽样加载失败："+sample_error;return
 if not apply_samples():sample_label.text="抽样加载失败："+sample_error;return
 for sample in sample_library.samples:
  var button:Button=$TrialUI/Samples/Margin/Rows/Buttons.get_node(str(sample.id))
  button.pressed.connect(select_sample.bind(str(sample.id)))
 get_window().title="潮港旧屋 · 衣物组合抽样试玩"
 $TrialUI/Panel/Margin/Rows/Scope.text="五组衣物组合抽样；右上选样例，左侧暂停/逐帧。仅启用所选样例动作与方向。无存档。"
 review_panel.get_node("Margin/Rows/Views/Reference/Label").text="同配方站姿"
 for button in review_panel.direction_buttons+review_panel.action_buttons:button.disabled=true
 $TrialUI/Panel/Margin/Rows/Controls/Short.hide();$TrialUI/Panel/Margin/Rows/Controls/Long.hide()
 select_sample("walk-west")
func apply_samples() -> bool:
 # Check every sample against the loaded, accepted motion before replacing anything.
 for sample in sample_library.samples:
  var data:Dictionary=sample.data
  var action:String=data.action_id;var direction:String=data.direction
  if data.idle.canvas_px!=[512.0,768.0] or data.idle.root_anchor_px!=[256.0,708.0] or not is_equal_approx(float(data.idle.display_scale),138.0/582.0):sample_error="站姿登记不符。";return false
  if action in ["walk","run"]:
   var indices:Array=clips.get(action,{}).get(direction,[])
   if indices.size()!=4:sample_error="原动作缺失。";return false
   for i in range(4):
    if frame_metadata[indices[i]].pose_id!=sample.pose_ids[i] or frame_metadata[indices[i]].duration_ms!=sample.durations_ms[i]:sample_error="样例姿态/时序与原动作不符。";return false
   if sample.canvas_px!=Vector2(512,768) or sample.root_anchor_px!=Vector2(256,708) or not is_equal_approx(sample.display_scale,138.0/582.0):sample_error="样例与原走跑登记不符。";return false
  else:
   var original:Dictionary=review_panel.farming_library.get_clip(action,direction,"B")
   if original.is_empty() or original.pose_ids!=sample.pose_ids or not same_durations(original.durations_ms,sample.durations_ms) or original.canvas_px!=sample.canvas_px or original.root_anchor_px!=sample.root_anchor_px or not is_equal_approx(original.display_scale,sample.display_scale):sample_error="农事样例与原动作登记不符。";return false
 for sample in sample_library.samples:
  var data:Dictionary=sample.data
  if data.action_id in ["walk","run"]:
   var indices:Array=clips[data.action_id][data.direction]
   for i in range(4):frames.B[indices[i]]=sample.textures[i]
  else:
   var original:Dictionary=review_panel.farming_library.get_clip(data.action_id,data.direction,"B")
   original.textures=sample.textures
   original.sample_sha256=sample.sample_sha256
   original.sample_recipe=data.recipe
   original.note="衣物组合抽样：观察袖腕、腰线、鞋口和遮挡；仅此配方与方向，待你验收。"
 return true
func select_sample(id:String) -> void:
 for sample in sample_library.samples:
  if sample.id!=id:continue
  reset_position();set_garment("B");facing=sample.data.direction;selected_sample=id;active_sample=sample
  frames.B[clips.idle[facing][0]]=sample.idle_texture
  review_panel.select_clip(facing,sample.data.action_id);review_panel.set_playing(true);refresh_pose()
  var slots:Dictionary=sample.data.recipe.slots
  sample_label.text="当前：%s\n上衣 %s · 裤子 %s · 鞋 %s\n世界：方向键走跑；F浇水 / G锄地 / H收获（仅当前样例）。"%[SAMPLE_LABELS[id],CLOTHES_LABELS.get(slots.top,"原款上衣"),CLOTHES_LABELS.get(slots.pants,"原款长裤"),CLOTHES_LABELS.get(slots.shoes,"原款棕鞋")]
  for other in sample_library.samples:
   var button:Button=$TrialUI/Samples/Margin/Rows/Buttons.get_node(str(other.id))
   button.set_pressed_no_signal(other.id==id)
  return

func movement_input() -> Vector2:
 if active_sample.is_empty():return Vector2.ZERO
 if active_sample.data.action_id not in ["walk","run"]:return Vector2.ZERO
 var requested:=super.movement_input()
 if requested.is_zero_approx() or direction_from_vector(requested)!=active_sample.data.direction:return Vector2.ZERO
 return {"west":Vector2.LEFT,"east":Vector2.RIGHT,"north":Vector2.UP,"south":Vector2.DOWN}[active_sample.data.direction]*requested.length()
func _physics_process(delta:float) -> void:
 if not active_sample.is_empty():run_requested=active_sample.data.action_id=="run"
 super._physics_process(delta)
func _unhandled_key_input(event:InputEvent) -> void:
 if not event is InputEventKey or active_sample.is_empty():return
 if event.physical_keycode in [KEY_1,KEY_2,KEY_SHIFT]:return
 var tools:Dictionary={KEY_F:"water",KEY_G:"hoe",KEY_H:"harvest"}
 if tools.has(event.physical_keycode) and tools[event.physical_keycode]!=active_sample.data.action_id:return
 super._unhandled_key_input(event)
func refresh_status() -> void:
 super.refresh_status()
 if not active_sample.is_empty() and load_error=="" and sample_error=="":
  status.text="%s · %s · 速度%d%%"%[SAMPLE_LABELS[selected_sample],"站立" if current_action=="idle" else "动作中",roundi(speed_factor*100)]

func diagnostic_note(action:String,direction:String,recipe:String) -> String:
 if not active_sample.is_empty() and action==active_sample.data.action_id and direction==active_sample.data.direction and recipe=="B":
  return "衣物组合抽样：观察袖腕、腰线、鞋口和连续动作；待你验收。"
 return super.diagnostic_note(action,direction,recipe)

func same_durations(left:Array,right:Array) -> bool:
 if left.size()!=right.size():return false
 for i in range(left.size()):
  if float(left[i])!=float(right[i]):return false
 return true
