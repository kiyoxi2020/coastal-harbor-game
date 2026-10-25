extends Node2D
## Isolated experience: schema1 west proof or explicit complete schema2 locomotion.
const SOURCE_RATE := 72.0
const BASE_FRAME_MS := 80.0
const DIRECTIONS := ["south", "west", "east", "north"]
var frames: Dictionary = {}
var frame_metadata: Array = []
var clips: Dictionary = {}
var move_policy: Dictionary = {}
var schema_version: int = 1
var current_action := "walk"
var facing := "west"
var phase_ms := 0.0
var idle_phase_ms := 0.0
var garment := "A"
var speed_factor := 0.75
var load_error := ""
var motion_error := ""
var artifact_digest := ""
var focused := true
var run_candidate_root := ""
var run_candidate_digest := ""
var run_garments_digest := ""
var run_requested := false
var run_base_frame_count := 0
# Remains the existing west proof until the complete new root has passed review.
var art_root := ProjectSettings.globalize_path("res://").path_join("../art/design/character-motion/adult-standard-v1/walk-west-proof-v1").simplify_path()
@onready var actor: CharacterBody2D = $HarborExterior/DepthSortedObjects/TrialActor
@onready var pose: Sprite2D = $HarborExterior/DepthSortedObjects/TrialActor/Pose
@onready var status: Label = $TrialUI/Panel/Margin/Rows/Status
@onready var speed_slider: HSlider = $TrialUI/Panel/Margin/Rows/Controls/Speed

func _ready() -> void:
	var codes := {"west": [KEY_A, KEY_LEFT], "east": [KEY_D, KEY_RIGHT], "north": [KEY_W, KEY_UP], "south": [KEY_S, KEY_DOWN]}
	for direction in codes:
		var action_name := "trial_walk_" + str(direction)
		if not InputMap.has_action(action_name):
			InputMap.add_action(action_name)
			for code in codes[direction]:
				var event := InputEventKey.new()
				event.physical_keycode = code
				InputMap.action_add_event(action_name, event)
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--trial-art-root="):
			art_root = argument.trim_prefix("--trial-art-root=")
		elif argument.begins_with("--trial-run-root="):
			run_candidate_root = argument.trim_prefix("--trial-run-root=")
	$WorldCamera.target = actor
	$WorldCamera.update_position()
	$WorldCamera.force_update_scroll()
	speed_slider.value_changed.connect(set_speed_factor)
	$TrialUI/Panel/Margin/Rows/Controls/Short.pressed.connect(func(): set_garment("A"))
	$TrialUI/Panel/Margin/Rows/Controls/Long.pressed.connect(func(): set_garment("B"))
	$TrialUI/Panel/Margin/Rows/Controls/Reset.pressed.connect(reset_position)
	$TrialUI/Panel/Margin/Rows/Controls/Exit.pressed.connect(func(): get_tree().quit())
	load_art(art_root)
	if run_candidate_root != "":
		load_run_candidate(run_candidate_root)
		$TrialUI/Panel/Margin/Rows/Instructions.text = "西向跑步小样 · A / 左箭头行走，按住 Shift 跑步 · 松开停步 · R 回起点 · 1 / 2 换上衣，跑步仅西向"
	refresh_pose()
	get_window().title = "潮港旧屋 · 人物步行体验（WASD / 方向键，R回起点）"

func reject_art(message: String) -> bool:
	load_error = message
	pose.visible = false
	refresh_status()
	return false

func positive_integer(value: Variant) -> bool:
	return (value is float or value is int) and is_finite(float(value)) and float(value) > 0 and float(value) == floor(float(value))

func relative_file(value: Variant) -> bool:
	return value is String and not value.is_empty() and not value.is_absolute_path() and not ".." in value.split("/")

