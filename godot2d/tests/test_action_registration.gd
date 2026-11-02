extends SceneTree
const Support = preload("res://tests/life_test_support.gd")
const MANIFEST = "res://assets/characters/integrations/adult-v5-pixel-visible-r010/manifest.json"
const FRAMES = "res://resources/player_body_v5_frames.tres"
var s := Support.new()
func _initialize() -> void:
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
	var frames := load(FRAMES) as SpriteFrames
	var geometry: Dictionary = data.geometry
	s.check("current_24_clips", data.clips.size() == 24 and frames.get_animation_names().size() == 24)
	s.check("one_canvas_and_root", Vector2(geometry.canvas_px[0], geometry.canvas_px[1]) == Vector2(260, 228) and Vector2(geometry.root_anchor_px[0], geometry.root_anchor_px[1]) == Vector2(125, 201) and is_equal_approx(geometry.world_scale, 0.25))
	var total := 0
	for clip in data.clips:
		var valid: bool = frames.has_animation(clip.name) and frames.get_frame_count(clip.name) == clip.frames.size()
		if valid:
			for i in range(clip.frames.size()):
				var image := frames.get_frame_texture(clip.name, i).get_image()
				valid = valid and image.get_size() == Vector2i(geometry.canvas_px[0], geometry.canvas_px[1])
				valid = valid and clip.frames[i].duration_ms > 0 and is_equal_approx(frames.get_frame_duration(clip.name, i) / frames.get_animation_speed(clip.name), clip.frames[i].duration_ms / 1000.0)
			total += clip.frames.size()
		s.check(str(clip.name) + "_fixed_registration", valid)
	s.check("current_108_frames", total == 108)
	print("ACTION_REGISTRATION checks=", s.checks.size(), " passed=", s.passed())
	quit(0 if s.passed() else 1)
