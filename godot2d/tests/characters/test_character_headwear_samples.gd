extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
const TEMP="/private/tmp/coastal-headwear-fixture"
const IDS=["run-east","hoe-west","water-south","harvest-north"]
var s=Support.new()
var catalog:Dictionary
func save(path:String,value) -> void:
 var file=FileAccess.open(path,FileAccess.WRITE);file.store_string(JSON.stringify(value));file.close()
func _initialize() -> void:call_deferred("run")
func run() -> void:
 var path="res://dev/characters/character_headwear_samples.gd"
 s.check("headwear_loader_exists",FileAccess.file_exists(path))
 if not s.passed():quit(1);return
 var loader=load(path).new()
 DirAccess.make_dir_recursive_absolute(TEMP)
 catalog={"schema_version":1,"template_id":"adult-standard-v1","scope":"sampled-headwear-not-exhaustive","samples":[]}
 for id in IDS:
  var dir=TEMP.path_join(id);DirAccess.make_dir_recursive_absolute(dir)
  var img=Image.create(8,8,false,Image.FORMAT_RGBA8);img.fill(Color.WHITE);img.save_png(dir.path_join("frame.png"))
  var hash=FileAccess.get_sha256(dir.path_join("frame.png"))
  var states={}
  for state in ["bare","hair","hat","hair_hat"]:states[state]={"file":"frame.png","sha256":hash}
  var idle={"pose_id":"idle_"+id.split("-")[1]+"_0","canvas_px":[8,8],"root_anchor_px":[4,7],"display_scale":0.2,"file":"frame.png","sha256":hash}
  var parent={"canvas_px":[8,8],"root_anchor_px":[4,7],"display_scale":0.2,"frames":[],"idle":idle,"inputs":{"frame.png":hash}}
  var data={"schema_version":1,"template_id":"adult-standard-v1","action_id":id.split("-")[0],"direction":id.split("-")[1],"parent_sample":id+"/parent.json","canvas_px":[8,8],"root_anchor_px":[4,7],"display_scale":0.2,"frames":[],"idle":idle.duplicate(true),"inputs":{"frame.png":hash}}
  data.idle.states=states.duplicate(true)
  for i in range(4):
   var frame={"pose_id":data.action_id+"_"+data.direction+"_"+str(i),"duration_ms":100,"file":"frame.png","sha256":hash}
   parent.frames.append(frame);var headframe=frame.duplicate(true);headframe.states=states.duplicate(true);data.frames.append(headframe)
  save(dir.path_join("parent.json"),parent);data.parent_sha256=FileAccess.get_sha256(dir.path_join("parent.json"))
  save(dir.path_join("sample.json"),data)
  catalog.samples.append({"id":id,"sample":id+"/sample.json","sha256":FileAccess.get_sha256(dir.path_join("sample.json"))})
 save(TEMP.path_join("catalog.json"),catalog)
 s.check("four_sample_four_state_fixture",loader.load_samples(TEMP,TEMP.path_join("catalog.json")))
 s.check("all_clips_loaded",loader.samples.size()==4)
 var candidate=JSON.parse_string(FileAccess.get_file_as_string(TEMP.path_join("run-east/sample.json")))
 var original=candidate.duplicate(true);var original_catalog=catalog.duplicate(true)
 for defect in ["missing_state","unknown_state","duration","fractional_duration","pose","geometry","scale","idle_state","idle_geometry","texture_hash","outside_path","parent_hash","parent_path","duplicate_pose"]:
  candidate=original.duplicate(true)
  match defect:
   "missing_state":candidate.frames[0].states.erase("hat")
   "unknown_state":candidate.frames[0].states.extra=candidate.frames[0].states.bare
   "duration":candidate.frames[0].duration_ms=101
   "fractional_duration":candidate.frames[0].duration_ms=100.5
   "pose":candidate.frames[0].pose_id="other"
   "geometry":candidate.canvas_px=[7,8]
   "scale":candidate.display_scale=0
   "idle_state":candidate.idle.states.erase("hair")
   "idle_geometry":candidate.idle.root_anchor_px=[3,7]
   "texture_hash":candidate.frames[0].states.hat.sha256="bad"
   "outside_path":candidate.frames[0].states.hair.file="../frame.png"
   "parent_hash":candidate.parent_sha256="bad"
   "parent_path":candidate.parent_sample="../parent.json"
   "duplicate_pose":candidate.frames[1].pose_id=candidate.frames[0].pose_id
  save(TEMP.path_join("run-east/sample.json"),candidate)
  catalog=original_catalog.duplicate(true);catalog.samples[0].sha256=FileAccess.get_sha256(TEMP.path_join("run-east/sample.json"));save(TEMP.path_join("catalog.json"),catalog)
  s.check("reject_"+defect,not loader.load_samples(TEMP,TEMP.path_join("catalog.json")))
  s.check("atomic_"+defect,loader.samples.is_empty() and loader.catalog_sha256=="")
 save(TEMP.path_join("run-east/sample.json"),original)
 original_catalog.samples[0].sha256=FileAccess.get_sha256(TEMP.path_join("run-east/sample.json"))
 save(TEMP.path_join("catalog.json"),original_catalog)
 var reloaded=loader.load_samples(TEMP,TEMP.path_join("catalog.json"))
 s.check("reload_valid",reloaded)
 var changed=FileAccess.open(TEMP.path_join("run-east/frame.png"),FileAccess.WRITE);changed.store_string("changed");changed.close()
 s.check("dependency_tamper_rejected",not loader.load_samples(TEMP,TEMP.path_join("catalog.json")))
 s.check("dependency_tamper_clears",loader.samples.is_empty())
 print("HEADWEAR_LOADER checks=",s.checks.size()," passed=",s.passed());quit(0 if s.passed() else 1)
