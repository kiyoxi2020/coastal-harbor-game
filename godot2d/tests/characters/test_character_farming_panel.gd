extends SceneTree
const Support = preload("res://tests/life_test_support.gd")
var s := Support.new()
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var fixture := preload("res://tests/characters/character_fixture_library.gd").farming_schema1("/private/tmp/coastal-layout-schema1-adapter")
	var trial = load("res://dev/characters/character_walk_trial.tscn").instantiate()
	trial.art_root = ProjectSettings.globalize_path("res://../art/characters/builds/locomotion-r001")
	root.add_child(trial)
	await process_frame
	trial.set_physics_process(false)
	var review = trial.review_panel
	s.check("farming_panel_adapter_exists", review.has_method("load_farming_samples"))
	if not review.has_method("load_farming_samples"):
		trial.queue_free();quit(1);return
	s.check("actual_farming_sources_load", review.load_farming_samples(fixture,fixture.path_join("catalog.json")))
	review.show();review.set_process(false)
	var counts := {"water":2,"hoe":4,"harvest":2}
	var world_before: Vector2 = trial.actor.position
	var phase_before: float = trial.phase_ms
	for action in ["water","hoe","harvest"]:
		review.select_clip("west",action)
		var clip: Dictionary = review.farming_library.get_clip(action,"west","A")
		s.check(action+"_actual_texture", review.motion_view.texture == clip.textures[0])
		s.check(action+"_same_direction_idle", review.reference_view.texture == trial.frames.A[trial.clips.idle.west[0]])
		s.check(action+"_pose_count", clip.textures.size() == counts[action])
		s.check(action+"_density_preserved", is_equal_approx(review.motion_view.scale.x,review.reference_view.scale.x/2.0))
		var reference_root: Vector2 = review.reference_view.position + Vector2(256,708)*review.reference_view.scale
		var motion_root: Vector2 = review.motion_view.position + clip.root_anchor_px*review.motion_view.scale
		s.check(action+"_registered_roots_aligned", reference_root.distance_to(motion_root) < 0.001)
		review.set_playing(true);review.advance_preview((float(clip.durations_ms[0])+1.0)/1000.0)
		s.check(action+"_original_timing", review.current_pose_index() == (1 % counts[action]))
		review.set_playing(false)
		var paused: float = review.preview_phase_ms
		review.advance_preview(1.0)
		s.check(action+"_pause", review.preview_phase_ms == paused)
		var previous_index: int = review.current_pose_index()
		review.step_frame()
		s.check(action+"_step", review.current_pose_index() == (previous_index+1) % counts[action])
		for i in range(counts[action]-1): review.step_frame()
		s.check(action+"_wraps_full_sequence", review.current_pose_index() == previous_index)
	trial.set_garment("B");review.refresh_preview()
	s.check("long_sleeve_not_faked", review.motion_view.texture == null and review.message.text.contains("短袖"))
	trial.set_garment("A");review.select_clip("north","water")
	s.check("missing_direction_not_faked", review.motion_view.texture == null and review.message.text.contains("西"))
	review.select_clip("west","walk")
	s.check("walk_geometry_restored", review.motion_view.texture != null and review.motion_view.scale == review.reference_view.scale and review.motion_view.position == review.reference_view.position)
	s.check("preview_did_not_change_world", trial.actor.position == world_before and trial.phase_ms == phase_before and trial.current_action == "idle" and trial.facing == "south")
	trial.queue_free();await process_frame
	print("FARMING_PANEL checks=",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