func load_art(directory: String) -> bool:
	clear_run_candidate()
	var manifest_path := directory.path_join("baked/export-manifest.json")
	if not FileAccess.file_exists(manifest_path): return reject_art("找不到小样资源，请从完整源码目录启动。")
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
	if not parsed is Dictionary: return reject_art("小样清单无效。")
	var version: Variant = parsed.get("schema_version")
	if not (version is float or version is int) or float(version) not in [1.0, 2.0]: return reject_art("不支持的小样schema。")
	if parsed.get("canvas_px") != [512.0, 768.0] or parsed.get("root_anchor_px") != [256.0, 708.0]: return reject_art("小样画布或根点不匹配。")
	if not is_equal_approx(float(parsed.get("display_scale", 0)), 138.0 / 582.0): return reject_art("小样显示比例不匹配。")
	var metadata: Variant = parsed.get("frames")
	if not metadata is Array or metadata.is_empty(): return reject_art("小样全局姿态表缺失。")
	var indices := {}
	for i in range(metadata.size()):
		var frame: Variant = metadata[i]
		if not frame is Dictionary or not frame.get("pose_id") is String or frame["pose_id"].is_empty() or indices.has(frame["pose_id"]) or not positive_integer(frame.get("duration_ms")):
			return reject_art("小样姿态或原始节拍不匹配。")
		indices[frame["pose_id"]] = i
	var resolved_clips := {}
	var policies := {"walk": {"base_world_speed": SOURCE_RATE, "playback_rate": 0.75}}
	if version == 1:
		if metadata.size() != 4: return reject_art("单侧小样必须四帧。")
		for i in range(4):
			if metadata[i]["pose_id"] != "walk_w_%d" % i or metadata[i]["duration_ms"] != BASE_FRAME_MS: return reject_art("单侧小样姿态或原始节拍不匹配。")
		resolved_clips = {"walk": {"west": [0, 1, 2, 3]}}
	else:
		var actions: Variant = parsed.get("actions")
		if not actions is Dictionary or actions.size() != 2 or not actions.has("idle") or not actions.has("walk"): return reject_art("四向小样缺少idle/walk动作。")
		var assigned := {}
		for action in ["idle", "walk"]:
			var clip: Variant = actions[action]
			if not clip is Dictionary or clip.get("loop") != true: return reject_art("小样动作循环声明无效。")
			var directions: Variant = clip.get("directions")
			if not directions is Dictionary or directions.size() != 4: return reject_art("小样缺少完整四向动作。")
			resolved_clips[action] = {}
			for direction in DIRECTIONS:
				var poses: Variant = directions.get(direction)
				if not poses is Array or poses.is_empty(): return reject_art("小样缺少方向：" + direction)
				resolved_clips[action][direction] = []
				for pose_id in poses:
					if not pose_id is String or not indices.has(pose_id) or assigned.has(pose_id): return reject_art("小样姿态引用重复或不存在。")
					var index: int = indices[pose_id]
					if metadata[index].get("action") != action or metadata[index].get("direction") != direction: return reject_art("小样动作与方向映射不匹配。")
					assigned[pose_id] = true
					resolved_clips[action][direction].append(index)
		if assigned.size() != metadata.size(): return reject_art("小样动作未覆盖全部姿态。")
		var supplied: Variant = parsed.get("move_policy")
		if not supplied is Dictionary or supplied.size() != 2: return reject_art("小样移动策略缺失。")
		for action in ["idle", "walk"]:
			var policy: Variant = supplied.get(action)
			if not policy is Dictionary: return reject_art("小样移动策略缺失。")
			var speed: Variant = policy.get("base_world_speed")
			var rate: Variant = policy.get("playback_rate")
			if not (speed is float or speed is int) or not is_finite(float(speed)) or (speed <= 0 if action == "walk" else speed != 0): return reject_art("小样基线速度无效。")
			if not (rate is float or rate is int) or not is_finite(float(rate)) or rate <= 0 or rate > 1: return reject_art("小样播放速度无效。")
		policies = supplied
		var contract: Variant = parsed.get("source_contract")
		if not contract is Dictionary or contract.is_empty(): return reject_art("小样源依赖合同缺失。")
		var inputs: Variant = parsed.get("inputs")
		if not inputs is Dictionary: return reject_art("小样源依赖索引缺失。")
		var source_root := directory.path_join("baked").path_join(str(parsed.get("source_root", ".."))).simplify_path()
		for reference in contract:
			if not relative_file(reference) or not contract[reference] is String or contract[reference].length() != 64 or not inputs.has(reference) or not inputs[reference] is Dictionary or inputs[reference].get("sha256") != contract[reference]: return reject_art("小样源依赖声明无效。")
			var dependency := source_root.path_join(reference)
			if not FileAccess.file_exists(dependency) or FileAccess.get_sha256(dependency) != contract[reference]: return reject_art("小样源依赖缺失或哈希不匹配。")
	var recipes: Variant = parsed.get("recipes")
	if not recipes is Dictionary or recipes.size() != 2 or not recipes.has("A") or not recipes.has("B"): return reject_art("小样衣物配方缺失。")
	var loaded := {}
	for recipe in ["A", "B"]:
		if not recipes[recipe] is Dictionary: return reject_art("小样衣物配方无效。")
		var entries: Variant = recipes[recipe].get("frames")
		if not entries is Array or entries.size() != metadata.size(): return reject_art("小样衣物姿态不完整。")
		loaded[recipe] = []
		for i in range(metadata.size()):
			var entry: Variant = entries[i]
			if not entry is Dictionary or entry.get("pose_id") != metadata[i]["pose_id"] or entry.get("duration_ms") != metadata[i]["duration_ms"]: return reject_art("小样配方姿态或时序不匹配。")
			if version == 2 and (entry.get("action") != metadata[i]["action"] or entry.get("direction") != metadata[i]["direction"]): return reject_art("小样配方动作方向不匹配。")
			if entry.get("file") != "%s_%d.png" % [recipe, i]: return reject_art("小样文件路径不匹配。")
			var image_path := directory.path_join("baked").path_join(entry["file"])
			if not FileAccess.file_exists(image_path) or FileAccess.get_sha256(image_path) != entry.get("sha256"): return reject_art("小样纹理缺失或哈希不匹配。")
			var image := Image.load_from_file(image_path)
			if image == null or image.get_size() != Vector2i(512, 768): return reject_art("小样纹理尺寸不匹配。")
			loaded[recipe].append(ImageTexture.create_from_image(image))
	frames = loaded
	frame_metadata = metadata
	clips = resolved_clips
	move_policy = policies
	schema_version = int(version)
	facing = "south" if schema_version == 2 else "west"
	current_action = "idle" if schema_version == 2 else "walk"
	phase_ms = 0.0
	idle_phase_ms = 0.0
	speed_factor = clampf(float(move_policy["walk"]["playback_rate"]), 0.5, 1.0)
	speed_slider.set_value_no_signal(speed_factor)
	art_root = directory
	artifact_digest = str(parsed.get("artifact_digest", ""))
	load_error = ""
	motion_error = ""
	pose.visible = true
	refresh_pose()
	return true

