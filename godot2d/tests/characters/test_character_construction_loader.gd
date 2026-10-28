extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
const Library=preload("res://dev/characters/character_headwear_samples.gd")
const STATES=["bare","hair","hat","hair_hat"]
var s=Support.new()
var project:="/private/tmp/coastal-construction-loader-"+str(OS.get_process_id())
var library:String
var suite:Dictionary
var base:Dictionary
var recipes:Dictionary
var manifests:Dictionary
var loader=Library.new()
func _initialize() -> void:call_deferred("run")
func save(path:String,value:Variant) -> void:
 DirAccess.make_dir_recursive_absolute(path.get_base_dir())
 var f=FileAccess.open(path,FileAccess.WRITE);f.store_string(JSON.stringify(value));f.close()
func hash_bytes(bytes:PackedByteArray) -> String:
 var h=HashingContext.new();h.start(HashingContext.HASH_SHA256);h.update(bytes);return h.finish().hex_encode()
func reference(path:String) -> Dictionary:
 return {"file":path,"sha256":FileAccess.get_sha256(library.path_join(path))}
func reset_fixture() -> void:
 library=project.path_join("art/characters")
 save(project.path_join("tools/characters/build.py"),{"synthetic":"builder"})
 save(project.path_join("tools/characters/build_contract.py"),{"synthetic":"contract"})
 save(project.path_join("tools/characters/composition_contract.py"),{"synthetic":"composition"})
 save(library.path_join("sources/source.json"),{"synthetic":"source"})
 var source=reference("sources/source.json")
 for name in ["templates/adult-standard-v1/template.json","templates/adult-standard-v1/motions/review-motion-v1/motion-set.json","parts/top03/design.json","parts/original-pants/design.json","parts/original-shoes/design.json","parts/hair-chestnut-short-v1/design.json","parts/hat-straw-navy-band-v1/design.json"]:save(library.path_join(name),{"synthetic":"registered-reference"})
 base={"kind":"coastal-character-construction-v1","schema_version":1,"resource_root":"art/characters","character_model_id":"unified-composable-character-v1","recipe_id":"base","revision":"r001","template":reference("templates/adult-standard-v1/template.json"),"motion_set":reference("templates/adult-standard-v1/motions/review-motion-v1/motion-set.json"),"slots":{"body":null,"top":reference("parts/top03/design.json"),"pants":reference("parts/original-pants/design.json"),"shoes":reference("parts/original-shoes/design.json")},"required_capabilities":[{"action_id":"hoe","direction":"west"},{"action_id":"idle","direction":"west"}],"clips":[],"authoring_inputs":[source]}
 for action in ["hoe","idle"]:
  var frames:Array=[]
  for i in range(4 if action=="hoe" else 1):frames.append({"pose_id":"hoe_west_key_"+str(i) if action=="hoe" else "idle_west_0","duration_ms":100,"layers":[],"layer_order":[],"registration":{},"composition":"alpha-over"})
  base.clips.append({"action_id":action,"direction":"west","canvas_px":[8,8],"root_anchor_px":[4,7],"display_scale":0.25,"action":source,"poses":source,"variant":"B","frames":frames})
 for clip in base.clips:
  var prefix="templates/adult-standard-v1/motions/review-motion-v1/actions/"+clip.action_id+"/r001/"
  var poses_path=prefix+"west/poses.json"
  save(library.path_join(prefix+"action.json"),{"action_id":clip.action_id,"directions":{"west":poses_path}})
  save(library.path_join(poses_path),{"template_id":"adult-standard-v1","action_id":clip.action_id,"direction":"west","variants":{"B":{"canvas_px":clip.canvas_px,"root_anchor_px":clip.root_anchor_px,"display_scale":clip.display_scale,"frames":clip.frames.duplicate(true)}}})
  clip.action=reference(prefix+"action.json");clip.poses=reference(poses_path)
 recipes={};manifests={}
 suite={"kind":"coastal-character-construction-review-v1","schema_version":1,"resource_root":"art/characters","scope":"review-only","sample_id":"hoe-west","states":{}}
 for state in STATES:
  recipes[state]={"kind":"coastal-character-construction-v1","schema_version":2,"resource_root":"art/characters","character_model_id":"unified-composable-character-v1","recipe_id":"head-"+state,"revision":"r001","base_recipe":{},"head_state":state,"slots":{},"clips":base.clips.duplicate(true),"authoring_inputs":[]}
  if state in ["hair","hair_hat"]:recipes[state].slots.hair=reference("parts/hair-chestnut-short-v1/design.json")
  if state in ["hat","hair_hat"]:recipes[state].slots.hat=reference("parts/hat-straw-navy-band-v1/design.json")
  recipes[state].clips=[]
  for clip in base.clips:
   var head_frames:Array=[]
   for frame in clip.frames:
    var order=["base"] if state=="bare" else ["base","hair"] if state=="hair" else ["far_hat","base","near_hat"] if state=="hat" else ["far_hat","base","under_hat_hair","near_hat"]
    var layers:Array=[]
    for id in order:
     if id=="base":continue
     layers.append({"id":id,"slot":"hat" if id in ["far_hat","near_hat"] else "hair","texture":source,"registration":{},"provenance":{}})
    head_frames.append({"pose_id":frame.pose_id,"operation":"none" if state=="bare" else "binary-rgba-replace" if state=="hair" else "supported-alpha-stack","layers":layers,"layer_order":order})
   recipes[state].clips.append({"action_id":clip.action_id,"direction":clip.direction,"frames":head_frames})
  var outputs:Array=[]
  for clip in base.clips:
   for frame in clip.frames:
    var name="frames/"+clip.action_id+"/west/"+frame.pose_id+".png"
    var path=library.path_join("builds/head-"+state).path_join(name)
    DirAccess.make_dir_recursive_absolute(path.get_base_dir())
    var picture=Image.create(8,8,false,Image.FORMAT_RGBA8);picture.fill(Color("e8c5a4"));picture.save_png(path)
    outputs.append({"file":name,"sha256":FileAccess.get_sha256(path),"rgba_sha256":hash_bytes(picture.get_data()),"size":[8,8]})
  manifests[state]={"kind":"coastal-character-review-build-v1","schema_version":1,"status":"review-only","release_eligible":false,"recipe":"recipes/head-"+state+"/r001.json","artifact_digest":"","inputs":{},"engine":{"pillow":"fixture","code":{"build.py":FileAccess.get_sha256(project.path_join("tools/characters/build.py")),"build_contract.py":FileAccess.get_sha256(project.path_join("tools/characters/build_contract.py")),"composition_contract.py":FileAccess.get_sha256(project.path_join("tools/characters/composition_contract.py"))}},"outputs":outputs}
 publish()
