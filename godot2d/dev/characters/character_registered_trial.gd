extends "res://dev/characters/character_walk_trial.gd"
## Data adapter only: movement, clocks and preview remain in the shared trial.
const RegisteredSamples = preload("res://dev/characters/character_registered_samples.gd")
@export var preview_root_px := Vector2(112, 200)
var registered_samples = RegisteredSamples.new()
var registered_project_override := ""
var registered_suite_override := ""

func _ready() -> void:
	initialize_trial_shell()
	var project = ProjectSettings.globalize_path("res://..").simplify_path()
	if registered_project_override != "": project = registered_project_override
	var suite_path = project.path_join("art/characters/reviews/registered/review.json")
	if registered_suite_override != "": suite_path = registered_suite_override
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--registered-suite="): suite_path = argument.trim_prefix("--registered-suite=")
	load_registered(project, suite_path)

func load_registered(project: String, suite_path: String) -> bool:
	frames.clear(); clips.clear(); frame_metadata.clear(); move_policy.clear()
	artifact_digest = ""; phase_ms = 0; idle_phase_ms = 0
	pose.texture = null; actor.velocity = Vector2.ZERO
	if not registered_samples.load_samples(project, suite_path):
		load_error = registered_samples.error
		review_panel.preview_phase_ms = 0
		review_panel.set_playing(false)
		review_panel.reference_view.texture = null
		review_panel.motion_view.texture = null
		update_registered_controls()
		refresh_status()
		return false
	frames = registered_samples.frames
	clips = registered_samples.clips
	frame_metadata = registered_samples.frame_metadata
	artifact_digest = registered_samples.artifact_digest
	var geometry = registered_samples.geometry
	var root = Vector2(float(geometry.root_anchor_px[0]), float(geometry.root_anchor_px[1]))
	pose.scale = Vector2.ONE * float(registered_samples.runtime.world_scale) * float(geometry.display_scale)
	pose.offset = -root
	var preview_scale = Vector2.ONE * .5 * float(geometry.display_scale)
	review_panel.reference_view.scale = preview_scale
	review_panel.reference_view.position = preview_root_px - root * preview_scale
	review_panel.motion_view.scale = preview_scale
	review_panel.motion_view.position = review_panel.reference_view.position
	move_policy = {"walk": {"base_world_speed": registered_samples.runtime.walk_world_speed}, "idle": {"playback_rate": 1.0}}
	schema_version = 2
	current_action = "idle"
	facing = str(clips.walk.keys()[0])
	garment = "B"; phase_ms = 0; idle_phase_ms = 0; run_requested = false
	speed_factor = float(registered_samples.runtime.speed_factor)
	speed_slider.set_value_no_signal(speed_factor)
	load_error = ""; motion_error = ""
	review_enabled = true
	review_panel.review_direction = facing; review_panel.review_action = "walk"
	review_panel.bind_trial(self)
	review_panel.select_clip(facing, "walk")
	review_panel.visible = true
	update_registered_controls()
	refresh_pose()
	return true

func movement_input() -> Vector2:
	if load_error != "" or not focused: return Vector2.ZERO
	var requested = super.movement_input()
	if requested.x < 0 and not clips.get("walk", {}).has("west"): requested.x = 0
	if requested.x > 0 and not clips.get("walk", {}).has("east"): requested.x = 0
	if requested.y < 0 and not clips.get("walk", {}).has("north"): requested.y = 0
	if requested.y > 0 and not clips.get("walk", {}).has("south"): requested.y = 0
	return requested

func update_registered_controls() -> void:
	if not is_instance_valid(review_panel): return
	for button in review_panel.direction_buttons:
		button.disabled = not clips.get("walk", {}).has(str(button.name).to_lower())
	for index in range(review_panel.action_buttons.size()):
		var action = review_panel.ACTIONS[index]
		review_panel.action_buttons[index].disabled = not clips.get(action, {}).has(review_panel.review_direction)

func refresh_status() -> void:
	if not is_instance_valid(status): return
	if load_error != "": status.text = load_error
	elif motion_error != "": status.text = motion_error
	else:
		status.text = "%s · %s / %s · 速度 %d%%（%.0f 世界单位/秒） · 当前帧 %.1f ms" % ["原身体" if garment == "A" else "当前配方", current_action, facing, roundi(speed_factor * 100), walk_speed(), frame_duration_ms()]
