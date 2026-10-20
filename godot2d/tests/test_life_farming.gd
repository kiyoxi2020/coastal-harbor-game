extends SceneTree
const State = preload("res://scripts/player_state.gd")
const Schema = preload("res://scripts/simulation/state_schema.gd")
const Rules = preload("res://scripts/simulation/life_rules.gd")
const Save = preload("res://scripts/save_service.gd")
const Service = preload("res://scripts/simulation/action_service.gd")
const Support = preload("res://tests/life_test_support.gd")
const POINT := Vector2(330,250)
var s := Support.new()
var state = State.new()
var disk
class FailSave extends RefCounted:
	func write_save(_value: Dictionary) -> bool: return false
func act(kind: String,args: Dictionary) -> Dictionary:
	var before: Dictionary=state.to_data(POINT)
	var result: Dictionary=Service.new(disk).execute(state,POINT,kind,args,int(state.life.action_seq)+1)
	s.check("immutable_"+str(s.checks.size()),state.to_data(POINT)==before)
	if result.ok:
		state=result.next_state
		var loaded: Dictionary=disk.read_save()
		var restored=State.new()
		s.check("disk_reload_"+str(s.checks.size()),loaded.ok and restored.restore(loaded.data) and Rules._same_payload(restored.to_data(POINT),state.to_data(POINT)))
		state=restored
	return result
func reject(kind: String,args: Dictionary,code: String) -> void:
	var before: Dictionary=state.to_data(POINT)
	var result: Dictionary=Rules.plan(before,kind,args,int(state.life.action_seq)+1)
	s.check("reject_"+code+str(s.checks.size()),not result.ok and result.code==code and state.to_data(POINT)==before)
func _initialize() -> void:
	disk=Save.new(s.temporary_directory("grid-rules"))
	state.bag.add("lettuce_seed",16)
	state.bag.add("tomato_seed",16)
	reject("plant",{"cell_id":"garden_a:0:0","crop_id":"lettuce"},"not_tilled")
	reject("water",{"cell_id":"garden_a:0:0"},"not_tilled")
	for payload in [{},{"cell_id":1},{"cell_id":"garden_a:4:0"},{"cell_id":"plot_a"},{"cell_id":"garden_a:0:0","extra":1}]: reject("hoe",payload,"invalid_request")
	var ids:=Schema.cell_ids()
	for index in range(ids.size()):
		var id:=ids[index]
		s.check("hoe_"+id,act("hoe",{"cell_id":id}).ok)
		if index==0:
			reject("hoe",{"cell_id":id},"already_tilled")
			s.check("prewater",act("water",{"cell_id":id}).ok)
		var crop: String="lettuce" if index%2==0 else "tomato"
		s.check("plant_"+id,act("plant",{"cell_id":id,"crop_id":crop}).ok)
		if index==0: s.check("wet_seed",state.life.plots[id].watered)
		else: s.check("water_"+id,act("water",{"cell_id":id}).ok)
		reject("plant",{"cell_id":id,"crop_id":crop},"plot_occupied")
		reject("water",{"cell_id":id},"already_watered")
		reject("harvest",{"cell_id":id},"not_mature")
	# A failed disk write never consumes the request or advances a whole day.
	var before: Dictionary=state.to_data(POINT)
	var seq: int=state.life.action_seq
	var failed:=Service.new(FailSave.new()).execute(state,POINT,"sleep",{"expected_day":1},seq+1)
	s.check("save_failure_atomic",not failed.ok and failed.code=="save_failed" and state.to_data(POINT)==before)
	s.check("retry_same_request",act("sleep",{"expected_day":1}).ok)
	var first: Dictionary=state.to_data(POINT)
	var replay:=Service.new(FailSave.new()).execute(state,POINT,"sleep",{"expected_day":1},int(state.life.action_seq))
	s.check("duplicate_does_not_write_or_grow",replay.ok and replay.duplicate and replay.events.is_empty() and state.to_data(POINT)==first)
	for cell in state.life.plots.values():
		s.check("independent_growth_"+str(s.checks.size()),cell.growth==1 and not cell.watered)
	# Missed watering pauses growth for every crop, without killing them.
	s.check("dry_night",act("sleep",{"expected_day":2}).ok)
	s.check("no_unwatered_growth",state.life.plots[ids[0]].growth==1 and state.life.plots[ids[1]].growth==1)
	for day in range(3,6):
		for id in ids:
			var cell: Dictionary=state.life.plots[id]
			var limit:=2 if cell.crop_id=="lettuce" else 4
			if cell.growth<limit: s.check("rewater_"+str(day)+id,act("water",{"cell_id":id}).ok)
		s.check("night_"+str(day),act("sleep",{"expected_day":day}).ok)
		var report: Dictionary=state.life.daily_reports[-1]
		s.check("mature_report_"+str(day),report.mature_plots.size()==(8 if day in [3,5] else 0))
	# Full bag rejects harvest without erasing produce or wet soil.
	var bag_before: Array=state.bag.snapshot()
	var full: Array=[]
	for i in range(24): full.append({"id":"clam","amount":99})
	state.bag.restore_slots(full)
	reject("harvest",{"cell_id":ids[0]},"inventory_full")
	state.bag.restore_slots(bag_before)
	s.check("water_mature_soil",act("water",{"cell_id":ids[0]}).ok)
	before=state.to_data(POINT)
	failed=Service.new(FailSave.new()).execute(state,POINT,"harvest",{"cell_id":ids[0]},int(state.life.action_seq)+1)
	s.check("harvest_save_failure",not failed.ok and state.to_data(POINT)==before)
	var r:=act("harvest",{"cell_id":ids[0]})
	s.check("harvest_production",r.ok and r.events[0].kind=="production" and r.events[0].inputs=={} and r.events[0].outputs=={"lettuce":3})
	s.check("harvest_preserves_soil",state.life.plots[ids[0]].tilled and state.life.plots[ids[0]].watered and state.life.plots[ids[0]].crop_id=="")
	var after: Dictionary=state.to_data(POINT)
	replay=Service.new(FailSave.new()).execute(state,POINT,"harvest",{"cell_id":ids[0]},int(state.life.action_seq))
	s.check("duplicate_harvest",replay.ok and replay.duplicate and state.to_data(POINT)==after and state.bag.count_item("lettuce")==3)
	for i in range(1,ids.size()): s.check("harvest_"+ids[i],act("harvest",{"cell_id":ids[i]}).ok)
	s.check("sixteen_cell_yield",state.bag.count_item("lettuce")==24 and state.bag.count_item("tomato")==24)
	s.check("replant_wet",act("plant",{"cell_id":ids[0],"crop_id":"tomato"}).ok and state.life.plots[ids[0]].watered)
	s.check("clear_empty_wet_overnight",act("sleep",{"expected_day":6}).ok and not state.life.plots[ids[0]].watered)
	s.check("seventh_night",act("sleep",{"expected_day":7}).ok and state.life.day_id==8 and state.life.daily_reports.size()==7)
	for field in ["inputs","outputs"]:
		var bad: Dictionary=state.to_data(POINT)
		for event in bad.life.events:
			if event.kind=="production":
				event[field]={"wood":1}
				break
		s.check("bad_production_"+field,not State.valid_data(bad))
	print("GRID_RULES checks=",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