func publish() -> void:
 save(library.path_join("recipes/base/r001.json"),base)
 for state in STATES:
  recipes[state].base_recipe=reference("recipes/base/r001.json")
  save(library.path_join(manifests[state].recipe),recipes[state])
  manifests[state].inputs={"recipes/base/r001.json":FileAccess.get_sha256(library.path_join("recipes/base/r001.json")),"sources/source.json":FileAccess.get_sha256(library.path_join("sources/source.json"))}
  for name in ["templates/adult-standard-v1/template.json","templates/adult-standard-v1/motions/review-motion-v1/motion-set.json","parts/top03/design.json","parts/original-pants/design.json","parts/original-shoes/design.json","parts/hair-chestnut-short-v1/design.json","parts/hat-straw-navy-band-v1/design.json"]:manifests[state].inputs[name]=FileAccess.get_sha256(library.path_join(name))
  for clip in base.clips:
   for dependency in [clip.action,clip.poses]:manifests[state].inputs[dependency.file]=dependency.sha256
  manifests[state].inputs[manifests[state].recipe]=FileAccess.get_sha256(library.path_join(manifests[state].recipe))
 publish_manifests()
func publish_manifests() -> void:
 for state in STATES:
  manifests[state].artifact_digest=hash_bytes(JSON.stringify({"inputs":manifests[state].inputs,"engine":manifests[state].engine},"",true).to_utf8_buffer())
  var path=library.path_join("builds/head-"+state+"/manifest.json");save(path,manifests[state])
  suite.states[state]={"manifest":"art/characters/builds/head-"+state+"/manifest.json","sha256":FileAccess.get_sha256(path)}
 save(library.path_join("reviews/headwear-construction/review.json"),suite)
func load_fixture() -> bool:
 return loader.load_samples(project,library.path_join("reviews/headwear-construction/review.json"))
func native_exit(evidence:String) -> int:
 var output:Array=[]
 return OS.execute(OS.get_executable_path(),PackedStringArray(["--headless","--path",ProjectSettings.globalize_path("res://"),"--log-file",evidence.replace("/", "-").insert(0,"/private/tmp/coastal-")+".log","--script","res://tests/characters/test_character_construction_native.gd","--","--evidence="+evidence]),output,true)
