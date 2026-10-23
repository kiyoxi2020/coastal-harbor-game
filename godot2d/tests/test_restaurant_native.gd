extends "res://tests/test_life_farming_native.gd"
func press(code:int):
	await key(code,true);await key(code,false)
func settle_day()->bool:
	await tap_e()
	check("sleep_open_day_%d"%w.foraging.life.day_id,w.journal.mode=="sleep")
	if w.journal.mode!="sleep":return false
	await click(w.journal.get_node("Root/SleepPage/Surface/Confirm"))
	check("daily_visible_%d"%w.foraging.life.day_id,w.journal.mode=="daily")
	await tap_e()
	return true
func enter_house_from_district()->bool:
	if not await walk_to(Vector2(320,220),"plaza_east"):return false
	if not await walk_to(Vector2(320,380),"south_exit"):return false
	await tap_e()
	check("travel_harbor",w.foraging.location=="harbor")
	if not await walk_to(Vector2(320,194),"harbor_door_row"):return false
	if not await walk_to(w.home.exterior_door.approach,"house_door"):return false
	if not await pass_door("house","enter"):return false
	if not await walk_to(Vector2(320,248),"bed_row"):return false
	return await walk_to(Vector2(232,248),"bed")
func return_restaurant()->bool:
	if not await walk_to(Vector2(320,248),"exit_row"):return false
	if not await walk_to(w.home.active_door().approach,"exit_door"):return false
	if not await pass_door("harbor","exit"):return false
	if not await walk_to(Vector2(320,194),"north_row"):return false
	if not await walk_to(Vector2(320,78),"north_exit"):return false
	# MAP01 marker is the authority; use its real exit point.
	var exit:Dictionary=preload("res://scripts/region_catalog.gd").exit_for("harbor",w)
	if not await walk_to(exit.point,"paired_exit"):return false
	await tap_e()
	check("travel_district",w.foraging.location=="harbor_district")
	if not await walk_to(Vector2(320,220),"plaza_back"):return false
	return await walk_to(Vector2(180,200),"service_back")
func run():
	evidence="/private/tmp/coastal-P11-native"
	DirAccess.make_dir_recursive_absolute(evidence)
	w=load("res://scenes/harbor.tscn").instantiate()
	w.set_meta("save_directory","/private/tmp/coastal-P11-native-save")
	w.set_meta("journal_test",true)
	w.set_meta("skip_verification",true)
	root.add_child(w)
	check("native_renderer",DisplayServer.get_name()!="headless")
	check("isolated",w.save_service.directory=="/private/tmp/coastal-P11-native-save")
	if not support.passed():finish();return
	w.start_new_game("餐馆原生验收")
	# Native UI fixture supplies one recipe; full farming+14-day economy is tested separately.
	w.foraging.bag.add("clam",2);w.foraging.bag.add("lettuce",2)
	w.home.switch_room("harbor_district",Vector2(320,350))
	if not await walk_to(Vector2(320,220),"plaza"):finish();return
	if not await walk_to(Vector2(180,200),"service"):finish();return
	await tap_e()
	var page=w.journal.get_node("Root/RestaurantPage")
	var view=w.get_node("HarborDistrict/DepthSortedObjects/Restaurant")
	check("E_opens_restaurant",w.journal.mode=="restaurant")
	check("closed_visible",view.get_node("ClosedSign").visible and not view.get_node("Customers/Customer1").visible)
	await capture("01-closed-page")
	await click(page.get_node("Surface/Supply"))
	check("clam_supply_saved",w.foraging.bag.count_item("clam")==1 and w.foraging.life.wallet==108)
	await click(page.get_node("Surface/SupplyItems").get_child(2))
	await click(page.get_node("Surface/Supply"))
	check("lettuce_supply_saved",w.foraging.bag.count_item("lettuce")==1 and w.foraging.life.wallet==120)
	await click(page.get_node("Surface/Open"))
	check("trial_saved",w.foraging.life.town.restaurant.status=="trial" and view.get_node("Customers/Customer1").visible and not view.get_node("Customers/Customer2").visible)
	await capture("02-trial-page")
	await press(KEY_ESCAPE);check("first_back_stays",w.journal.mode=="restaurant")
	await press(KEY_ESCAPE);check("second_back_closes",w.journal.mode=="")
	await capture("03-trial-world")
	if not await enter_house_from_district():finish();return
	if not await settle_day():finish();return
	if not await settle_day():finish();return
	check("two_good_operating",w.foraging.life.town.restaurant.status=="operating")
	if not await return_restaurant():finish();return
	await capture("04-operating-world")
	await tap_e()
	check("operating_two_customers",view.get_node("Customers/Customer2").visible)
	await capture("05-operating-page")
	var before:Dictionary=w.foraging.to_data(w.player.position)
	var disk=w.save_service.read_save()
	var state=preload("res://scripts/player_state.gd").new()
	check("disk_reload",disk.ok and state.restore(disk.data))
	if disk.ok and state.restore(disk.data):w._set_state(state)
	check("reload_no_income",w.foraging.life.wallet==before.life.wallet and preload("res://scripts/simulation/life_rules.gd")._same_payload(w.foraging.life.town.restaurant,before.life.town.restaurant) and view.get_node("Customers/Customer2").visible)
	await click(page.get_node("Surface/Close"))
	# Finite empty-supply fixture exercises decline with the same production rules.
	var inv=preload("res://scripts/inventory/inventory_container.gd").new(48)
	w.foraging.life.accounts.market.slots=inv.snapshot()
	for item in w.foraging.life.town.supply_depot.stock:w.foraging.life.town.supply_depot.stock[item]=0
	w.foraging.life.town.restaurant.slots=inv.snapshot()
	if not await enter_house_from_district():finish();return
	for i in range(3):
		if not await settle_day():finish();return
	check("three_bad_closed",w.foraging.life.town.restaurant.status=="closed" and not w.foraging.life.town.restaurant.enabled)
	if not await return_restaurant():finish();return
	await capture("06-closed-after-shortage")
	await tap_e()
	await click(page.get_node("Surface/SupplyItems").get_child(0));await click(page.get_node("Surface/Supply"))
	await click(page.get_node("Surface/SupplyItems").get_child(2));await click(page.get_node("Surface/Supply"))
	await click(page.get_node("Surface/Open"))
	check("resupplied_reopens",w.foraging.life.town.restaurant.status=="trial")
	page.get_node("Surface/FundingAmount").value=10
	var cash:int=w.foraging.life.wallet
	await click(page.get_node("Surface/Fund"))
	check("personal_funding_saved",w.foraging.life.wallet==cash-10)
	await capture("07-recovered-funded")
	finish()
