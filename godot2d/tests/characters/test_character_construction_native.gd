extends "res://tests/characters/test_character_headwear_native.gd"
## One strict construction sample. Reuses the existing GPU/ten-cycle/world
## inspection path without broadening old frozen headwear evidence.
func construction_suite() -> String:
 var result=ProjectSettings.globalize_path("res://..").simplify_path().path_join("art/characters/reviews/headwear-construction/review.json")
 for argument in OS.get_cmdline_user_args():
  if argument.begins_with("--construction-suite="):result=argument.trim_prefix("--construction-suite=")
 return result
func fresh_evidence() -> bool:
 if not evidence.begins_with("/private/tmp/coastal-") or "\\" in evidence or ":" in evidence:return false
 for part in evidence.split("/").slice(1):
  if part in ["",".",".."]:return false
 var guard=load("res://dev/characters/character_construction_samples.gd").new()
 if not guard.no_links(evidence):return false
 var directory=DirAccess.open(evidence)
 if directory==null:return false
 directory.include_hidden=true
 if not directory.get_directories().is_empty() or directory.get_files()!=PackedStringArray(["input-contract.json"]):return false
 return guard.no_links(evidence.path_join("input-contract.json"))
func run() -> void:
 if not fresh_evidence():printerr("fresh, unlinked evidence directory containing only input-contract.json required");quit(2);return
 DirAccess.make_dir_recursive_absolute(evidence.path_join("boards"))
 DirAccess.make_dir_recursive_absolute(evidence.path_join("sequence"))
 var contract=evidence.path_join("input-contract.json")
 if not FileAccess.file_exists(contract) or not JSON.parse_string(FileAccess.get_file_as_string(contract)) is Dictionary:printerr("pre-capture input contract required");quit(2);return
 input_contract_sha256=FileAccess.get_sha256(contract);started_utc=Time.get_datetime_string_from_system(true)
 trial=load("res://dev/characters/character_headwear_hoe_review.tscn").instantiate()
 trial.head_catalog_override=construction_suite()
 root.add_child(trial);review=trial.review_panel
 await focus()
 check("real_gpu",DisplayServer.get_name()!="headless")
 check("one_strict_head_sample",trial.head_ready and trial.head_error=="" and trial.head_library.samples.size()==1 and trial.head_library.suite_kind=="coastal-character-construction-review-v1" and trial.head_library.manifest_bindings.size()==4)
 if not s.passed():finish();return
 check("west_hoe_default",trial.selected_sample=="hoe-west" and trial.head_state=="hair_hat")
 for button in trial.get_node("TrialUI/Samples/Margin/Rows/Buttons").get_children():
  check("bounded_button_"+button.name,button.visible==(button.name=="hoe-west") and (button.name=="hoe-west" or button.disabled))
 check("sample_controls_fit",fits(trial.get_node("TrialUI/Samples")))
 check("head_controls_fit",fits(trial.get_node("TrialUI/Headwear")))
 check("motion_panel_fits",fits(review))
 await snapshot("overview")
 output_files["overview.png"]=FileAccess.get_sha256(evidence.path_join("overview.png"))
 for sample in trial.head_library.samples:
  for state in trial.HeadLibrary.STATES:await inspect_head(sample,state)
 finish()
func png_inventory(directory:String,prefix:String="") -> void:
 var dir=DirAccess.open(directory)
 if dir==null:return
 for name in dir.get_files():
  if name.ends_with(".png"):output_files[prefix+name]=FileAccess.get_sha256(directory.path_join(name))
 for name in dir.get_directories():
  if not dir.is_link(name):png_inventory(directory.path_join(name),prefix+name+"/")
func finish() -> void:
 # Preserve the exact binary64 values sampled before JSON decimal formatting.
 for row in samples:
  row.phase_f64le=PackedFloat64Array([float(row.phase_ms)]).to_byte_array().hex_encode()
  row.unwrapped_f64le=PackedFloat64Array([float(row.unwrapped_ms)]).to_byte_array().hex_encode()
 png_inventory(evidence)
 var clips:Dictionary={};var manifests:Dictionary={};var suite_sha="";var kind=""
 if is_instance_valid(trial):
  suite_sha=trial.head_library.catalog_sha256;kind=trial.head_library.suite_kind;manifests=trial.head_library.manifest_bindings
  for sample in trial.head_library.samples:clips[sample.id]={"sample_sha256":sample.sample_sha256,"pose_ids":sample.pose_ids,"durations_ms":sample.durations_ms,"states":trial.HeadLibrary.STATES}
 var manifest_sha256:Dictionary={}
 for state in manifests:manifest_sha256[state]=manifests[state].sha256
 var report={"scope":"One review-only strict construction west-hoe sample: four head states, four action poses plus matching idle; native dark/light stopped frames, ten panel cycles per state, four world poses, live head-state switches without clock reset. Fixture signals/logical input; no OS keyboard/mouse, WM focus, user approval, production release or export claim.","input_contract_sha256":input_contract_sha256,"started_utc":started_utc,"finished_utc":Time.get_datetime_string_from_system(true),"catalog_sha256":suite_sha,"suite_sha256":suite_sha,"suite_kind":kind,"manifests":manifests,"manifest_sha256":manifest_sha256,"renderer":{"display_server":DisplayServer.get_name(),"rendering_method":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name()},"clips":clips,"checks":s.checks,"samples":samples,"captures":captures,"output_hashes":output_files}
 save_json(evidence.path_join("report.json"),report)
 print("CONSTRUCTION_NATIVE checks=",s.checks.size()," passed=",s.passed()," samples=",samples.size()," captures=",captures.size())
 quit(0 if s.passed() else 1)