func clear_run_candidate() -> void:
	if run_base_frame_count > 0:
		frame_metadata.resize(run_base_frame_count)
		for recipe in frames: frames[recipe].resize(run_base_frame_count)
	clips.erase("run")
	move_policy.erase("run")
	run_base_frame_count = 0
	run_candidate_digest = ""
	run_garments_digest = ""
	if current_action == "run": current_action = "idle"

func reject_run_candidate(message: String) -> bool:
	motion_error = message
	refresh_pose()
	return false

func load_run_candidate(directory: String) -> bool:
	# Authoring proof with optional dependency-bound garment bakes; not a release.
	clear_run_candidate()
	if schema_version != 2 or load_error != "": return reject_run_candidate("跑步候选需要已加载的四向walk/idle。")
	var manifest_path := directory.path_join("candidate.json")
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(manifest_path)) if FileAccess.file_exists(manifest_path) else null
	if not data is Dictionary or data.get("template_id") != "adult-standard-v1" or data.get("status") != "unapproved_complete_frame_proof": return reject_run_candidate("跑步候选合同缺失或无效。")
	if data.get("walk_artifact_digest") != artifact_digest: return reject_run_candidate("跑步候选与当前walk版本不匹配。")
	if data.get("canvas_px") != [512.0, 768.0] or data.get("root_anchor_px") != [256.0, 708.0] or not is_equal_approx(float(data.get("display_scale", 0)), 138.0 / 582.0): return reject_run_candidate("跑步候选坐标不匹配。")
	var sources: Variant = data.get("inputs")
	if not sources is Dictionary or sources.is_empty(): return reject_run_candidate("跑步候选依赖缺失。")
	for reference in sources:
		if not relative_file(reference) or not sources[reference] is String or FileAccess.get_sha256(directory.path_join(reference)) != sources[reference]: return reject_run_candidate("跑步候选依赖哈希不匹配。")
	var entries: Variant = data.get("frames")
	if not entries is Array or entries.size() != 4 or data.get("phase_map") != [0.0, 1.0, 2.0, 3.0] or clips.walk.west.size() != 4: return reject_run_candidate("跑步候选接触相位映射无效。")
	if data.get("base_world_speed") != 108.0: return reject_run_candidate("跑步候选速度无效。")
	var textures: Array = []
	var metadata: Array = []
	for i in range(4):
		var entry: Variant = entries[i]
		if not entry is Dictionary or entry.get("pose_id") != "run_west_%d" % i or not positive_integer(entry.get("duration_ms")) or not relative_file(entry.get("file")): return reject_run_candidate("跑步候选姿态无效。")
		var path := directory.path_join(str(entry.file))
		if not sources.has(entry.file) or FileAccess.get_sha256(path) != sources[entry.file]: return reject_run_candidate("跑步候选纹理哈希不匹配。")
		var image := Image.load_from_file(path)
		if image == null or image.get_size() != Vector2i(512, 768): return reject_run_candidate("跑步候选纹理尺寸不匹配。")
		textures.append(ImageTexture.create_from_image(image))
		metadata.append({"pose_id": entry.pose_id, "duration_ms": entry.duration_ms, "action": "run", "direction": "west"})
	var garment_textures := {"A": textures}
	var garment_path := directory.path_join("run-garments.json")
	if FileAccess.file_exists(garment_path):
		var layered: Variant = JSON.parse_string(FileAccess.get_file_as_string(garment_path))
		if not layered is Dictionary or layered.get("candidate_manifest_sha256") != FileAccess.get_sha256(manifest_path): return reject_run_candidate("跑步衣物与当前动作版本不匹配。")
		var dependencies: Variant = layered.get("inputs")
		var recipes: Variant = layered.get("recipes")
		if not dependencies is Dictionary or dependencies.is_empty() or not recipes is Dictionary or recipes.size() != 2: return reject_run_candidate("跑步衣物依赖或配方缺失。")
		for reference in dependencies:
			if not relative_file(reference) or not dependencies[reference] is String or FileAccess.get_sha256(directory.path_join(reference)) != dependencies[reference]: return reject_run_candidate("跑步衣物依赖哈希不匹配。")
		for recipe in ["A", "B"]:
			var files: Variant = recipes.get(recipe)
			if not files is Array or files.size() != 4: return reject_run_candidate("跑步衣物缺少完整四帧。")
			var loaded: Array = []
			for reference in files:
				if not relative_file(reference) or not dependencies.has(reference): return reject_run_candidate("跑步衣物纹理未登记。")
				var picture := Image.load_from_file(directory.path_join(reference))
				if picture == null or picture.get_size() != Vector2i(512, 768): return reject_run_candidate("跑步衣物纹理尺寸不匹配。")
				loaded.append(ImageTexture.create_from_image(picture))
			garment_textures[recipe] = loaded
		run_garments_digest = FileAccess.get_sha256(garment_path)
	run_base_frame_count = frame_metadata.size()
	frame_metadata.append_array(metadata)
	for recipe in garment_textures: frames[recipe].append_array(garment_textures[recipe])
	clips.run = {"west": range(run_base_frame_count, run_base_frame_count + 4)}
	move_policy.run = {"base_world_speed": 108.0, "playback_rate": 0.75}
	run_candidate_digest = FileAccess.get_sha256(manifest_path)
	$TrialUI/Panel/Margin/Rows/Scope.text = "西向跑步：%s。换装小样待视觉评审；本入口不读写存档。" % ("短袖／长袖" if garment_textures.has("B") else "仅短袖")
	motion_error = ""
	refresh_pose()
	return true

