extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
const Library=preload("res://dev/characters/character_construction_samples.gd")
var s=Support.new()
func _initialize() -> void:call_deferred("run")
func save(path:String,data:Variant) -> void:
 var file=FileAccess.open(path,FileAccess.WRITE);file.store_string(JSON.stringify(data));file.close()
func run() -> void:
 var project=""
 for argument in OS.get_cmdline_user_args():
  if argument.begins_with("--fixture-project="):project=argument.trim_prefix("--fixture-project=")
 s.check("temporary_fixture_only",project.begins_with("/private/tmp/coastal-"))
 if not s.passed():quit(1);return
 var path=project.path_join("art/characters/reviews/full/review.json")
 var loader=Library.new()
 s.check("real_built_complete_package_loads",loader.load_samples(project,path))
 if not s.passed():print("FULL_LOADER_ERROR ",loader.error);quit(1);return
 s.check("twenty_motion_samples",loader.samples.size()==20)
 s.check("fixed_head_one_binding",loader.manifest_bindings.size()==1 and loader.manifest_bindings.has("hair_hat"))
 s.check("full_package_flag",loader.get("full_package")==true)
 s.check("json_integral_pair_accepted",loader.uniform_pair([0.0,0.0],0.0) and loader.uniform_pair([1.0,1.0],1.0))
 s.check("nonunit_scale_rejected",not loader.uniform_pair([1.0,1.001],1.0) and not loader.uniform_pair([true,true],1.0))
 var ids:Array=[]
 for sample in loader.samples:
  ids.append(sample.id)
  s.check(sample.id+"_only_hair_hat",sample.textures_by_state.keys()==["hair_hat"] and sample.idle_by_state.keys()==["hair_hat"])
  s.check(sample.id+"_variable_pose_count",sample.pose_ids.size()==3 and sample.durations_ms.size()==3 and sample.textures_by_state.hair_hat.size()==3)
  s.check(sample.id+"_canonical_idle",sample.data.idle.pose_id=="idle_"+sample.data.direction+"_0")
 s.check("unique_motion_samples",ids.size()==20 and ids.count("walk-west")==1 and ids.count("harvest-north")==1)
 var original_text=FileAccess.get_file_as_string(path)
 var original=JSON.parse_string(original_text)
 var manifest_path=project.path_join(original.manifest.manifest)
 var manifest_text=FileAccess.get_file_as_string(manifest_path)
 var manifest=JSON.parse_string(manifest_text)
 var base=loader.read_json(project.path_join("art/characters/"+manifest.recipe))
 var base_recipe=loader.read_json(project.path_join("art/characters/"+base.base_recipe.file))
 base_recipe.slots.erase("pants")
 s.check("fixed_identity_rejects_missing_original_pants",loader.has_method("fixed_identity_valid") and not loader.call("fixed_identity_valid",project.path_join("art/characters"),base_recipe,base))
 var claim_path=""
 for file in manifest.inputs:
  if file.contains("/compatibility/"):claim_path=file;break
 s.check("fixture_has_transitive_claim",claim_path!="")
 if claim_path!="":
  var claim_file=project.path_join("art/characters/"+claim_path)
  var claim_text=FileAccess.get_file_as_string(claim_file)
  manifest.inputs.erase(claim_path)
  save(claim_file,{"tampered":true})
  manifest.artifact_digest=loader.bytes_hash(JSON.stringify({"inputs":manifest.inputs,"engine":manifest.engine},"",true).to_utf8_buffer())
  save(manifest_path,manifest)
  var corrupt=original.duplicate(true);corrupt.manifest.sha256=FileAccess.get_sha256(manifest_path);save(path,corrupt)
  s.check("unlisted_transitive_claim_rejected",not loader.load_samples(project,path))
  var file=FileAccess.open(claim_file,FileAccess.WRITE);file.store_string(claim_text);file.close()
  file=FileAccess.open(manifest_path,FileAccess.WRITE);file.store_string(manifest_text);file.close()
 var no_runtime=original.duplicate(true);no_runtime.erase("runtime");save(path,no_runtime)
 s.check("implicit_runtime_rejected",not loader.load_samples(project,path) and loader.samples.is_empty())
 var bad=original.duplicate(true);bad.canonical_idle.north=["idle_south_0"];save(path,bad)
 s.check("wrong_canonical_idle_rejected",not loader.load_samples(project,path) and loader.samples.is_empty())
 bad=original.duplicate(true);bad.samples.pop_back();save(path,bad)
 s.check("missing_motion_rejected",not loader.load_samples(project,path) and loader.samples.is_empty())
 var restore=FileAccess.open(path,FileAccess.WRITE);restore.store_string(original_text);restore.close()
 s.check("valid_reload_after_failure",loader.load_samples(project,path))
 print("CONSTRUCTION_FULL_LOADER checks=",s.checks.size()," passed=",s.passed())
 quit(0 if s.passed() else 1)
