extends SceneTree
const Binding=preload("res://tests/characters/registered_observation_binding.gd")
const Support=preload("res://tests/life_test_support.gd")
class FakeLibrary extends RefCounted:
 var full_package:=true
 var catalog_sha256:="a".repeat(64)
 var manifest_bindings={"hair_hat":{"manifest":"art/characters/builds/test/manifest.json","sha256":"b".repeat(64),"artifact_digest":"c".repeat(64)}}
 var runtime={"default_speed_factor":0.75}
 var samples=[{"sample_path":"/private/tmp/coastal-binding-test/art/characters/reviews/full/review.json"}]
var s=Support.new()
func _initialize() -> void:call_deferred("run")
func run() -> void:
 var contract={"kind":"coastal-all-actions-native-input-v1","suite":"art/characters/reviews/full/review.json","files":{"art/characters/reviews/full/review.json":"a".repeat(64)},"manifest":{"manifest":"art/characters/builds/test/manifest.json","sha256":"b".repeat(64)},"artifact_digest":"c".repeat(64),"runtime":{"default_speed_factor":0.75}}
 var project="/private/tmp/coastal-binding-test"
 var valid=Binding.verify(FakeLibrary.new(),contract,project)
 s.check("actual_selected_library_accepted",valid.get("passed")==true)
 for defect in ["suite-hash","suite-path","manifest-hash","manifest-path","artifact","runtime","partial","missing-proof"]:
  var library=FakeLibrary.new();var data=contract.duplicate(true)
  match defect:
   "suite-hash":library.catalog_sha256="d".repeat(64)
   "suite-path":library.samples=[{"sample_path":project+"/art/characters/reviews/other/review.json"}]
   "manifest-hash":library.manifest_bindings.hair_hat.sha256="d".repeat(64)
   "manifest-path":library.manifest_bindings.hair_hat.manifest="art/characters/builds/other/manifest.json"
   "artifact":library.manifest_bindings.hair_hat.artifact_digest="d".repeat(64)
   "runtime":library.runtime.default_speed_factor=1.0
   "partial":library.full_package=false
   "missing-proof":data.erase("files")
  s.check("reject_actual_"+defect,Binding.verify(library,data,project).get("passed")==false)
 s.check("binding_copies_actual_runtime",valid.get("runtime")==contract.runtime)
 quit(0 if s.passed() else 1)
