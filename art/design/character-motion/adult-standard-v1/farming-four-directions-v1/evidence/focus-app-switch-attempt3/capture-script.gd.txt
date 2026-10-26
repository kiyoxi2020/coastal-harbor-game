extends "res://tests/test_character_farming_24_native.gd"
func run() -> void:
	if not evidence.begins_with("/private/tmp/coastal-" ):quit(2);return
	DirAccess.make_dir_recursive_absolute(evidence)
	var contract:=evidence.path_join("input-contract.json")
	if not FileAccess.file_exists(contract):printerr("pre-capture contract missing");quit(2);return
	input_contract_sha256=FileAccess.get_sha256(contract);started_utc=Time.get_datetime_string_from_system(true)
	trial=load("res://dev/character_walk_trial.tscn").instantiate()
	var project:=ProjectSettings.globalize_path("res://..")
	trial.art_root=project.path_join("art/design/character-motion/adult-standard-v1/locomotion-v1")
	trial.run_candidate_root=project.path_join("art/design/character-motion/adult-standard-v1/run-four-directions-v1")
	trial.run_diagnostics_enabled=true;trial.farming_review_enabled=true;trial.farming_transitions_enabled=true
	trial.farming_catalog_path=project.path_join("art/design/character-motion/adult-standard-v1/farming-four-directions-v1/catalog.json")
	root.add_child(trial);review=trial.review_panel;await focus()
	check("native_renderer",DisplayServer.get_name()!="headless")
	await key(KEY_A,true);await physics_frame;await physics_frame;await key(KEY_A,false);await key(KEY_1,true);await key(KEY_1,false)
	await snapshot("before-native-focus-transfer")
	await key(KEY_G,true);await key(KEY_G,false)
	check("tool_started_west_A",trial.current_action=="hoe" and trial.facing=="west" and trial.garment=="A")
	var output:Array=[]
	var activate_other:="ObjC.import('AppKit'); $.NSRunningApplication.runningApplicationsWithBundleIdentifier('com.apple.finder').firstObject.activateWithOptions(3);"
	var exit_code:=OS.execute("/usr/bin/osascript",PackedStringArray(["-l","JavaScript","-e",activate_other]),output,true)
	check("external_app_activation_succeeded",exit_code==0)
	var deadline:=Time.get_ticks_msec()+1500
	while (trial.focused or root.has_focus()) and Time.get_ticks_msec()<deadline:await process_frame
	var focus_out_observed:bool=not trial.focused and not root.has_focus()
	check("real_external_app_focus_out",focus_out_observed)
	var before:float=trial.farming_elapsed_ms
	var position:Vector2=trial.actor.position
	await create_timer(0.3).timeout
	var after:float=trial.farming_elapsed_ms
	check("native_focus_freezes_world_tool_clock",not trial.focused and is_equal_approx(before,after) and not trial.farming_clip.is_empty())
	check("native_focus_keeps_position",trial.actor.position==position)
	var activate_self:="ObjC.import('AppKit'); $.NSRunningApplication.runningApplicationWithProcessIdentifier(%d).activateWithOptions(3);"%OS.get_process_id()
	exit_code=OS.execute("/usr/bin/osascript",PackedStringArray(["-l","JavaScript","-e",activate_self]),output,true)
	check("native_app_reactivation_succeeded",exit_code==0)
	deadline=Time.get_ticks_msec()+1500
	while (not trial.focused or not root.has_focus()) and Time.get_ticks_msec()<deadline:await process_frame
	check("native_window_focus_restored",trial.focused and root.has_focus())
	await create_timer(0.1).timeout
	check("native_tool_clock_resumes",trial.farming_elapsed_ms>after or trial.farming_clip.is_empty())
	await create_timer(1.0).timeout
	check("native_tool_finishes_idle",trial.current_action=="idle" and trial.farming_clip.is_empty())
	await snapshot("after-restore-and-idle")
	var report:Dictionary={"scope":"Supplement only: real external Finder activation/WM focus-out and exact Godot PID reactivation/WM focus-in freezes one west-A hoe world clock/position, restoring focus resumes and finishes idle. Not a new24-group animation capture.","input_contract_sha256":input_contract_sha256,"started_utc":started_utc,"finished_utc":Time.get_datetime_string_from_system(true),"wm_focus_out_observed":focus_out_observed,"wm_focus_in_observed":trial.focused and root.has_focus(),"paused_elapsed_before_ms":before,"paused_elapsed_after_ms":after,"pause_wall_seconds":0.3,"checks":s.checks}
	save_json(evidence.path_join("report.json"),report)
	print("FARMING_FOCUS_NATIVE checks=",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
