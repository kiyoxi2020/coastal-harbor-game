extends SceneTree
const Support = preload("res://tests/life_test_support.gd")
const ROOT := "/private/tmp/coastal-farming-catalog-v2"
var s := Support.new()
var catalog: Dictionary
func _initialize() -> void: call_deferred("run")
func save_json(path: String, value) -> void:
	var file := FileAccess.open(path,FileAccess.WRITE)
	file.store_string(JSON.stringify(value));file.close()
func make_fixture() -> void:
	DirAccess.make_dir_recursive_absolute(ROOT)
	catalog = {"schema_version":2,"template_id":"adult-standard-v1","clips":[]}
	for action in ["hoe","water","harvest"]:
		for direction in ["south","west","east","north"]:
			for garment in ["A","B"]:
				var id: String = action+"-"+direction+"-"+garment
				var directory: String = ROOT.path_join(id)
				DirAccess.make_dir_recursive_absolute(directory)
				var data := {"schema_version":1,"template_id":"adult-standard-v1","action_id":action,"direction":direction,"garment":garment,"status":"full_sequence_pending_visual_acceptance","canvas_px":[16,24],"root_anchor_px":[8,22],"display_scale":138.0/1164.0,"source_density_scale_vs_idle":2,"inputs":{},"frames":[]}
				var phases: Array = {"hoe":["ready","lift","contact","recovery"],"water":["ready","raise","pour","recovery"],"harvest":["ready","reach","pluck","recovery"]}[action]
				for i in range(4):
					# Tiny synthetic fixture textures are test data, never formal game art.
					var image := Image.create(16,24,false,Image.FORMAT_RGBA8)
					image.fill(Color(float(i+1)/5,0.4,0.8,1))
					var file := "%d.png" % i
					image.save_png(directory.path_join(file))
					var digest := FileAccess.get_sha256(directory.path_join(file))
					data.inputs[file] = digest
					data.frames.append({"pose_id":id+"_"+str(i),"phase":phases[i],"duration_ms":200,"file":file,"sha256":digest,"source":file,"source_sha256":digest})
				save_json(directory.path_join("candidate.json"),data)
				catalog.clips.append({"action_id":action,"direction":direction,"garment":garment,"candidate":id+"/candidate.json","sha256":FileAccess.get_sha256(directory.path_join("candidate.json")),"note":"完整序列候选，待用户验收。"})
	save_json(ROOT.path_join("catalog.json"),catalog)
func rejected(loader, id: String) -> void:
	save_json(ROOT.path_join("catalog.json"),catalog)
	s.check(id,not loader.load_catalog(ROOT,ROOT.path_join("catalog.json")) and loader.clips.is_empty() and loader.catalog_sha256.is_empty())
func run() -> void:
	make_fixture()
	var loader = load("res://dev/character_farming_review.gd").new()
	s.check("v2_complete_24_load",loader.load_catalog(ROOT,ROOT.path_join("catalog.json")))
	if not s.passed():
		printerr(loader.error);quit(1);return
	for record in catalog.clips:
		var clip: Dictionary = loader.get_clip(record.action_id,record.direction,record.garment)
		s.check(record.action_id+record.direction+record.garment+"_actual_clip",not clip.is_empty() and clip.direction==record.direction and clip.garment==record.garment and clip.textures.size()==4 and clip.durations_ms==[200,200,200,200])
	s.check("unknown_recipe_no_fallback",loader.get_clip("hoe","south","C").is_empty())
	var original := catalog.duplicate(true)
	catalog.clips.pop_back();rejected(loader,"missing_combo_rejected")
	catalog = original.duplicate(true);catalog.clips[23] = catalog.clips[0].duplicate(true);rejected(loader,"duplicate_combo_rejected")
	catalog = original.duplicate(true);catalog.clips[0].direction="diagonal";rejected(loader,"unknown_direction_rejected")
	catalog = original.duplicate(true);catalog.clips[0].garment="C";rejected(loader,"unknown_garment_rejected")
	catalog = original.duplicate(true);catalog.clips[0].direction="north";rejected(loader,"mismatched_direction_rejected")
	catalog = original.duplicate(true);catalog.clips[0].garment="B";rejected(loader,"mismatched_garment_rejected")
	catalog = original.duplicate(true)
	var path: String = ROOT.path_join(catalog.clips[0].candidate)
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path))
	data.frames.pop_back();save_json(path,data);catalog.clips[0].sha256=FileAccess.get_sha256(path);rejected(loader,"incomplete_sequence_rejected")
	make_fixture();data=JSON.parse_string(FileAccess.get_file_as_string(path));data.frames[2].phase="lift";save_json(path,data);catalog.clips[0].sha256=FileAccess.get_sha256(path);rejected(loader,"missing_contact_phase_rejected")
	make_fixture();data=JSON.parse_string(FileAccess.get_file_as_string(path));data.frames[2].file=data.frames[1].file;data.frames[2].sha256=data.frames[1].sha256;save_json(path,data);catalog.clips[0].sha256=FileAccess.get_sha256(path);rejected(loader,"duplicate_texture_sequence_rejected")
	make_fixture();s.check("valid_reload_recovers",loader.load_catalog(ROOT,ROOT.path_join("catalog.json")))
	var complete_v2 := catalog.duplicate(true)
	for indices in [[6,14,22],[3,11,19]]:
		catalog={"schema_version":1,"template_id":"adult-standard-v1","clips":[]}
		for index in indices: catalog.clips.append(complete_v2.clips[index])
		rejected(loader,"schema1_wrong_scope_"+str(indices[0]))
	make_fixture();s.check("v2_after_schema1_rejection_recovers",loader.load_catalog(ROOT,ROOT.path_join("catalog.json")))
	print("FARMING_CATALOG_V2 checks=",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
