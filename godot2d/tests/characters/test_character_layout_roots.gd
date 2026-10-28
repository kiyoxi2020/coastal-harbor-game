extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
var s:=Support.new()
const TEMP="/private/tmp/coastal-character-layout-root-fixture"
const IDS=["walk-west","run-east","hoe-west","water-south","harvest-north"]
func save(path:String,value) -> void:
 var f:=FileAccess.open(path,FileAccess.WRITE);f.store_string(JSON.stringify(value));f.close()
func _initialize() -> void:call_deferred("run")
func run() -> void:
 var path:="res://dev/characters/character_wardrobe_samples.gd"
 s.check("sample_loader_exists",FileAccess.file_exists(path))
 if not s.passed():quit(1);return
 var loader=load(path).new()
 DirAccess.make_dir_recursive_absolute(TEMP)
 var catalog:Dictionary={"schema_version":1,"scope":"sampled-not-exhaustive","samples":[]}
 for id in IDS:
  var dir:=TEMP.path_join("art/characters/reviews").path_join(id);DirAccess.make_dir_recursive_absolute(dir)
  var img:=Image.create(8,8,false,Image.FORMAT_RGBA8);img.fill(Color.WHITE);img.save_png(dir.path_join("frame.png"))
  var hash:=FileAccess.get_sha256(dir.path_join("frame.png"))
  var data:Dictionary={"schema_version":1,"template_id":"adult-standard-v1","action_id":id.split("-")[0],"direction":id.split("-")[1],"recipe":{"id":id,"slots":{"top":"test-top","pants":"test-pants","shoes":"test-shoes"}},"canvas_px":[8,8],"root_anchor_px":[4,7],"display_scale":0.2,"resource_root":"art/characters","inputs":{"reviews/"+id+"/frame.png":hash},"frames":[]}
  for i in range(4):data.frames.append({"pose_id":id+str(i),"duration_ms":100,"file":"reviews/"+id+"/frame.png","sha256":hash})
  data.idle={"file":"reviews/"+id+"/frame.png","sha256":hash,"canvas_px":[8,8],"root_anchor_px":[4,7],"display_scale":0.2,"pose_id":"idle_"+id.split("-")[1]+"_0"}
  save(dir.path_join("sample.json"),data)
  catalog.samples.append({"id":id,"sample":"art/characters/reviews/"+id+"/sample.json","sha256":FileAccess.get_sha256(dir.path_join("sample.json"))})
 save(TEMP.path_join("catalog.json"),catalog)
 s.check("rooted_sample_fixture_load",loader.load_samples(TEMP,TEMP.path_join("catalog.json")))
 s.check("five_sample_clips",loader.samples.size()==5)
 var sample_path:=TEMP.path_join("art/characters/reviews/walk-west/sample.json")
 var original:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(sample_path))
 var original_catalog:Dictionary=catalog.duplicate(true)
 var Paths=load("res://dev/characters/character_resource_paths.gd")
 for invalid_root in ["art/design", "/art/characters", "../art/characters", "art/characters/..", "art\\characters", "", null]:
  var damaged:Dictionary=original.duplicate(true);damaged.resource_root=invalid_root
  save(sample_path,damaged);catalog=original_catalog.duplicate(true)
  catalog.samples[0].sha256=FileAccess.get_sha256(sample_path);save(TEMP.path_join("catalog.json"),catalog)
  s.check("sample_root_reject_"+str(invalid_root),not loader.load_samples(TEMP,TEMP.path_join("catalog.json")) and loader.samples.is_empty())
  s.check("shared_root_reject_"+str(invalid_root),Paths.base(TEMP,sample_path,damaged)=="")
  catalog=original_catalog.duplicate(true);catalog.resource_root=invalid_root
  save(TEMP.path_join("catalog.json"),catalog)
  s.check("catalog_root_reject_"+str(invalid_root),not loader.load_samples(TEMP,TEMP.path_join("catalog.json")))
 for invalid_path in ["../frame.png", "/private/tmp/frame.png", "C:/frame.png", "x\\frame.png", "./frame.png", "x//frame.png"]:
  var damaged:Dictionary=original.duplicate(true);damaged.inputs={invalid_path:"0".repeat(64)}
  save(sample_path,damaged);catalog=original_catalog.duplicate(true)
  catalog.samples[0].sha256=FileAccess.get_sha256(sample_path);save(TEMP.path_join("catalog.json"),catalog)
  s.check("rooted_input_reject_"+invalid_path,not loader.load_samples(TEMP,TEMP.path_join("catalog.json")))
 save(sample_path,original);catalog=original_catalog.duplicate(true);catalog.samples[0].sha256=FileAccess.get_sha256(sample_path);save(TEMP.path_join("catalog.json"),catalog)
 s.check("rooted_reload_recovers",loader.load_samples(TEMP,TEMP.path_join("catalog.json")))
 var changed:=FileAccess.open(TEMP.path_join("art/characters/reviews/walk-west/frame.png"),FileAccess.WRITE)
 changed.store_string("tampered");changed.close()
 s.check("rooted_actual_hash_still_checked",not loader.load_samples(TEMP,TEMP.path_join("catalog.json")) and loader.samples.is_empty())
 print("CHARACTER_LAYOUT_ROOTS checks=",s.checks.size()," passed=",s.passed());quit(0 if s.passed() else 1)
