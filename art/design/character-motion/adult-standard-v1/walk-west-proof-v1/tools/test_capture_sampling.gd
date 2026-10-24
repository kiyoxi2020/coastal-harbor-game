extends SceneTree

func _initialize() -> void:
	var review = load("res://review.tscn").instantiate()
	if not review.has_method("continuous_interval_ms") or not review.has_method("capture_complete"):
		printerr("FAIL: capture must derive sampling interval and enforce duration/count/pose coverage together")
		review.free()
		quit(1)
		return
	review.timeline.configure([80, 80, 80, 80])
	if not is_equal_approx(review.continuous_interval_ms(), 40.0):
		printerr("FAIL: 80ms poses need <=40ms sampling interval")
		review.free()
		quit(1)
		return
	var all_poses := {0: true, 1: true, 2: true, 3: true}
	review.elapsed_ms = 3200.0
	if review.capture_complete(37, all_poses) or review.capture_complete(39, all_poses) or review.capture_complete(40, {0: true}):
		printerr("FAIL: ten cycles alone cannot finish with insufficient samples/poses")
		review.free()
		quit(1)
		return
	review.elapsed_ms = 3199.0
	if review.capture_complete(40, all_poses):
		printerr("FAIL: forty samples cannot finish before ten cycles")
		review.free()
		quit(1)
		return
	review.elapsed_ms = 3200.0
	if not review.capture_complete(40, all_poses):
		printerr("FAIL: complete evidence may finish")
		review.free()
		quit(1)
		return
	review.timeline.configure([160, 160, 160, 160])
	if not is_equal_approx(review.continuous_interval_ms(), 1000.0 / 24.0):
		printerr("FAIL: longer poses still need >=24fps target sampling")
		review.free()
		quit(1)
		return
	review.timeline.configure([12, 40, 80, 100])
	if not is_equal_approx(review.continuous_interval_ms(), 6.0):
		printerr("FAIL: minimum pose duration controls sampling")
		review.free()
		quit(1)
		return
	review.free()
	print("PASS capture sampling: minimum half-frame / 24fps interval, >=10 cycles, >=40 samples, all four poses")
	quit(0)