func native_preservation_checks() -> void:
 var evidence=project+"-used-evidence"
 DirAccess.make_dir_recursive_absolute(evidence)
 save(evidence.path_join("input-contract.json"),{"fixture":"preservation"})
 var marker=evidence.path_join("report.json")
 save(marker,{"frozen":"do not overwrite"})
 var before=FileAccess.get_sha256(marker)
 s.check("native_existing_evidence_exit2",native_exit(evidence)==2)
 s.check("native_existing_report_preserved",FileAccess.get_sha256(marker)==before)
 s.check("native_existing_evidence_no_new_directories",DirAccess.get_directories_at(evidence).is_empty())
 for kind in ["hidden_file","receipt","empty_directory","root_link","parent_link","input_link"]:
  var target=project+"-native-"+kind
  DirAccess.make_dir_recursive_absolute(target)
  save(target.path_join("input-contract.json"),{"fixture":kind})
  var entry=target
  if kind=="hidden_file":save(target.path_join(".receipt.json"),{"frozen":"hidden"})
  elif kind=="receipt":save(target.path_join("receipt.json"),{"frozen":"receipt"})
  elif kind=="empty_directory":DirAccess.make_dir_recursive_absolute(target.path_join("boards"))
  elif kind in ["root_link","parent_link"]:
   var link=target+"-link"
   s.check(kind+"_created",OS.execute("/bin/ln",PackedStringArray(["-s",target,link]))==0)
   entry=link
   if kind=="parent_link":
    DirAccess.make_dir_recursive_absolute(target.path_join("run"));save(target.path_join("run/input-contract.json"),{"fixture":kind});entry=link.path_join("run")
  elif kind=="input_link":
   var contract=target.path_join("input-contract.json");DirAccess.rename_absolute(contract,target+"-contract.json")
   s.check(kind+"_created",OS.execute("/bin/ln",PackedStringArray(["-s",target+"-contract.json",contract]))==0)
  var files=DirAccess.get_files_at(target);var directories=DirAccess.get_directories_at(target)
  s.check("native_reject_"+kind,native_exit(entry)==2)
  s.check("native_preserve_"+kind,DirAccess.get_files_at(target)==files and DirAccess.get_directories_at(target)==directories)