func has_motion_garment(action: String, direction: String, recipe: String) -> bool:
	var indices: Array = clips.get(action, {}).get(direction, [])
	if indices.is_empty() or not frames.has(recipe): return false
	for index in indices:
		if index >= frames[recipe].size() or frames[recipe][index] == null: return false
	return true

func set_locomotion_action(value: String) -> bool:
	if value not in ["walk", "run"] or not has_motion_garment(value, facing, garment):
		return reject_run_candidate("当前上衣或方向未提供此动作资源。")
	if current_action == value: return true
	# Map the within-pose fraction, including unequal durations, by observed phase.
	if current_action in ["walk", "run"]:
		var remaining := fposmod(phase_ms, clip_duration(current_action, facing))
		var source: Array = clips[current_action][facing]
		var target: Array = clips[value][facing]
		for i in range(source.size()):
			var duration: float = frame_metadata[source[i]].duration_ms
			if remaining < duration:
				phase_ms = 0.0
				for j in range(i): phase_ms += float(frame_metadata[target[j]].duration_ms)
				phase_ms += remaining / duration * float(frame_metadata[target[i]].duration_ms)
				break
			remaining -= duration
	current_action = value
	motion_error = ""
	refresh_pose()
	return true

func locomotion_speed() -> float:
	return float(move_policy.get(current_action, move_policy.get("walk", {})).get("base_world_speed", SOURCE_RATE)) * speed_factor

