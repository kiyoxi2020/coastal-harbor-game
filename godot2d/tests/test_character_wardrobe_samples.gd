extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
var s:=Support.new()
const TEMP="/private/tmp/coastal-wardrobe-sample-fixture"
const IDS=["walk-west","run-east","hoe-west","water-south","harvest-north"]
func save(path:String,value) -> void:
 var f:=FileAccess.open(path,FileAccess.WRITE);f.store_string(JSON.stringify(value));f.close()
func _initialize() -> void:call_deferred("run")
func run() -> void:
 var path:="res://dev/character_wardrobe_samples.gd"
 s.check("sample_loader_exists",FileAccess.file_exists(path))
 if not s.passed():quit(1);return
 var loader=load(path).new()
 DirAccess.make_dir_recursive_absolute(TEMP)
 var catalog:Dictionary={"schema_version":1,"scope":"sampled-not-exhaustive","samples":[]}
 for id in IDS:
  var dir:=TEMP.path_join(id);DirAccess.make_dir_recursive_absolute(dir)
  var img:=Image.create(8,8,false,Image.FORMAT_RGBA8);img.fill(Color.WHITE);img.save_png(dir.path_join("frame.png"))
  var hash:=FileAccess.get_sha256(dir.path_join("frame.png"))
  var data:Dictionary={"schema_version":1,"template_id":"adult-standard-v1","action_id":id.split("-")[0],"direction":id.split("-")[1],"recipe":{"id":id,"slots":{"top":"test-top","pants":"test-pants","shoes":"test-shoes"}},"canvas_px":[8,8],"root_anchor_px":[4,7],"display_scale":0.2,"inputs":{"frame.png":hash},"frames":[]}
  for i in range(4):data.frames.append({"pose_id":id+str(i),"duration_ms":100,"file":"frame.png","sha256":hash})
  data.idle={"file":"frame.png","sha256":hash,"canvas_px":[8,8],"root_anchor_px":[4,7],"display_scale":0.2,"pose_id":"idle_"+id.split("-")[1]+"_0"}
  save(dir.path_join("sample.json"),data)
  catalog.samples.append({"id":id,"sample":id+"/sample.json","sha256":FileAccess.get_sha256(dir.path_join("sample.json"))})
 save(TEMP.path_join("catalog.json"),catalog)
 s.check("five_sample_fixture_load",loader.load_samples(TEMP,TEMP.path_join("catalog.json")))
 s.check("five_sample_clips",loader.samples.size()==5)
 var original:Dictionary=catalog.duplicate(true)
 var candidate_path:=TEMP.path_join("walk-west/sample.json")
 var candidate:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(candidate_path))
 var saved:Dictionary=candidate.duplicate(true)
 for defect in ["idle","recipe","duration","pose","canvas","idle_scale","idle_root"]:
  candidate=saved.duplicate(true)
  match defect:
   "idle":candidate.erase("idle")
   "recipe":candidate.recipe.slots.erase("pants")
   "duration":candidate.frames[0].duration_ms=0
   "pose":candidate.frames[1].pose_id=candidate.frames[0].pose_id
   "canvas":candidate.canvas_px=[8,"bad"]
   "idle_scale":candidate.idle.display_scale=0
   "idle_root":candidate.idle.root_anchor_px=[-1,7]
  save(candidate_path,candidate)
  catalog=original.duplicate(true);catalog.samples[0].sha256=FileAccess.get_sha256(candidate_path)
  save(TEMP.path_join("catalog.json"),catalog)
  s.check("reject_invalid_"+defect,not loader.load_samples(TEMP,TEMP.path_join("catalog.json")))
 save(candidate_path,saved);catalog=original.duplicate(true)
 catalog.samples.pop_back();save(TEMP.path_join("catalog.json"),catalog)
 s.check("missing_action_rejected",not loader.load_samples(TEMP,TEMP.path_join("catalog.json")))
 s.check("failure_clears_all",loader.samples.is_empty())
 catalog=original.duplicate(true);catalog.samples[0].sample="../outside.json";save(TEMP.path_join("catalog.json"),catalog)
 s.check("outside_path_rejected",not loader.load_samples(TEMP,TEMP.path_join("catalog.json")))
 catalog=original.duplicate(true);catalog.samples[0].sha256="bad";save(TEMP.path_join("catalog.json"),catalog)
 s.check("candidate_hash_rejected",not loader.load_samples(TEMP,TEMP.path_join("catalog.json")))
 save(TEMP.path_join("catalog.json"),original)
 var changed:=FileAccess.open(TEMP.path_join("walk-west/frame.png"),FileAccess.WRITE);changed.store_string("changed");changed.close()
 s.check("source_hash_rejected",not loader.load_samples(TEMP,TEMP.path_join("catalog.json")))
 s.check("tamper_clears_all",loader.samples.is_empty())
 print("WARDROBE_SAMPLES checks=",s.checks.size()," passed=",s.passed());quit(0 if s.passed() else 1)
