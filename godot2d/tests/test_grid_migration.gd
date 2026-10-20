extends SceneTree
const State = preload("res://scripts/player_state.gd")
const V3 = preload("res://scripts/simulation/state_schema_v3.gd")
const Rules = preload("res://scripts/simulation/life_rules.gd")
const Support = preload("res://tests/life_test_support.gd")
var s := Support.new()
func _initialize() -> void:
	var old: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://tests/fixtures/life_save_v3.json"))
	old.life.plots.plot_a = {"crop_id":"lettuce","growth":1,"watered":true,"fertilized":false}
	old.life.plots.plot_b = {"crop_id":"tomato","growth":4,"watered":false,"fertilized":false}
	old.life.day_id = 3
	old.life.last_settled_day = 2
	old.life.wallet = 87
	old.life.action_seq = 12
	old.life.last_receipt = {"request_id":12,"kind":"water","args":{"plot_id":"plot_a"}}
	old.life.daily_reports = [{"day_id":2,"cash_in":12,"cash_out":5,"pickups":1,"mature_plots":["plot_b"],"summary":["旧记录"]}]
	s.check("frozen_v3_valid",V3.validate_v3(old))
	var migrated := State.migrate_data(old)
	s.check("v3_upgraded",migrated.get("version")==4 and State.valid_data(migrated))
	if not migrated.is_empty():
		var occupied := 0
		for cell in migrated.life.plots.values():
			if cell.crop_id != "": occupied += 1
		s.check("no_crop_duplication",occupied==2 and migrated.life.plots["garden_a:0:0"].growth==1 and migrated.life.plots["garden_a:0:0"].watered and migrated.life.plots["garden_b:0:0"].growth==4)
		s.check("preserve_economy",migrated.bag==old.bag and migrated.chest==old.chest and migrated.life.wallet==87 and migrated.life.accounts==old.life.accounts)
		s.check("preserve_history",migrated.life.day_id==3 and migrated.life.action_seq==12 and migrated.life.last_receipt==old.life.last_receipt and migrated.life.daily_reports[0].mature_plots==["garden_b:0:0"])
		var repeated:=Rules.plan(migrated,"water",{"plot_id":"plot_a"},12)
		s.check("old_receipt_still_deduplicates",repeated.ok and repeated.events.is_empty())
		var invalid_new:=Rules.plan(migrated,"water",{"plot_id":"plot_a"},13)
		s.check("old_id_rejected_for_new_action",not invalid_new.ok and invalid_new.code=="invalid_request")
		var restored = State.new()
		s.check("json_reload",restored.restore(JSON.parse_string(JSON.stringify(migrated))))
		for field in ["tilled","watered","growth"]:
			var bad := migrated.duplicate(true)
			bad.life.plots["garden_a:0:0"][field] = 1 if field != "growth" else true
			s.check("strict_"+field,not State.valid_data(bad))
		var bad := migrated.duplicate(true)
		bad.life.plots.erase("garden_b:3:1")
		s.check("missing_cell",not State.valid_data(bad))
		bad=migrated.duplicate(true)
		bad.life.plots["garden_b:9:1"]=bad.life.plots["garden_b:3:1"].duplicate(true)
		s.check("extra_cell",not State.valid_data(bad))
		bad=migrated.duplicate(true)
		bad.life.plots["garden_b:0:0"].fertilized=true
		s.check("mature_fertilizer_rejected",not State.valid_data(bad))
		bad=old.duplicate(true)
		bad.life.plots.plot_a["tilled"]=true
		s.check("v3_frozen_reject_extra",State.migrate_data(bad).is_empty())
	print("GRID_MIGRATION checks=",s.checks.size()," passed=",s.passed())
	quit(0 if s.passed() else 1)