func walk_speed() -> float:
	return float(move_policy.get("walk", {}).get("base_world_speed", SOURCE_RATE)) * speed_factor

func frame_duration_ms() -> float:
	var rate: float = speed_factor if current_action in ["walk", "run"] else float(move_policy.get("idle", {}).get("playback_rate", 1.0))
	return float(frame_metadata[current_frame()]["duration_ms"]) / rate if not frame_metadata.is_empty() else BASE_FRAME_MS / speed_factor

func set_speed_factor(value: float) -> void:
	speed_factor = clampf(value, 0.5, 1.0)
	speed_slider.set_value_no_signal(speed_factor)
	refresh_status()

func set_garment(value: String) -> void:
	if value not in ["A", "B"]: return
	if not has_motion_garment(current_action, facing, value):
		reject_run_candidate("当前动作缺少这套上衣资源。")
		return
	garment = value
	motion_error = ""
	refresh_pose()

func clip_duration(action: String, direction: String) -> float:
	var total := 0.0
	for index in clips.get(action, {}).get(direction, []):
		total += float(frame_metadata[index]["duration_ms"])
	return total

func set_motion_direction(value: String) -> bool:
	if current_action == "run" and value != "west":
		return reject_run_candidate("跑步其他方向尚未制作；松开 Shift 可行走转向。")
	if current_action == "run": return true
	if not clips.get("walk", {}).has(value):
		motion_error = "当前小样未声明方向：" + value
		refresh_status()
		return false
	var previous_cycle := clip_duration("walk", facing)
	var fraction := phase_ms / previous_cycle if previous_cycle > 0 else 0.0
	facing = value
	phase_ms = fposmod(fraction, 1.0) * clip_duration("walk", facing)
	motion_error = ""
	refresh_pose()
	return true