func run() -> void:
 reset_fixture()
 s.check("strict_construction_four_states_load",load_fixture())
 if not s.passed():print("EXPECTED RED construction consumer missing: ",loader.error);quit(1);return
 s.check("one_bounded_sample",loader.samples.size()==1 and loader.samples[0].id=="hoe-west")
 s.check("four_motion_poses",loader.samples[0].pose_ids==["hoe_west_key_0","hoe_west_key_1","hoe_west_key_2","hoe_west_key_3"])
 s.check("project_parent_path_rejected",not loader.load_samples(project+"/../"+project.get_file(),library.path_join("reviews/headwear-construction/review.json")))
 s.check("project_parent_path_atomic",loader.samples.is_empty() and loader.catalog_sha256=="")
 var defects=["missing_explicit_base","base_actual_duration","base_actual_scale","base_actual_root","empty_slots","wrong_design","empty_layers","wrong_layer_slot","wrong_layer_order","missing_helper","base_slots","base_template","recipe_slots_type","recipe_authoring_type","clip_unknown","frame_unknown","operation","missing_state","unknown_state","suite_unknown","suite_version_bool","suite_scope","state_unknown","state_hash","manifest_unknown","release","release_type","manifest_version","recipe_unknown","wrong_state","base_hash","base_unknown","base_pose","base_duration","fractional_duration","base_geometry","base_scope","output_unknown","output_pose","output_hash","output_rgba","output_size","output_not_png","source_hash","engine_hash","engine_path","missing_engine","input_path","absolute_output","traversal_output","backslash_output","manifest_path","source_link","output_link"]
 for defect in defects:
  reset_fixture()
  match defect:
   "missing_explicit_base":recipes.hair.clips[0].frames[0].layer_order=["hair"];publish()
   "base_actual_duration":base.clips[0].frames[0].duration_ms=101;publish()
   "base_actual_scale":base.clips[0].display_scale=0.5;publish()
   "base_actual_root":base.clips[0].root_anchor_px=[3,7];publish()
   "empty_slots":recipes.hair.slots={};publish()
   "wrong_design":recipes.hair.slots.hair=reference("parts/hat-straw-navy-band-v1/design.json");publish()
   "empty_layers":recipes.hair.clips[0].frames[0].layers=[];publish()
   "wrong_layer_slot":recipes.hair.clips[0].frames[0].layers[0].slot="hat";publish()
   "wrong_layer_order":recipes.hair_hat.clips[0].frames[0].layer_order=["near_hat","base","under_hat_hair","far_hat"];publish()
   "base_slots":base.slots={"body":null,"top":{"file":"parts/top04/design.json","sha256":"0".repeat(64)}};publish()
   "base_template":base.template=base.motion_set;publish()
   "recipe_slots_type":recipes.hair.slots=[];publish()
   "recipe_authoring_type":recipes.hair.authoring_inputs={};publish()
   "clip_unknown":recipes.hair.clips[0].extra=true;publish()
   "frame_unknown":recipes.hair.clips[0].frames[0].extra=true;publish()
   "operation":recipes.hair.clips[0].frames[0].operation="alpha-over";publish()
   "recipe_unknown":recipes.hair.extra=true;publish()
   "wrong_state":recipes.hair.head_state="hat";publish()
   "base_unknown":base.extra=true;publish()
   "base_pose":base.clips[0].frames[0].pose_id="other";publish()
   "base_duration":recipes.hair.clips[0].frames[0].duration_ms=101;publish()
   "fractional_duration":base.clips[0].frames[0].duration_ms=100.5;publish()
   "base_geometry":base.clips[0].canvas_px=[7,8];publish()
   "base_scope":base.clips[0].direction="east";publish()
  match defect:
   "missing_state":suite.states.erase("hat")
   "unknown_state":suite.states.extra=suite.states.bare
   "suite_unknown":suite.extra=true
   "suite_version_bool":suite.schema_version=true
   "suite_scope":suite.scope="production"
   "state_unknown":suite.states.hair.extra=true
   "state_hash":suite.states.hair.sha256="0".repeat(64)
   "manifest_unknown":manifests.hair.extra=true
   "release":manifests.hair.release_eligible=true
   "release_type":manifests.hair.release_eligible=0
   "manifest_version":manifests.hair.schema_version=true
   "base_hash":recipes.hair.base_recipe.sha256="0".repeat(64);save(library.path_join(manifests.hair.recipe),recipes.hair);manifests.hair.inputs[manifests.hair.recipe]=FileAccess.get_sha256(library.path_join(manifests.hair.recipe))
   "output_unknown":manifests.hair.outputs[0].extra=true
   "output_pose":manifests.hair.outputs[0].file="frames/hoe/west/other.png"
   "output_hash":manifests.hair.outputs[0].sha256="0".repeat(64)
   "output_rgba":manifests.hair.outputs[0].rgba_sha256="0".repeat(64)
   "output_size":manifests.hair.outputs[0].size=[7,8]
   "output_not_png":save(library.path_join("builds/head-hair").path_join(manifests.hair.outputs[0].file),{"not":"png"});manifests.hair.outputs[0].sha256=FileAccess.get_sha256(library.path_join("builds/head-hair").path_join(manifests.hair.outputs[0].file))
   "source_hash":save(library.path_join("sources/source.json"),{"changed":true})
   "engine_hash":save(project.path_join("tools/characters/build.py"),{"changed":true})
   "engine_path":manifests.hair.engine.code["../build.py"]="0".repeat(64)
   "missing_helper":manifests.hair.engine.code.erase("composition_contract.py")
   "missing_engine":manifests.hair.engine.code.erase("build.py")
   "input_path":manifests.hair.inputs["../outside.json"]="0".repeat(64)
   "absolute_output":manifests.hair.outputs[0].file="/private/tmp/out.png"
   "traversal_output":manifests.hair.outputs[0].file="frames/../out.png"
   "backslash_output":manifests.hair.outputs[0].file="frames\\out.png"
   "manifest_path":suite.states.hair.manifest="art/characters/builds/../outside/manifest.json"
   "source_link","output_link":
    var target=library.path_join("sources/source.json") if defect=="source_link" else library.path_join("builds/head-hair").path_join(manifests.hair.outputs[0].file)
    var backup=target+".original";DirAccess.rename_absolute(target,backup)
    s.check(defect+"_created",OS.execute("/bin/ln",PackedStringArray(["-s",backup,target]))==0)
  # Rehash outer bindings to ensure malformed content, rather than only its envelope, is tested.
  if defect not in ["missing_state","unknown_state","suite_unknown","suite_version_bool","suite_scope","state_unknown","state_hash","manifest_path"]:publish_manifests()
  else:save(library.path_join("reviews/headwear-construction/review.json"),suite)
  s.check("reject_"+defect,not load_fixture())
  s.check("atomic_"+defect,loader.samples.is_empty() and loader.catalog_sha256=="")
  if defect in ["source_link","output_link"]:
   var target=library.path_join("sources/source.json") if defect=="source_link" else library.path_join("builds/head-hair").path_join(manifests.hair.outputs[0].file)
   DirAccess.remove_absolute(target);DirAccess.rename_absolute(target+".original",target)
 reset_fixture();s.check("reload_after_failures",load_fixture())
 native_preservation_checks()
 print("CONSTRUCTION_LOADER checks=",s.checks.size()," passed=",s.passed());quit(0 if s.passed() else 1)
