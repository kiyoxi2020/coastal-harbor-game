extends SceneTree
const Support=preload("res://tests/life_test_support.gd")
const Library=preload("res://dev/characters/character_headwear_samples.gd")
const Binding=preload("res://tests/characters/registered_observation_binding.gd")
const BODY_KIND="coastal-body-character-review-v1"
var s=Support.new()
var project:String
var fixture:String
var original_suite:Dictionary
var fixture_suite:String
var manifest_path:String
var manifest_text:String
var recipe_path:String
var recipe_text:String
class BoundLibrary extends RefCounted:
 var full_package:=true
 var suite_kind:=BODY_KIND
 var catalog_sha256:="a".repeat(64)
 var manifest_bindings={"body":{"manifest":"art/characters/builds/test/manifest.json","sha256":"b".repeat(64),"artifact_digest":"c".repeat(64)}}
 var runtime={"default_speed_factor":0.75}
 var samples=[{"sample_path":"/private/tmp/coastal-body-binding/art/characters/reviews/body/review.json"}]
func _initialize() -> void:call_deferred("run")
func save(path:String,data:Variant) -> void:
 DirAccess.make_dir_recursive_absolute(path.get_base_dir())
 var handle=FileAccess.open(path,FileAccess.WRITE);handle.store_string(JSON.stringify(data));handle.close()
func put_text(path:String,value:String) -> void:
 var handle=FileAccess.open(path,FileAccess.WRITE);handle.store_string(value);handle.close()
func copy_file(source:String,target:String) -> void:
 DirAccess.make_dir_recursive_absolute(target.get_base_dir())
 if DirAccess.copy_absolute(source,target)!=OK:s.check("fixture_copy_"+target.get_file(),false)
func make_fixture(suite_path:String) -> void:
 fixture="/private/tmp/coastal-body-samples-"+str(Time.get_ticks_usec())
 fixture_suite=fixture.path_join("art/characters/reviews/body/review.json")
 original_suite=JSON.parse_string(FileAccess.get_file_as_string(suite_path))
 save(fixture_suite,original_suite)
 var library=project.path_join("art/characters")
 var manifest_source=library.path_join(original_suite.manifest.file)
 manifest_path=fixture.path_join("art/characters/"+original_suite.manifest.file)
 copy_file(manifest_source,manifest_path)
 manifest_text=FileAccess.get_file_as_string(manifest_path)
 var manifest:Dictionary=JSON.parse_string(manifest_text)
 for file in manifest.inputs:copy_file(library.path_join(file),fixture.path_join("art/characters/"+file))
 for output in manifest.outputs:copy_file(manifest_source.get_base_dir().path_join(output.file),manifest_path.get_base_dir().path_join(output.file))
 for file in ["build.py","build_contract.py","composition_contract.py","pack_sources.py"]:
  copy_file(project.path_join("tools/characters/"+file),fixture.path_join("tools/characters/"+file))
 recipe_path=fixture.path_join("art/characters/"+manifest.recipe)
 recipe_text=FileAccess.get_file_as_string(recipe_path)
func rebind_recipe(loader:Object,recipe:Dictionary) -> void:
 save(recipe_path,recipe)
 var manifest:Dictionary=JSON.parse_string(manifest_text)
 manifest.inputs[manifest.recipe]=FileAccess.get_sha256(recipe_path)
 rebind_manifest(loader,manifest)
func rebind_manifest(loader:Object,manifest:Dictionary) -> void:
 manifest.artifact_digest=loader.bytes_hash(JSON.stringify({"inputs":manifest.inputs,"engine":manifest.engine},"",true).to_utf8_buffer())
 save(manifest_path,manifest)
 var suite=original_suite.duplicate(true);suite.manifest.sha256=FileAccess.get_sha256(manifest_path);save(fixture_suite,suite)
func reset_fixture() -> void:
 put_text(recipe_path,recipe_text);put_text(manifest_path,manifest_text);save(fixture_suite,original_suite)
func test_representation(strict:Object) -> void:
 var library=fixture.path_join("art/characters")
 var refs=original_suite.packed_sources.duplicate(true)
 var pack_path=library.path_join(refs[0].file)
 var pack_text=FileAccess.get_file_as_string(pack_path)
 var layout_path=pack_path.get_base_dir().path_join("layout.json")
 var layout_text=FileAccess.get_file_as_string(layout_path)
 var manifest:Dictionary=JSON.parse_string(manifest_text)
 for label in ["hair","idle-visible"]:
  var layout:Dictionary=JSON.parse_string(layout_text);layout.clips[0].representation=label;save(layout_path,layout)
  var pack:Dictionary=JSON.parse_string(pack_text)
  for output in pack.outputs:
   if output.file=="layout.json":output.sha256=FileAccess.get_sha256(layout_path)
  save(pack_path,pack)
  var inputs=manifest.inputs.duplicate(true)
  inputs[refs[0].file.get_base_dir().path_join("layout.json")]=FileAccess.get_sha256(layout_path)
  inputs[refs[0].file]=FileAccess.get_sha256(pack_path);refs[0].sha256=inputs[refs[0].file]
  s.check("body_rejects_packed_representation_"+label,strict.pack_index(fixture,library,refs,inputs).is_empty())
 put_text(pack_path,pack_text);put_text(layout_path,layout_text)
