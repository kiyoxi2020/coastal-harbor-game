extends RefCounted
## Bind the actual validated library, rather than trusting command-line intent.
static func rejected(message:String) -> Dictionary:return {"passed":false,"error":message}
static func verify(library:Object,contract:Dictionary,project:String) -> Dictionary:
 if library==null or library.get("full_package")!=true:return rejected("Actual library is not the full package")
 if contract.get("kind")!="coastal-all-actions-native-input-v1":return rejected("Unexpected native input contract")
 var suite=contract.get("suite");var files=contract.get("files");var expected=contract.get("manifest")
 if not suite is String or not files is Dictionary or not expected is Dictionary:return rejected("Missing frozen suite binding")
 var expected_sha=files.get(suite,"")
 if not expected_sha is String or expected_sha.length()!=64 or library.get("catalog_sha256")!=expected_sha:return rejected("Actual loaded suite SHA differs")
 var bindings=library.get("manifest_bindings")
 if not bindings is Dictionary or bindings.size()!=1 or not bindings.get("hair_hat") is Dictionary:return rejected("Actual fixed-head manifest binding missing")
 var actual:Dictionary=bindings.hair_hat
 if actual.get("manifest")!=expected.get("manifest") or actual.get("sha256")!=expected.get("sha256") or actual.get("artifact_digest")!=contract.get("artifact_digest"):return rejected("Actual loaded manifest/artifact differs")
 var runtime=library.get("runtime")
 if not runtime is Dictionary or not contract.get("runtime") is Dictionary or runtime!=contract.runtime:return rejected("Actual loaded runtime differs")
 var samples=library.get("samples");var expected_path:String=project.path_join(suite).simplify_path()
 if not samples is Array or samples.is_empty():return rejected("Actual loaded suite path missing")
 for sample in samples:
  if not sample is Dictionary or not sample.get("sample_path") is String or sample.sample_path.simplify_path()!=expected_path:return rejected("Actual loaded suite path differs")
 return {"passed":true,"actual_suite_path":str(samples[0].sample_path).simplify_path(),"catalog_sha256":library.get("catalog_sha256"),"manifest_binding":actual.duplicate(true),"runtime":runtime.duplicate(true),"full_package":true}
