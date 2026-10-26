extends "res://tests/test_character_farming_24_native.gd"
func run() -> void:
	if not evidence.begins_with("/private/tmp/coastal-"):quit(2);return
	DirAccess.make_dir_recursive_absolute(evidence.path_join("sequence"));DirAccess.make_dir_recursive_absolute(evidence.path_join("boards"))
	var contract:=evidence.path_join("input-contract.json")
	if not FileAccess.file_exists(contract):printerr("pre-capture input contract required");quit(2);return
	input_contract_sha256=FileAccess.get_sha256(contract);started_utc=Time.get_datetime_string_from_system(true)
	var project:=ProjectSettings.globalize_path("res://..")
	var catalog_root:=project.path_join("art/design/character-motion/adult-standard-v1/farming-four-directions-v1")
	trial=load("res://dev/character_walk_trial.tscn").instantiate()
	trial.art_root=catalog_root.path_join("../locomotion-v1");trial.run_candidate_root=catalog_root.path_join("../run-four-directions-v1")
	trial.run_diagnostics_enabled=true;trial.farming_review_enabled=true;trial.farming_transitions_enabled=true;trial.review_enabled=true;trial.farming_review_action="hoe"
	trial.farming_catalog_path=catalog_root.path_join("catalog-color-v2.json")
	root.add_child(trial);review=trial.review_panel;await focus()
	check("native_renderer",DisplayServer.get_name()!="headless");check("all_24_catalog_clips_load",review.farming_library.clips.size()==24)
	check("panel_fits",fits(review));check("top_controls_fit",fits(trial.get_node("TrialUI/Panel")))
	var before:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(catalog_root.path_join("catalog-before-color-v2.json")))
	var after:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(trial.farming_catalog_path))
	var unchanged:=0
	for i in range(before.clips.size()):
		var record:Dictionary=before.clips[i]
		if not (record.action_id=="hoe" and record.garment=="B"):
			if record==after.clips[i]:unchanged+=1
	check("accepted_20_records_exactly_unchanged",unchanged==20)
	if not s.passed():finish();return
	for direction in ["south","west","east","north"]:
		trial.set_garment("B");review.select_clip(direction,"hoe");check(direction+"_corrected_full_canvas_fits",canvas_fits())
		await inspect_clip("hoe",direction,"B")
		# Comparison fixture selects the accepted watering reference directly;
		# actual UI selection is exercised by inspect_clip for all four changed clips.
		review.set_playing(false);review.select_clip(direction,"water")
		check(direction+"_accepted_water_reference",review.review_action=="water" and review.motion_view.texture==review.farming_library.get_clip("water",direction,"B").textures[0])
		await snapshot("accepted-water-"+direction+"-B")
	finish()
func finish() -> void:
	var clips:Dictionary={}
	if is_instance_valid(review) and review.farming_library!=null:
		for direction in ["south","west","east","north"]:
			var clip:Dictionary=review.farming_library.get_clip("hoe",direction,"B")
			if not clip.is_empty():clips[direction]={"candidate_sha256":clip.candidate_sha256,"pose_ids":clip.pose_ids,"durations_ms":clip.durations_ms,"canvas_px":[clip.canvas_px.x,clip.canvas_px.y],"root_anchor_px":[clip.root_anchor_px.x,clip.root_anchor_px.y]}
	var report:Dictionary={"scope":"Color-only hoe-B revision:4directions/16poses,deterministic fixture via actual control signals and trial handlers,not OS keyboard/mouse automation;each10panelcycles+1worldone-shot.20other catalog records preserved and accepted-water native reference snapshots. Original346native remains historical for original24; this report does not grant new user palette approval.","input_contract_sha256":input_contract_sha256,"started_utc":started_utc,"finished_utc":Time.get_datetime_string_from_system(true),"clips":clips,"checks":s.checks,"samples":samples,"captures":captures,"catalog_sha256":review.farming_library.catalog_sha256 if is_instance_valid(review) and review.farming_library!=null else ""}
	save_json(evidence.path_join("report.json"),report);save_json(evidence.path_join("checks.json"),s.checks)
	print("HOE_COLOR_NATIVE checks=",s.checks.size()," passed=",s.passed()," samples=",samples.size()," captures=",captures.size())
	quit(0 if s.passed() else 1)

# Native render fixture: OS injection proved unreliable in two preserved probes.
# Invoke real UI signals/handlers deterministically; no claim of physical input/focus validation.
func check(id:String,ok:bool) -> void:
	s.check(id.replace("_world_direction_key","_fixture_direction").replace("_world_action_key","_fixture_action").replace("_native_selection","_fixture_selection"),ok)
func focus() -> void:
	if is_instance_valid(trial):trial.focused=true
	await process_frame
	if is_instance_valid(trial):trial.focused=true
func click(button:Button) -> void:
	if button.toggle_mode:button.button_pressed=not button.button_pressed
	button.pressed.emit()
	await process_frame
func key(code:int,pressed:bool) -> void:
	if not pressed:return
	trial.focused=true
	var directions:Dictionary={KEY_S:"south",KEY_A:"west",KEY_D:"east",KEY_W:"north"}
	if directions.has(code):
		trial.facing=directions[code];trial.refresh_pose()
	else:
		var event:=InputEventKey.new();event.physical_keycode=code;event.pressed=true
		trial._unhandled_key_input(event)
	await process_frame