func test_unregistered_action(strict:Object) -> void:
 reset_fixture()
 var recipe:Dictionary=JSON.parse_string(recipe_text)
 var manifest:Dictionary=JSON.parse_string(manifest_text)
 var original:String=recipe.clips[0].action.file
 var alternate:String=original.get_base_dir().path_join("unregistered-action.json")
 copy_file(fixture.path_join("art/characters/"+original),fixture.path_join("art/characters/"+alternate))
 recipe.clips[0].action.file=alternate;save(recipe_path,recipe)
 manifest.inputs[alternate]=FileAccess.get_sha256(fixture.path_join("art/characters/"+alternate))
 manifest.inputs[manifest.recipe]=FileAccess.get_sha256(recipe_path)
 rebind_manifest(strict,manifest)
 s.check("body_rejects_action_outside_registered_motion",not strict.load_samples(fixture,fixture_suite))
 reset_fixture()
func test_binding() -> void:
 var contract={"kind":"coastal-all-actions-native-input-v1","suite_kind":BODY_KIND,"suite":"art/characters/reviews/body/review.json","files":{"art/characters/reviews/body/review.json":"a".repeat(64)},"manifest":{"manifest":"art/characters/builds/test/manifest.json","sha256":"b".repeat(64)},"artifact_digest":"c".repeat(64),"runtime":{"default_speed_factor":0.75}}
 var actual=BoundLibrary.new()
 s.check("body_actual_binding_accepted",Binding.verify(actual,contract,"/private/tmp/coastal-body-binding").get("passed")==true)
 actual.manifest_bindings={"hair_hat":actual.manifest_bindings.body}
 s.check("body_rejects_head_binding",Binding.verify(actual,contract,"/private/tmp/coastal-body-binding").get("passed")==false)
 actual=BoundLibrary.new();actual.suite_kind="coastal-character-construction-review-v1"
 s.check("body_rejects_wrong_actual_kind",Binding.verify(actual,contract,"/private/tmp/coastal-body-binding").get("passed")==false)
func test_trial(library:Object,suite_path:String) -> void:
 var trial=load("res://dev/characters/character_headwear_trial.tscn").instantiate()
 trial.head_catalog_override=suite_path
 root.add_child(trial);trial.set_physics_process(false)
 s.check("body_ready_uses_existing_install",trial.head_ready and trial.head_library.full_package and trial.head_error=="")
 if not trial.head_ready:return
 s.check("body_has_no_legacy_art",trial.artifact_digest=="" and trial.sample_library.samples.is_empty())
 s.check("body_head_controls_hidden",not trial.get_node("TrialUI/Headwear").visible)
 s.check("body_fixed_state",trial.head_state=="body" and trial.select_head_state("body") and not trial.select_head_state("hair_hat"))
 trial.head_label.text="";trial.refresh_head_label()
 s.check("body_label_refresh_has_no_head_identity", "身体" in trial.head_label.text and not "草帽" in trial.head_label.text)
 s.check("body_labels_not_old_costume",not "条纹" in trial.sample_label.text and "身体" in trial.sample_label.text)
 var speed_text=trial.get_node("TrialUI/Panel/Margin/Rows/Controls/MaxSpeed")
 var default_speed:float=library.runtime.default_speed_factor
 s.check("body_speed_label_matches_loaded_default",("%d%%"%roundi(default_speed*100)) in speed_text.text and not "原速" in speed_text.text)
 trial.set_speed_factor(0.5)
 s.check("body_speed_label_tracks_adjustment","50%" in speed_text.text)
 trial.set_speed_factor(default_speed)
 for direction in ["north","west","south","east"]:
  trial.set_motion_direction(direction)
  for action in ["idle","walk","run","hoe","water","harvest"]:
   trial.review_panel.select_clip(direction,action)
   s.check("body_preview_"+action+direction,trial.review_panel.preview_available() and trial.review_panel.motion_view.texture==trial.head_library.full_clips[action+"-"+direction].textures[0])
   if direction=="north" and action=="idle":s.check("body_preview_has_body_copy","身体" in trial.review_panel.message.text and not "草帽" in trial.review_panel.message.text)
  for action in ["hoe","water","harvest"]:
   s.check("body_farm_starts_"+action+direction,trial.start_farming_sample(action))
   var clip:Dictionary=library.full_clips[action+"-"+direction]
   var elapsed=0.0
   for i in range(clip.textures.size()):
    trial.farming_elapsed_ms=elapsed+float(clip.durations_ms[i])*0.5;trial.refresh_pose()
    s.check("body_farm_pose_"+action+direction+str(i),trial.pose.texture.get_image().get_data()==clip.textures[i].get_image().get_data())
    elapsed+=float(clip.durations_ms[i])
   trial.advance_farming_sample(5)
   s.check("body_farm_canonical_idle_"+action+direction,trial.farming_clip.is_empty() and trial.pose.texture==trial.head_library.canonical_idle[direction].textures[0])
 trial.queue_free()
