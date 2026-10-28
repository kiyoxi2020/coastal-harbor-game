extends "res://tests/test_character_headwear_native.gd"
## Bounded rerun of the changed west-hoe clip; other samples only load unchanged.
func run() -> void:
 if not evidence.begins_with("/private/tmp/coastal-"):quit(2);return
 DirAccess.make_dir_recursive_absolute(evidence.path_join("boards"))
 DirAccess.make_dir_recursive_absolute(evidence.path_join("sequence"))
 var contract:=evidence.path_join("input-contract.json")
 if not FileAccess.file_exists(contract):printerr("pre-capture contract required");quit(2);return
 input_contract_sha256=FileAccess.get_sha256(contract)
 started_utc=Time.get_datetime_string_from_system(true)
 trial=load("res://dev/character_headwear_hoe_review.tscn").instantiate()
 trial.head_catalog_override=ProjectSettings.globalize_path("res://..").path_join("art/design/character-motion/adult-standard-v1/headwear-sampling-v1/revisions/hoe-west-hat-v2/catalog.json")
 root.add_child(trial);review=trial.review_panel
 await focus()
 check("real_gpu",DisplayServer.get_name()!="headless")
 check("four_head_samples_loaded",trial.head_ready and trial.head_error=="" and trial.head_library.samples.size()==4)
 if not s.passed():finish();return
 check("sample_controls_fit",fits(trial.get_node("TrialUI/Samples")))
 check("head_controls_fit",fits(trial.get_node("TrialUI/Headwear")))
 check("motion_panel_fits",fits(review))
 await snapshot("overview")
 output_files["overview.png"]=FileAccess.get_sha256(evidence.path_join("overview.png"))
 for sample in trial.head_library.samples:
  if sample.id=="hoe-west":
   for state in trial.HeadLibrary.STATES:await inspect_head(sample,state)
 finish()

func finish() -> void:
 var clips:Dictionary={}
 if is_instance_valid(trial):
  for sample in trial.head_library.samples:
   if sample.id=="hoe-west":clips[sample.id]={"sample_sha256":sample.sample_sha256,"pose_ids":sample.pose_ids,"durations_ms":sample.durations_ms,"states":trial.HeadLibrary.STATES}
 var report:Dictionary={"scope":"Changed west-hoe sample only: five poses, four head states; native GPU dark/light stopped frames, ten panel cycles per state, world hoe one-shot, live state switching and matching idle. Other samples load but are not newly visually tested. Signals/handlers/logical Input; no OS input or WM focus claim.","input_contract_sha256":input_contract_sha256,"started_utc":started_utc,"finished_utc":Time.get_datetime_string_from_system(true),"catalog_sha256":trial.head_library.catalog_sha256 if is_instance_valid(trial) else "","clips":clips,"checks":s.checks,"samples":samples,"captures":captures,"output_hashes":output_files}
 save_json(evidence.path_join("report.json"),report)
 print("HOE_HEADWEAR_NATIVE checks=",s.checks.size()," passed=",s.passed()," samples=",samples.size()," captures=",captures.size())
 quit(0 if s.passed() else 1)
