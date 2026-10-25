extends SceneTree

const BASE = 'res://'
const DURATIONS = [0.23, 0.12, 0.23, 0.32]
var elapsed := 0.0
var canvas: ReviewCanvas
var captured := false

class ReviewCanvas extends Node2D:
	var textures: Array[Texture2D] = []
	var current := 0
	const SCALE := 138.0 / 582.0
	func _draw() -> void:
		draw_rect(Rect2(0, 0, 1100, 650), Color('#26312e'))
		draw_rect(Rect2(0, 300, 1100, 350), Color('#ece4cf'))
		var font := ThemeDB.fallback_font
		draw_string(font, Vector2(26, 30), 'HOE WEST - REWORK REQUIRED - scale 138/582; candidate about 135px tall', HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color.WHITE)
		for index in range(textures.size()):
			var p := Vector2(40 + index * 270, 60)
			draw_texture_rect(textures[index], Rect2(p, Vector2(768, 768) * SCALE), false)
			draw_string(font, p + Vector2(0, 218), 'Frame %d' % index, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.WHITE)
		for xx in [260, 720]:
			draw_texture_rect(textures[current], Rect2(Vector2(xx, 354), Vector2(768, 768) * SCALE), false)
			draw_line(Vector2(xx - 20, 354 + 708 * SCALE), Vector2(xx + 145, 354 + 708 * SCALE), Color('#a09578'), 1)
		draw_string(font, Vector2(28, 620), 'Looping complete action - dark and light background / frame %d / no gameplay or save service' % current, HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color('#253028'))

func _initialize() -> void:
	root.size = Vector2i(1100, 650)
	root.title = 'Hoe West Candidate - Independent Native Review'
	root.content_scale_size = Vector2i(1100, 650)
	canvas = ReviewCanvas.new()
	canvas.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	for index in range(4):
		var image := Image.load_from_file(ProjectSettings.globalize_path(BASE + 'registered/hoe_west_%d.png' % index))
		canvas.textures.append(ImageTexture.create_from_image(image))
	root.add_child(canvas)

func _process(delta: float) -> bool:
	elapsed += delta
	var phase := fmod(elapsed, 0.9)
	var cumulative := 0.0
	for index in range(4):
		cumulative += DURATIONS[index]
		if phase < cumulative:
			canvas.current = index
			break
	canvas.queue_redraw()
	if elapsed > 0.4 and not captured:
		captured = true
		RenderingServer.frame_post_draw.connect(_capture, CONNECT_ONE_SHOT)
	if elapsed >= 9.0:
		print('HOE_NATIVE_REVIEW ten complete 900ms cycles; no gameplay/save services loaded')
		quit()
	return false

func _capture() -> void:
	root.get_texture().get_image().save_png(ProjectSettings.globalize_path(BASE + 'evidence/native-scale-review.png'))