func run() -> void:
 project=ProjectSettings.globalize_path("res://..").simplify_path()
 var suite_path=project.path_join("art/characters/reviews/body-actions/review.json")
 for argument in OS.get_cmdline_user_args():
  if argument.begins_with("--body-suite="):suite_path=argument.trim_prefix("--body-suite=")
 var loader=Library.new()
 s.check("body_suite_dispatch_loads",loader.load_samples(project,suite_path))
 if not s.passed():print("BODY_LOAD_ERROR ",loader.error);quit(1);return
 s.check("body_complete_24_capabilities",loader.full_package and not loader.candidate_package and loader.full_clips.size()==24 and loader.canonical_idle.size()==4)
 s.check("body_single_manifest_binding",loader.manifest_bindings.keys()==["body"])
 s.check("body_twenty_motion_samples",loader.samples.size()==20)
 s.check("body_variable_frames",loader.full_clips["hoe-west"].textures.size()==6 and loader.full_clips["water-west"].textures.size()==4 and loader.full_clips["walk-west"].textures.size()==6)
 for sample in loader.samples:
  s.check("body_observer_sample_"+sample.id,sample.sample_path==suite_path and sample.textures_by_state.keys()==["body"] and sample.idle_by_state.keys()==["body"])
 test_binding();test_trial(loader,suite_path)
 if "--body-ui-only" in OS.get_cmdline_user_args():
  print("BODY_UI checks=",s.checks.size()," passed=",s.passed());quit(0 if s.passed() else 1);return
 make_fixture(suite_path)
 var strict=load("res://dev/characters/character_body_samples.gd").new()
 s.check("body_copied_fixture_loads",strict.load_samples(fixture,fixture_suite))
 var image_path=manifest_path.get_base_dir().path_join("frames/idle/north/idle_north_0.png")
 s.check("body_rejects_fractional_image_dimensions",strict.rgba_image(image_path,[256.5,224])==null)
 var alpha_recipe:Dictionary=JSON.parse_string(recipe_text)
 alpha_recipe.clips[0].frames[0].composition="alpha-over"
 rebind_recipe(strict,alpha_recipe)
 s.check("body_accepts_single_layer_alpha_over",strict.load_samples(fixture,fixture_suite))
 test_representation(strict);test_unregistered_action(strict)
 for defect in ["scope","schema","manifest-traversal","duplicate-pack","runtime","missing-clip","extra-slot","mask","pose-time","output-rgba","input-closure"]:
  reset_fixture()
  var suite=original_suite.duplicate(true)
  var recipe:Dictionary=JSON.parse_string(recipe_text)
  var manifest:Dictionary=JSON.parse_string(manifest_text)
  match defect:
   "scope":suite.scope="production";save(fixture_suite,suite)
   "schema":suite.schema_version=2;save(fixture_suite,suite)
   "manifest-traversal":suite.manifest.file="builds/../escape/manifest.json";save(fixture_suite,suite)
   "duplicate-pack":suite.packed_sources.append(suite.packed_sources[0]);save(fixture_suite,suite)
   "runtime":suite.runtime.clips["walk-west"].playback_rate=2;save(fixture_suite,suite)
   "missing-clip":recipe.clips.pop_back();recipe.required_capabilities.pop_back();rebind_recipe(strict,recipe)
   "extra-slot":recipe.slots.hair=null;rebind_recipe(strict,recipe)
   "mask":recipe.clips[0].frames[0].layers[0].coverage=recipe.clips[0].frames[0].layers[0].texture;rebind_recipe(strict,recipe)
   "pose-time":recipe.clips[0].frames[0].duration_ms+=1;rebind_recipe(strict,recipe)
   "output-rgba":manifest.outputs[0].rgba_sha256="0".repeat(64);rebind_manifest(strict,manifest)
   "input-closure":manifest.inputs.erase(original_suite.packed_sources[0].file);rebind_manifest(strict,manifest)
  s.check("body_rejects_"+defect,not strict.load_samples(fixture,fixture_suite) and strict.samples.is_empty() and not strict.full_package)
 reset_fixture()
 s.check("body_reload_after_rejections",strict.load_samples(fixture,fixture_suite))
 print("BODY_SAMPLES checks=",s.checks.size()," passed=",s.passed())
 quit(0 if s.passed() else 1)