func current_frame() -> int:
	var entries: Array = clips.get(current_action, {}).get(facing, [])
	if entries.is_empty(): return 0
	var elapsed := fposmod(phase_ms if current_action in ["walk", "run"] else idle_phase_ms, clip_duration(current_action, facing))
	for index in entries:
		var duration: float = frame_metadata[index]["duration_ms"]
		if elapsed < duration: return index
		elapsed -= duration
	return entries[-1]

func refresh_pose() -> void:
	if load_error == "" and frames.has(garment): pose.texture = frames[garment][current_frame()]
	refresh_status()

func refresh_status() -> void:
	if not is_instance_valid(status): return
	if load_error != "": status.text = load_error
	elif motion_error != "": status.text = motion_error
	else: status.text = "%s · %s / %s · 速度 %d%%（%.0f 世界单位/秒） · 当前帧 %.1f ms" % ["奶油短袖" if garment == "A" else "蓝色长袖", current_action, facing, roundi(speed_factor * 100), locomotion_speed() if current_action == "run" else walk_speed(), frame_duration_ms()]

func reset_position() -> void:
	actor.position = $Start.position
	actor.velocity = Vector2.ZERO
	phase_ms = 0.0
	idle_phase_ms = 0.0
	current_action = "idle" if schema_version == 2 else "walk"
	refresh_pose()

func movement_input() -> Vector2:
	return Input.get_vector("trial_walk_west", "trial_walk_east", "trial_walk_north", "trial_walk_south") if focused else Vector2.ZERO

func direction_from_vector(value: Vector2) -> String:
	if absf(value.x) > absf(value.y): return "east" if value.x > 0 else "west"
	return "south" if value.y > 0 else "north"

func _physics_process(delta: float) -> void:
	if load_error != "": return
	var requested := movement_input()
	var supported := true
	if clips.has("run") and not requested.is_zero_approx():
		if not run_requested and current_action == "run": set_locomotion_action("walk")
	if not requested.is_zero_approx(): supported = set_motion_direction(direction_from_vector(requested))
	if supported and clips.has("run") and not requested.is_zero_approx(): supported = set_locomotion_action("run" if run_requested else "walk")
	var before := actor.position
	actor.velocity = requested * (locomotion_speed() if current_action == "run" else walk_speed()) if supported else Vector2.ZERO
	actor.move_and_slide()
	var actual := actor.position - before
	# Recovery after release/opposing a wall must not advance the walking clock.
	var distance := actual.length() if actual.dot(requested) > 0.001 else 0.0
	if distance > 0.001:
		if current_action != "run": current_action = "walk"
		phase_ms = fposmod(phase_ms + distance / float(move_policy[current_action]["base_world_speed"]) * 1000.0, clip_duration(current_action, facing))
	elif schema_version == 2:
		current_action = "idle"
		idle_phase_ms += delta * 1000.0 * float(move_policy["idle"]["playback_rate"])
	refresh_pose()

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.physical_keycode == KEY_SHIFT:
		run_requested = event.pressed
		return
	if not event is InputEventKey or not event.pressed or event.echo: return
	match event.physical_keycode:
		KEY_1: set_garment("A")
		KEY_2: set_garment("B")
		KEY_R: reset_position()
		KEY_MINUS: set_speed_factor(speed_factor - 0.05)
		KEY_EQUAL: set_speed_factor(speed_factor + 0.05)
		KEY_ESCAPE: get_tree().quit()

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_WINDOW_FOCUS_OUT:
		focused = false
		run_requested = false
	elif what == NOTIFICATION_WM_WINDOW_FOCUS_IN: focused = true
