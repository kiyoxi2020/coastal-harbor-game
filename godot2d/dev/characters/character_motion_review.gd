extends PanelContainer
## Inspection only: samples the trial's actual textures without mutating its actor.
const DIRECTIONS := ["south", "west", "east", "north"]
const ACTIONS := ["idle", "walk", "run", "water", "hoe", "harvest"]
const FARMING_ACTIONS := ["water", "hoe", "harvest"]
var farming_library
var farming_error := ""
var trial
var review_direction := "south"
var review_action := "run"
var preview_phase_ms := 0.0
var playing := true
@onready var direction_buttons: Array[Button] = [$Margin/Rows/Directions/South, $Margin/Rows/Directions/West, $Margin/Rows/Directions/East, $Margin/Rows/Directions/North]
@onready var action_buttons: Array[Button] = [$Margin/Rows/Actions/Idle, $Margin/Rows/Actions/Walk, $Margin/Rows/Actions/Run, $Margin/Rows/Actions/FarmActions/Water, $Margin/Rows/Actions/FarmActions/Hoe, $Margin/Rows/Actions/FarmActions/Harvest]
@onready var reference_view: Sprite2D = $Margin/Rows/Views/Reference/Slot/Texture
@onready var motion_view: Sprite2D = $Margin/Rows/Views/Motion/Slot/Texture
@onready var play_button: CheckButton = $Margin/Rows/Playback/Play
@onready var frame_label: Label = $Margin/Rows/Playback/Frame
@onready var message: Label = $Margin/Rows/Message

func _ready() -> void:
	for i in range(DIRECTIONS.size()):
		var direction: String = DIRECTIONS[i]
		direction_buttons[i].pressed.connect(func(): select_clip(direction, review_action))
	for i in range(ACTIONS.size()):
		var action: String = ACTIONS[i]
		action_buttons[i].pressed.connect(func(): select_clip(review_direction, action))
	play_button.toggled.connect(set_playing)
	$Margin/Rows/Playback/Next.pressed.connect(step_frame)

func bind_trial(value) -> void:
	trial = value
	refresh_preview()

func select_clip(direction: String, action: String) -> void:
	if direction not in DIRECTIONS or action not in ACTIONS: return
	review_direction = direction
	review_action = action
	preview_phase_ms = 0.0
	for i in range(DIRECTIONS.size()): direction_buttons[i].set_pressed_no_signal(DIRECTIONS[i] == direction)
	for i in range(ACTIONS.size()): action_buttons[i].set_pressed_no_signal(ACTIONS[i] == action)
	refresh_preview()

func set_playing(value: bool) -> void:
	playing = value
	play_button.set_pressed_no_signal(value)

func load_farming_samples(project_root: String, catalog_path: String = "") -> bool:
	if catalog_path.is_empty(): catalog_path = project_root.path_join("art/characters/reviews/farming/catalog.json")
	$Margin/Rows/Actions/FarmActions.show()
	var path := "res://dev/characters/character_farming_review.gd"
	if not ResourceLoader.exists(path):
		farming_error = "农事样例加载器未找到。"
		return false
	farming_library = load(path).new()
	var loaded: bool = farming_library.load_catalog(project_root,catalog_path)
	farming_error = farming_library.error
	refresh_preview()
	return loaded

func farming_clip() -> Dictionary:
	if farming_library == null or not is_instance_valid(trial): return {}
	return farming_library.get_clip(review_action, review_direction, trial.garment)

func preview_durations() -> Array:
	if not is_instance_valid(trial): return []
	if review_action in FARMING_ACTIONS:
		return farming_clip().get("durations_ms", [])
	var durations: Array = []
	for index in trial.clips.get(review_action, {}).get(review_direction, []):
		durations.append(trial.frame_metadata[index].duration_ms)
	return durations

func preview_available() -> bool:
	if not is_instance_valid(trial): return false
	if review_action in FARMING_ACTIONS: return not farming_clip().is_empty()
	return trial.has_motion_garment(review_action, review_direction, trial.garment)

func preview_duration() -> float:
	var total := 0.0
	for duration in preview_durations(): total += float(duration)
	return total

func current_pose_index() -> int:
	var duration := preview_duration()
	var durations := preview_durations()
	if duration <= 0 or durations.is_empty(): return 0
	var elapsed := fposmod(preview_phase_ms, duration)
	for i in range(durations.size()):
		if elapsed < float(durations[i]): return i
		elapsed -= float(durations[i])
	return durations.size() - 1

func advance_preview(delta: float) -> void:
	if not is_instance_valid(trial): return
	var duration := preview_duration()
	if playing and duration > 0 and preview_available():
		var rate: float = trial.speed_factor if review_action in ["walk", "run"] else float(trial.move_policy.get("idle", {}).get("playback_rate", 1.0))
		if review_action in FARMING_ACTIONS: rate = 1.0
		preview_phase_ms = fposmod(preview_phase_ms + delta * 1000.0 * rate, duration)
	refresh_preview()

func step_frame() -> void:
	set_playing(false)
	if not preview_available(): return
	var durations := preview_durations()
	var next := (current_pose_index() + 1) % durations.size()
	preview_phase_ms = 0.0
	for i in range(next): preview_phase_ms += float(durations[i])
	refresh_preview()

func refresh_preview() -> void:
	if not is_instance_valid(trial): return
	reference_view.texture = null
	motion_view.texture = null
	$Margin/Rows/Views/Motion/Label.text = "当前动作"
	if trial.has_motion_garment("idle", review_direction, trial.garment):
		reference_view.texture = trial.frames[trial.garment][trial.clips.idle[review_direction][0]]
	if not preview_available():
		message.text = "此方向未提供这套上衣的动作；按 1 查看短袖，或选择其他方向。"
		if review_action in FARMING_ACTIONS:
			message.text = farming_error if farming_error != "" else ("农事样例仅有西向短袖；请选西，并按 1 查看短袖。" if farming_library == null or farming_library.catalog_version == 1 else "当前方向或上衣的农事资源未提供；请检查目录。")
		frame_label.text = "资源未提供"
		return
	var index := current_pose_index()
	if review_action in FARMING_ACTIONS:
		var clip := farming_clip()
		motion_view.texture = clip.textures[index]
		# Whole-frame placement from the recorded root, preserving source density.
		motion_view.scale = reference_view.scale * (float(clip.display_scale) / (138.0 / 582.0))
		motion_view.position = reference_view.position + Vector2(256,708) * reference_view.scale - clip.root_anchor_px * motion_view.scale
		$Margin/Rows/Views/Motion/Label.text = "农事动作候选" if farming_library.catalog_version == 2 else "农事关键姿态"
		frame_label.text = "第 %d / %d 姿态" % [index + 1, clip.textures.size()]
		message.text = clip.note
		return
	motion_view.scale = reference_view.scale
	motion_view.position = reference_view.position
	motion_view.texture = trial.frames[trial.garment][trial.clips[review_action][review_direction][index]]
	frame_label.text = "第 %d / %d 帧" % [index + 1, trial.clips[review_action][review_direction].size()]
	var note: String = trial.diagnostic_note(review_action,review_direction,trial.garment)
	$Margin/Rows/Views/Motion/Label.text = "当前诊断稿" if note != "" else "当前动作"
	message.text = note if note != "" else "对比头部、身形和动作；是否通过由你确认。"

func _process(delta: float) -> void:
	if is_visible_in_tree(): advance_preview(delta)
