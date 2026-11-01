extends SceneTree
## Real-library relocation smoke check. No save service or historical media.
const Support = preload("res://tests/life_test_support.gd")
var s = Support.new()
var trial
var review
var pose_count := 0
var screenshot := "/private/tmp/coastal-organized-character.png"
func _initialize() -> void:
 call_deferred("run")
func draw_frame() -> void:
 await process_frame
 trial.focused = true
 await RenderingServer.frame_post_draw
func run() -> void:
 s.check("native_renderer", DisplayServer.get_name() != "headless")
 if not s.passed(): quit(2); return
 var repo = ProjectSettings.globalize_path("res://..").simplify_path()
 trial = load("res://dev/characters/character_headwear_trial.tscn").instantiate()
 trial.head_catalog_override = repo.path_join("art/characters/reviews/all-actions-construction/review.json")
 root.add_child(trial)
 await draw_frame()
 s.check("real_full_package_loaded", trial.head_ready and trial.head_error == "" and trial.uses_registered_package())
 if not s.passed(): print("ORGANIZATION_ERROR ",trial.head_error); quit(1); return
 review = trial.review_panel
 s.check("all_24_clips", trial.head_library.full_clips.size() == 24)
 for id in trial.head_library.full_clips:
  var clip: Dictionary = trial.head_library.full_clips[id]
  var action: String = clip.action_id
  var direction: String = clip.direction
  review.select_clip(direction,action)
  review.set_playing(false)
  var phase := 0.0
  for index in clip.textures.size():
   review.preview_phase_ms = phase
   review.refresh_preview()
   await draw_frame()
   s.check(id+str(index)+"_real_texture",review.current_pose_index()==index and review.motion_view.texture==clip.textures[index])
   s.check(id+str(index)+"_gpu_image",not clip.textures[index].get_image().is_empty())
   phase += float(clip.durations_ms[index])
   pose_count += 1
  if action == "idle": continue
  trial.reset_position()
  trial.actor.position = Vector2(330,230)
  trial.facing = direction
  trial.run_requested = action == "run"
  trial.refresh_pose()
  var start: Vector2 = trial.actor.position
  if action in ["walk","run"]: Input.action_press("trial_walk_"+direction)
  else: s.check(id+"_farm_starts",trial.start_farming_sample(action))
  var seen: Dictionary = {}
  var deadline = Time.get_ticks_msec() + int(phase / float(trial.head_library.runtime.clips[id].playback_rate) / trial.speed_factor) + 300
  while Time.get_ticks_msec() < deadline:
   await draw_frame()
   if trial.current_action == action:
    var index: int = clip.textures.find(trial.pose.texture)
    if index >= 0: seen[index] = true
  if action in ["walk","run"]: Input.action_release("trial_walk_"+direction)
  trial.run_requested = false
  await physics_frame
  await physics_frame
  await draw_frame()
  s.check(id+"_continuous_poses",seen.size() == clip.textures.size())
  s.check(id+"_movement",trial.actor.position.distance_to(start)>1 if action in ["walk","run"] else trial.actor.position==start)
  s.check(id+"_returns_idle",trial.current_action=="idle" and trial.pose.texture==trial.head_library.full_clips["idle-"+direction].textures[0])
 s.check("all_84_poses",pose_count==84)
 review.select_clip("south","walk")
 review.set_playing(false)
 await draw_frame()
 s.check("screenshot",root.get_texture().get_image().save_png(screenshot)==OK)
 print("ORGANIZATION_ACTUAL clips=",trial.head_library.full_clips.size()," poses=",pose_count," checks=",s.checks.size()," passed=",s.passed())
 quit(0 if s.passed() else 1)
