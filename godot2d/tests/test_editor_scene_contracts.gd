extends SceneTree

var checks: Dictionary = {}

class JournalPlayerStub:
	extends CharacterBody2D
	var sprite := AnimatedSprite2D.new()
	func _init() -> void:
		add_child(sprite)

class JournalWorldStub:
	extends Node
	var player := JournalPlayerStub.new()
	var foraging
	var save_service
	var settings
	var release_input := false
	var session_started := true
	func _init(save_path: String) -> void:
		add_child(player)
		foraging = (load("res://scripts/player_state.gd") as Script).new()
		foraging.bag.add("clam", 2)
		save_service = (load("res://scripts/save_service.gd") as Script).new(save_path)
		settings = (load("res://scripts/settings_service.gd") as Script).new(save_path)
	func save_progress() -> bool:
		return true

func _initialize() -> void:
	call_deferred("run")

func check(id: String, value: bool) -> void:
	checks[id] = value
	print(("PASS " if value else "FAIL ") + id)

func require_nodes(path: String, names: Array[String]) -> bool:
	if not ResourceLoader.exists(path):
		print("FAIL missing scene: ", path)
		return false
	var packed := load(path) as PackedScene
	if packed == null:
		print("FAIL invalid scene: ", path)
		return false
	var instance := packed.instantiate()
	var ok := true
	for node_path in names:
		if not instance.has_node(node_path):
			print("FAIL before ready: ", path, " / ", node_path)
			ok = false
	instance.free()
	return ok

func property_names(object: Object) -> Array[String]:
	var names: Array[String] = []
	for entry in object.get_property_list():
		names.append(entry.name)
	return names

func run_batch_1() -> void:
	const HUD_PATH := "res://scenes/ui/hud.tscn"
	check("batch1_hud_nodes_before_ready", require_nodes(HUD_PATH, [
		"Root/Top/Title",
		"Root/Top/Subtitle",
		"Root/Top/Region",
		"Root/Bottom/Controls",
		"Root/Prompt",
		"Root/Toast",
		"Root/LocationPanel/Description",
		"Root/BackpackButton/Icon",
		"Root/BackpackButton/Hint",
	]))
	check("batch1_hud_scene_exists", ResourceLoader.exists(HUD_PATH))
	check("batch1_backpack_scene_exists", ResourceLoader.exists("res://scenes/ui/components/backpack_button.tscn"))
	check("batch1_theme_exists", ResourceLoader.exists("res://resources/ui/pixel_theme.tres"))
	var style_script := load("res://scripts/ui/pixel_style.gd") as Script
	var icon_script := load("res://scripts/ui/backpack_icon.gd") as Script
	check("batch1_pixel_style_editor_preview", style_script.is_tool())
	check("batch1_backpack_icon_editor_preview", icon_script.is_tool())
	for entry in [
		["pixel_canvas.tres", "canvas", ["173f49", "3d7277", "285966", "6e9c98", "24434c", "a7b995", "d56b45"]],
		["pixel_teal.tres", "teal", ["295b67", "639796", "9ac4ba", "c9e1cc", "24434c", "b6a07b", "d56b45"]],
		["pixel_active.tres", "active", ["9d523b", "df8057", "edaa7f", "ffe3b7", "24434c", "b6a07b", "d56b45"]],
		["pixel_focus.tres", "focus", ["9d523b", "df8057", "edaa7f", "ffe3b7", "24434c", "b6a07b", "d56b45"]],
	]:
		var style := load("res://resources/ui/" + entry[0]) as StyleBox
		check("batch1_" + entry[1] + "_serialized", style.get("kind") == entry[1]
			and style.content_margin_left == 10.0 and style.content_margin_top == 10.0
			and style.content_margin_right == 10.0 and style.content_margin_bottom == 10.0
			and (style.get("dark_color") as Color).is_equal_approx(Color(entry[2][0]))
			and (style.get("mid_color") as Color).is_equal_approx(Color(entry[2][1]))
			and (style.get("fill_color") as Color).is_equal_approx(Color(entry[2][2]))
			and (style.get("light_color") as Color).is_equal_approx(Color(entry[2][3]))
			and (style.get("shadow_color") as Color).is_equal_approx(Color(entry[2][4]))
			and (style.get("stitch_color") as Color).is_equal_approx(Color(entry[2][5]))
			and (style.get("focus_color") as Color).is_equal_approx(Color(entry[2][6])))
	if not ResourceLoader.exists(HUD_PATH):
		return

	var hud := (load(HUD_PATH) as PackedScene).instantiate()
	var root_control := hud.get_node("Root") as Control
	var top := hud.get_node("Root/Top") as Control
	var title := hud.get_node("Root/Top/Title") as Label
	var prompt := hud.get_node("Root/Prompt") as Label
	var icon := hud.get_node("Root/BackpackButton/Icon") as Control
	check("batch1_icon_editor_drawable", icon.size == Vector2(52, 52)
		and (icon.get("strap_dark_color") as Color).is_equal_approx(Color("463d31"))
		and (icon.get("strap_light_color") as Color).is_equal_approx(Color("d4ac6a"))
		and (icon.get("outline_color") as Color).is_equal_approx(Color("483c32"))
		and (icon.get("body_shadow_color") as Color).is_equal_approx(Color("986137"))
		and (icon.get("body_color") as Color).is_equal_approx(Color("c28a50"))
		and (icon.get("body_highlight_color") as Color).is_equal_approx(Color("e0b777"))
		and (icon.get("seam_color") as Color).is_equal_approx(Color("74482f"))
		and (icon.get("pocket_shadow_color") as Color).is_equal_approx(Color("694631"))
		and (icon.get("pocket_color") as Color).is_equal_approx(Color("ac7743"))
		and (icon.get("buckle_dark_color") as Color).is_equal_approx(Color("523e2d"))
		and (icon.get("buckle_light_color") as Color).is_equal_approx(Color("ffe0a0"))
		and (icon.get("edge_light_color") as Color).is_equal_approx(Color("e4b977"))
		and (icon.get("edge_dark_color") as Color).is_equal_approx(Color("734b31")))
	title.text = "Inspector 自定义标题"
	top.offset_bottom = 74.0
	prompt.add_theme_color_override("font_color", Color("7ad7ff"))
	root.add_child(hud)
	await process_frame
	check("batch1_title_override_survives_ready", title.text == "Inspector 自定义标题")
	check("batch1_top_offset_survives_ready", is_equal_approx(top.offset_bottom, 74.0))
	check("batch1_theme_color_survives_ready", prompt.get_theme_color("font_color") == Color("7ad7ff"))
	root.get_window().size = Vector2i(1440, 810)
	await process_frame
	await process_frame
	check("batch1_title_override_survives_resize", title.text == "Inspector 自定义标题")
	check("batch1_top_offset_survives_resize", is_equal_approx(top.offset_bottom, 74.0))
	check("batch1_theme_color_survives_resize", prompt.get_theme_color("font_color") == Color("7ad7ff"))
	check("batch1_root_full_rect", root_control.anchor_right == 1.0 and root_control.anchor_bottom == 1.0)
	hud.free()

func node_ids(nodes: Array[Node]) -> Array[int]:
	var ids: Array[int] = []
	for node in nodes:
		ids.append(node.get_instance_id())
	return ids

func key_event(code: int) -> InputEventKey:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.keycode = code
	event.pressed = true
	return event

func run_batch_2() -> void:
	const JOURNAL_PATH := "res://scenes/ui/journal.tscn"
	const MAIN_MENU_PATH := "res://scenes/ui/main_menu.tscn"
	const PAUSE_MENU_PATH := "res://scenes/ui/pause_menu.tscn"
	const BAG_PAGE_PATH := "res://scenes/ui/pages/bag_page.tscn"
	const PROFILE_PAGE_PATH := "res://scenes/ui/pages/profile_page.tscn"
	const SETTINGS_PAGE_PATH := "res://scenes/ui/pages/settings_page.tscn"
	const STORAGE_PAGE_PATH := "res://scenes/ui/pages/storage_page.tscn"
	const INVENTORY_SLOT_PATH := "res://scenes/ui/components/inventory_slot.tscn"
	const ITEM_DETAILS_PATH := "res://scenes/ui/components/item_details.tscn"
	const PORTRAIT_PATH := "res://scenes/ui/components/portrait.tscn"
	const NAME_DIALOG_PATH := "res://scenes/ui/dialogs/name_dialog.tscn"
	const QUANTITY_DIALOG_PATH := "res://scenes/ui/dialogs/quantity_dialog.tscn"
	const CONFIRM_DIALOG_PATH := "res://scenes/ui/dialogs/confirm_dialog.tscn"
	const SAVE_ERROR_DIALOG_PATH := "res://scenes/ui/dialogs/save_error_dialog.tscn"

	check("batch2_journal_nodes_before_ready", require_nodes(JOURNAL_PATH, [
		"Root/MainMenu/Surface/continue",
		"Root/PauseMenu/Surface/Tabs/tab_bag",
		"Root/PauseMenu/Surface/Tabs/tab_profile",
		"Root/PauseMenu/Surface/Tabs/tab_settings",
		"Root/PauseMenu/Surface/BagPage/BagGrid/bag_0",
		"Root/StoragePage/Surface/BagGrid/bag_0",
		"Root/StoragePage/Surface/ChestScroll/ChestGrid/chest_0",
		"Root/Dialogs/NameDialog/Panel/player_name",
		"Root/Dialogs/QuantityDialog/Panel/quantity",
		"Root/Dialogs/ConfirmDialog/Panel/cancel",
		"Root/Dialogs/SaveErrorDialog/Panel/retry",
	]))
	for entry in [
		["main_menu", MAIN_MENU_PATH], ["pause_menu", PAUSE_MENU_PATH],
		["bag_page", BAG_PAGE_PATH], ["profile_page", PROFILE_PAGE_PATH],
		["settings_page", SETTINGS_PAGE_PATH], ["storage_page", STORAGE_PAGE_PATH],
		["inventory_slot", INVENTORY_SLOT_PATH], ["item_details", ITEM_DETAILS_PATH],
		["portrait", PORTRAIT_PATH], ["name_dialog", NAME_DIALOG_PATH],
		["quantity_dialog", QUANTITY_DIALOG_PATH], ["confirm_dialog", CONFIRM_DIALOG_PATH],
		["save_error_dialog", SAVE_ERROR_DIALOG_PATH],
	]:
		check("batch2_" + entry[0] + "_scene_exists", ResourceLoader.exists(entry[1]))
	if not ResourceLoader.exists(JOURNAL_PATH):
		return

	var journal := (load(JOURNAL_PATH) as PackedScene).instantiate()
	var pre_tree_bag_slots: Array[Node] = journal.get_node("Root/PauseMenu/Surface/BagPage/BagGrid").find_children("bag_*", "Button", false, false)
	var pre_tree_storage_bag_slots: Array[Node] = journal.get_node("Root/StoragePage/Surface/BagGrid").find_children("bag_*", "Button", false, false)
	var pre_tree_storage_chest_slots: Array[Node] = journal.get_node("Root/StoragePage/Surface/ChestScroll/ChestGrid").find_children("chest_*", "Button", false, false)
	check("batch2_bag_24_slots_before_ready", pre_tree_bag_slots.size() == 24)
	check("batch2_storage_24_plus_48_before_ready", pre_tree_storage_bag_slots.size() == 24 and pre_tree_storage_chest_slots.size() == 48)
	var continue_button := journal.get_node("Root/MainMenu/Surface/continue") as Button
	continue_button.text = "Inspector 自定义继续"
	continue_button.add_theme_color_override("font_color", Color("7ad7ff"))
	var tab_button := journal.get_node("Root/PauseMenu/Surface/Tabs/tab_bag") as Button
	var slot_button := journal.get_node("Root/PauseMenu/Surface/BagPage/BagGrid/bag_0") as Button
	var slot_icon := slot_button.get_node("Icon") as Node2D
	var note_label := journal.get_node("Root/PauseMenu/Surface/Note") as Label
	var close_button := journal.get_node("Root/PauseMenu/Surface/close") as Button
	var tab_style := StyleBoxFlat.new()
	tab_style.bg_color = Color("123456")
	var slot_style := StyleBoxFlat.new()
	slot_style.bg_color = Color("654321")
	tab_button.add_theme_stylebox_override("normal", tab_style)
	slot_button.add_theme_stylebox_override("normal", slot_style)
	slot_icon.position = Vector2(17, 19)
	note_label.text = "Inspector 自定义固定说明"
	close_button.text = "Inspector 自定义返回"
	var stub := JournalWorldStub.new("/private/tmp/coastal-editor-b2-inspector-" + str(Time.get_ticks_usec()))
	journal.initialize(stub)
	root.add_child(journal)
	await process_frame
	check("batch2_unbound_override_survives_ready", continue_button.text == "Inspector 自定义继续"
		and continue_button.get_theme_color("font_color") == Color("7ad7ff"))
	journal.show_page("bag")
	journal.select_slot("bag", 0)
	journal.show_page("profile")
	journal.show_page("settings")
	journal.show_page("bag")
	root.get_window().size = Vector2i(1440, 810)
	await process_frame
	await process_frame
	check("batch2_tab_normal_override_survives_refresh_resize", tab_button.get_theme_stylebox("normal") == tab_style)
	check("batch2_slot_override_survives_refresh_resize", slot_button.get_theme_stylebox("normal") == slot_style
		and slot_icon.position == Vector2(17, 19))
	check("batch2_fixed_text_overrides_survive_refresh_resize", note_label.text == "Inspector 自定义固定说明"
		and close_button.text == "Inspector 自定义返回")
	paused = false
	journal.free()
	stub.free()

	var unbound_journal := (load(JOURNAL_PATH) as PackedScene).instantiate()
	root.add_child(unbound_journal)
	await process_frame
	check("batch2_unbound_journal_safe", unbound_journal.get("world") == null and unbound_journal.get("mode") == "")
	unbound_journal.free()

	for page_path in [BAG_PAGE_PATH, PROFILE_PAGE_PATH, SETTINGS_PAGE_PATH, STORAGE_PAGE_PATH]:
		var page := (load(page_path) as PackedScene).instantiate()
		root.add_child(page)
		await process_frame
		check("batch2_standalone_" + page_path.get_file().get_basename(), is_instance_valid(page))
		page.free()

	var scene := (load("res://scenes/harbor.tscn") as PackedScene).instantiate()
	scene.set_meta("journal_test", true)
	scene.set_meta("save_directory", "/private/tmp/coastal-editor-b2-contract-" + str(Time.get_ticks_usec()))
	root.add_child(scene)
	await process_frame
	await process_frame
	var ui = scene.journal
	var pause_menu: Node = ui.get_node("Root/PauseMenu")
	var bag_slots: Array[Node] = pause_menu.get_node("Surface/BagPage/BagGrid").find_children("bag_*", "Button", false, false)
	var storage_bag_slots: Array[Node] = ui.get_node("Root/StoragePage/Surface/BagGrid").find_children("bag_*", "Button", false, false)
	var storage_chest_slots: Array[Node] = ui.get_node("Root/StoragePage/Surface/ChestScroll/ChestGrid").find_children("chest_*", "Button", false, false)
	check("batch2_bag_24_slots_runtime", bag_slots.size() == 24)
	check("batch2_storage_24_plus_48_runtime", storage_bag_slots.size() == 24 and storage_chest_slots.size() == 48)
	var bag_ids := node_ids(bag_slots)
	var storage_bag_ids := node_ids(storage_bag_slots)
	var storage_chest_ids := node_ids(storage_chest_slots)
	var runtime_continue := ui.get_node("Root/MainMenu/Surface/continue") as Button
	var continue_id := runtime_continue.get_instance_id()
	runtime_continue.text = "保留的继续文本"
	runtime_continue.add_theme_color_override("font_color", Color("7ad7ff"))

	ui.show_page("bag")
	await process_frame
	var bag_zero := pause_menu.get_node("Surface/BagPage/BagGrid/bag_0") as Button
	bag_zero.grab_focus()
	await process_frame
	ui.show_page("profile")
	await process_frame
	check("batch2_hidden_page_loses_focus", root.gui_get_focus_owner() != bag_zero)
	for iteration in range(20):
		ui.show_page("bag")
		ui.select_slot("bag", iteration % 24)
		ui.show_page("profile")
		ui.show_page("settings")
		ui.confirm("确认测试", func(): pass)
		ui.cancel_modal()
	ui.show_page("title")
	await process_frame
	check("batch2_continue_instance_stable", runtime_continue.get_instance_id() == continue_id)
	check("batch2_continue_override_stable", runtime_continue.text == "保留的继续文本"
		and runtime_continue.get_theme_color("font_color") == Color("7ad7ff"))
	check("batch2_bag_instances_stable", node_ids(bag_slots) == bag_ids)
	check("batch2_storage_bag_instances_stable", node_ids(storage_bag_slots) == storage_bag_ids)
	check("batch2_storage_chest_instances_stable", node_ids(storage_chest_slots) == storage_chest_ids)

	ui.show_page("bag")
	await process_frame
	var sort_button := pause_menu.get_node("Surface/BagPage/sort") as Button
	var presses := [0]
	sort_button.pressed.connect(func(): presses[0] += 1)
	sort_button.grab_focus()
	ui._input(key_event(KEY_E))
	await process_frame
	check("batch2_one_key_one_operation", presses[0] == 1)

	var confirmed := [0]
	ui.confirm("默认取消测试", func(): confirmed[0] += 1)
	await process_frame
	var focus: Control = root.gui_get_focus_owner()
	check("batch2_confirm_defaults_cancel", focus is Button and focus.name == "cancel")
	ui._input(key_event(KEY_E))
	await process_frame
	check("batch2_confirm_cancel_safe", confirmed[0] == 0 and ui.modal == null
		and not ui.confirm_action.is_valid() and not ui.quantity_action.is_valid())
	ui.confirm("焦点圈测试", func(): confirmed[0] += 1)
	await process_frame
	runtime_continue.grab_focus()
	await process_frame
	await process_frame
	focus = root.gui_get_focus_owner()
	check("batch2_modal_focus_trapped", ui.modal != null and ui.modal.is_ancestor_of(focus))
	ui.cancel_modal()
	paused = false
	scene.free()

func run_batch_3() -> void:
	const PLAYER_PATH := "res://scenes/actors/player.tscn"
	const PLAYER_FRAMES_PATH := "res://resources/player_frames.tres"
	const PLAYER_MASK_PATH := "res://resources/player_mask.tres"
	const HARBOR_PATH := "res://scenes/harbor.tscn"

	check("batch3_player_scene_exists", ResourceLoader.exists(PLAYER_PATH))
	check("batch3_player_frames_exists", ResourceLoader.exists(PLAYER_FRAMES_PATH))
	check("batch3_player_mask_exists", ResourceLoader.exists(PLAYER_MASK_PATH))
	check("batch3_player_nodes_before_ready", require_nodes(PLAYER_PATH, [
		"CollisionShape2D",
		"AnimatedSprite2D",
		"Shadow",
	]))

	if ResourceLoader.exists(PLAYER_FRAMES_PATH):
		var frames := load(PLAYER_FRAMES_PATH) as SpriteFrames
		var animations := frames.get_animation_names()
		check("batch3_four_serialized_directions", animations.size() == 4)
		for direction in ["south", "west", "east", "north"]:
			check("batch3_%s_four_frames" % direction,
				animations.has(direction) and frames.get_frame_count(direction) == 4)
			check("batch3_%s_seven_fps" % direction,
				animations.has(direction) and is_equal_approx(frames.get_animation_speed(direction), 7.0))

	if ResourceLoader.exists(PLAYER_PATH):
		var packed := load(PLAYER_PATH) as PackedScene
		var first := packed.instantiate() as CharacterBody2D
		var second := packed.instantiate() as CharacterBody2D
		var collision := first.get_node("CollisionShape2D") as CollisionShape2D
		var first_sprite := first.get_node("AnimatedSprite2D") as AnimatedSprite2D
		var second_sprite := second.get_node("AnimatedSprite2D") as AnimatedSprite2D
		var shadow := first.get_node("Shadow") as Polygon2D
		check("batch3_collision_10_by_6", collision.shape is RectangleShape2D
			and (collision.shape as RectangleShape2D).size == Vector2(10, 6))
		check("batch3_shadow_serialized", shadow.polygon.size() == 4)
		check("batch3_mask_local_to_scene", first_sprite.material is ShaderMaterial
			and first_sprite.material.resource_local_to_scene)
		check("batch3_mask_instances_independent", first_sprite.material != second_sprite.material)

		first_sprite.offset = Vector2(3, -5)
		first_sprite.modulate = Color("75d6c8")
		first_sprite.z_index = 4
		first.modulate = Color("ffd6a5")
		first.z_index = 3
		first.process_mode = Node.PROCESS_MODE_DISABLED
		root.add_child(first)
		await process_frame
		first.set_doorway_hidden(0.75)
		first.doorway_material.set_shader_parameter("clip_enabled", true)
		first.reset_doorway_visual()
		check("batch3_sprite_inspector_values_survive_ready_restore",
			first_sprite.offset == Vector2(3, -5)
			and first_sprite.modulate == Color("75d6c8")
			and first_sprite.z_index == 4)
		check("batch3_player_inspector_values_survive_ready_restore",
			first.modulate == Color("ffd6a5") and first.z_index == 3)
		check("batch3_restore_clears_only_transition_state", first.doorway_hidden == 0.0
			and not first.doorway_material.get_shader_parameter("clip_enabled")
			and shadow.visible)
		first.free()
		second.free()

	var harbor := (load(HARBOR_PATH) as PackedScene).instantiate()
	var camera := harbor.get_node_or_null("WorldCamera") as Camera2D
	check("batch3_camera_serialized_before_ready", camera != null)
	if camera != null:
		camera.zoom = Vector2(1.75, 1.75)
		camera.position_smoothing_enabled = true
	harbor.set_meta("skip_verification", true)
	harbor.set_meta("save_directory", "/private/tmp/coastal-editor-b3-contract-" + str(Time.get_ticks_usec()))
	root.add_child(harbor)
	await process_frame
	await physics_frame
	check("batch3_one_runtime_player", harbor.find_children("Returnee", "CharacterBody2D", true, false).size() == 1
		and harbor.player != null)
	check("batch3_one_runtime_camera", harbor.find_children("WorldCamera", "Camera2D", true, false).size() == 1)
	if camera != null:
		check("batch3_camera_inspector_defaults_survive_ready",
			camera.zoom == Vector2(1.75, 1.75) and camera.position_smoothing_enabled)
		check("batch3_camera_targets_player", camera.target == harbor.player)
	paused = false
	harbor.free()

func run_batch_4() -> void:
	const EXTERIOR_PATH := "res://scenes/world/harbor_exterior.tscn"
	const TREE_PATH := "res://scenes/world/tree.tscn"
	const PROP_PATH := "res://scenes/world/prop.tscn"
	const PICKUP_PATH := "res://scenes/world/forage_pickup.tscn"
	check("batch4_exterior_nodes_before_ready", require_nodes(EXTERIOR_PATH, [
		"Terrain",
		"Terrain/WaterDetail",
		"DepthSortedObjects",
		"Spawn",
		"InteractPoints/house",
		"StaticCollisions",
	]))
	for entry in [["tree", TREE_PATH], ["prop", PROP_PATH], ["pickup", PICKUP_PATH]]:
		check("batch4_" + entry[0] + "_scene_exists", ResourceLoader.exists(entry[1]))
	if not ResourceLoader.exists(EXTERIOR_PATH):
		return
	var exterior := (load(EXTERIOR_PATH) as PackedScene).instantiate()
	var sort_layer := exterior.get_node_or_null("DepthSortedObjects") as Node2D
	var tree_nodes: Array[Node] = [] if sort_layer == null else sort_layer.find_children("CoastalTree*", "Node2D", false, false)
	var pickup_nodes: Array[Node] = [] if sort_layer == null else sort_layer.find_children("*_?", "Node2D", false, false)
	check("batch4_five_trees_before_ready", tree_nodes.size() == 5)
	check("batch4_six_pickups_before_ready", exterior.get_node_or_null("DepthSortedObjects/ForagePickups") != null
		and exterior.get_node("DepthSortedObjects/ForagePickups").get_child_count() == 6)
	check("batch4_static_props_and_collisions_before_ready", exterior.get_node_or_null("DepthSortedObjects/House") != null
		and exterior.get_node_or_null("DepthSortedObjects/Market") != null
		and exterior.get_node("StaticCollisions").get_child_count() >= 1)
	if tree_nodes.size() > 0:
		var tree := tree_nodes[0] as Node2D
		var moved := tree.position + Vector2(31, 17)
		tree.position = moved
		root.add_child(exterior)
		await process_frame
		check("batch4_tree_inspector_position_survives_ready", tree.position == moved)
		var blocker := tree.get_node_or_null("Base") as StaticBody2D
		check("batch4_safe_query_reads_moved_collision", blocker != null
			and exterior.safe_position(blocker.global_position) != blocker.global_position)
		exterior.free()
	else:
		exterior.free()

func run_batch_5() -> void:
	const INTERIOR_PATH := "res://scenes/world/house_interior.tscn"
	const EXTERIOR_ART_PATH := "res://scenes/world/house_exterior_art.tscn"
	const FURNITURE_PATH := "res://scenes/world/furniture.tscn"
	const DOOR_PATH := "res://scenes/world/interactive_door.tscn"
	const INDOOR_DOOR_PATH := "res://scenes/world/indoor_door.tscn"
	const OUTDOOR_DOOR_PATH := "res://scenes/world/outdoor_door.tscn"
	const OVERLAY_PATH := "res://scenes/ui/transition_overlay.tscn"
	const Room := preload("res://scripts/room_data.gd")
	const State := preload("res://scripts/player_state.gd")

	check("batch5_interior_nodes_before_ready", require_nodes(INTERIOR_PATH, [
		"StaticArt/Floor",
		"StaticArt/NorthWall",
		"StaticArt/Rug",
		"Furniture/Bed/Sprite2D",
		"Furniture/Bed/BaseCollision/CollisionShape2D",
		"Furniture/InteriorDoor/Approach",
		"StaticCollisions/NorthWall/CollisionShape2D",
		"Spawn",
		"Storage",
	]))
	check("batch5_interactive_door_nodes_before_ready", require_nodes(DOOR_PATH, [
		"DoorCollision/CollisionShape2D",
		"JambCollision/Left",
		"JambCollision/Right",
		"Frame/Left",
		"Frame/Right",
		"Frame/Top",
		"Recess",
		"DoorLeaf",
		"Threshold",
		"Approach",
	]))
	check("batch5_outdoor_door_visual_nodes_before_ready", require_nodes(OUTDOOR_DOOR_PATH, [
		"Outline/Outer",
		"Outline/Inner",
		"LeafEdge",
	]))
	check("batch5_exterior_four_parts_before_ready", require_nodes(EXTERIOR_ART_PATH, [
		"AtlasParts/Top",
		"AtlasParts/Left",
		"AtlasParts/Right",
		"AtlasParts/Bottom",
	]))
	check("batch5_overlay_before_ready", require_nodes(OVERLAY_PATH, ["Fade"]))
	for entry in [
		["interior", INTERIOR_PATH], ["exterior_art", EXTERIOR_ART_PATH],
		["furniture", FURNITURE_PATH], ["door", DOOR_PATH],
		["indoor_door", INDOOR_DOOR_PATH], ["outdoor_door", OUTDOOR_DOOR_PATH],
		["transition_overlay", OVERLAY_PATH],
	]:
		check("batch5_" + entry[0] + "_scene_exists", ResourceLoader.exists(entry[1]))
	if not ResourceLoader.exists(INTERIOR_PATH) or not ResourceLoader.exists(EXTERIOR_ART_PATH) \
			or not ResourceLoader.exists(INDOOR_DOOR_PATH) or not ResourceLoader.exists(OUTDOOR_DOOR_PATH) \
			or not ResourceLoader.exists(OVERLAY_PATH):
		return

	var interior := (load(INTERIOR_PATH) as PackedScene).instantiate()
	var furniture_root := interior.get_node("Furniture")
	var furniture_names := ["Bed", "nightstand", "kitchen", "table", "chair", "chest",
		"shelf", "photo", "window_left", "window_right", "plant"]
	var furniture_ok := true
	for furniture_name in furniture_names:
		var furniture := furniture_root.get_node_or_null(furniture_name)
		furniture_ok = furniture_ok and furniture != null \
			and furniture.get_node_or_null("Sprite2D") is Sprite2D \
			and furniture.get_node_or_null("BaseCollision/CollisionShape2D") is CollisionShape2D
	check("batch5_eleven_furniture_and_bases_before_ready", furniture_ok)
	check("batch5_room_data_reads_scene_furniture", (Callable(Room, "furniture").call(interior) as Array).size() == 11)

	var bed := furniture_root.get_node("Bed") as Node2D
	var original_bed_position := bed.position
	bed.position += Vector2(72, 0)
	var moved_bed_point := bed.position - Vector2(0, 20)
	root.add_child(interior)
	await process_frame
	check("batch5_furniture_inspector_position_survives_ready", bed.position == original_bed_position + Vector2(72, 0))
	check("batch5_moved_furniture_changes_runtime_safe_position",
		interior.safe_position(moved_bed_point) == interior.spawn_point())
	check("batch5_old_furniture_position_becomes_safe",
		interior.safe_position(original_bed_position - Vector2(0, 20)) == original_bed_position - Vector2(0, 20))
	check("batch5_room_data_reads_moved_collision",
		(Callable(Room, "blockers").call(interior) as Array).any(func(rect: Rect2): return rect.grow(6).has_point(moved_bed_point)))
	check("batch5_player_state_uses_scene_safe_source",
		Callable(State, "safe_position").call("house", moved_bed_point, interior) == interior.spawn_point())
	interior.free()

	var indoor_door := (load(INDOOR_DOOR_PATH) as PackedScene).instantiate()
	var approach_marker := indoor_door.get_node("Approach") as Marker2D
	approach_marker.position = Vector2(7, -41)
	indoor_door.position = Vector2(333, 321)
	root.add_child(indoor_door)
	await process_frame
	check("batch5_door_inspector_values_survive_ready",
		indoor_door.position == Vector2(333, 321) and approach_marker.position == Vector2(7, -41))
	check("batch5_door_approach_reads_marker",
		indoor_door.approach == indoor_door.position + approach_marker.position
		and indoor_door.can_interact(indoor_door.approach))
	var left_jamb := indoor_door.get_node("JambCollision/Left") as CollisionShape2D
	var right_jamb := indoor_door.get_node("JambCollision/Right") as CollisionShape2D
	indoor_door.set_pose(2)
	await physics_frame
	check("batch5_open_disables_channel_not_jambs",
		indoor_door.get_node("DoorCollision/CollisionShape2D").disabled
		and not left_jamb.disabled and not right_jamb.disabled)
	var indoor_leaf := indoor_door.get_node("DoorLeaf") as Sprite2D
	check("batch5_indoor_leaf_keeps_registered_strip",
		indoor_leaf.texture is AtlasTexture
		and (indoor_leaf.texture as AtlasTexture).region == Rect2(0, 29, 30, 8))
	indoor_door.free()

	var outdoor_door := (load(OUTDOOR_DOOR_PATH) as PackedScene).instantiate()
	var outdoor_recess := outdoor_door.get_node("Recess") as Polygon2D
	var outdoor_leaf := outdoor_door.get_node("DoorLeaf") as Sprite2D
	check("batch5_outdoor_recess_restores_sort_origin",
		outdoor_recess.position == Vector2(0, -40)
		and outdoor_recess.polygon == PackedVector2Array([
			Vector2(-11, 11), Vector2(11, 11), Vector2(11, 40), Vector2(-11, 40)]))
	check("batch5_outdoor_leaf_separates_sort_origin_from_draw_offset",
		outdoor_leaf.position == Vector2.ZERO
		and Vector2(outdoor_leaf.offset.x * outdoor_leaf.scale.x,
			outdoor_leaf.offset.y * outdoor_leaf.scale.y).is_equal_approx(Vector2(-11, -29)))
	check("batch5_outdoor_colors_round_trip_exactly",
		outdoor_recess.color == Color8(23, 46, 52)
		and (outdoor_door.get_node("Frame/Left") as Polygon2D).color == Color8(118, 145, 133)
		and (outdoor_door.get_node("Frame/Top") as Polygon2D).color == Color8(169, 185, 160)
		and (outdoor_door.get_node("Threshold") as Polygon2D).color == Color8(214, 199, 160)
		and (outdoor_door.get_node("LeafEdge") as Polygon2D).color == Color8(56, 116, 123))
	outdoor_door.free()

	var exterior_art := (load(EXTERIOR_ART_PATH) as PackedScene).instantiate() as Node2D
	var parts := exterior_art.get_node("AtlasParts").get_children()
	var regions: Array[Rect2] = []
	var destination_bounds := Rect2()
	var first_part := true
	for part in parts:
		var sprite := part as Sprite2D
		if sprite == null or not sprite.texture is AtlasTexture:
			continue
		var region := (sprite.texture as AtlasTexture).region
		regions.append(region)
		var destination := Rect2(exterior_art.position + sprite.position, region.size * sprite.scale)
		destination_bounds = destination if first_part else destination_bounds.merge(destination)
		first_part = false
	var non_overlapping := regions.size() == 4
	for first_index in regions.size():
		for second_index in range(first_index + 1, regions.size()):
			non_overlapping = non_overlapping and not regions[first_index].intersects(regions[second_index])
	check("batch5_exterior_four_atlas_regions_non_overlapping", non_overlapping)
	check("batch5_exterior_sort_origin_y165", exterior_art.position == Vector2(174, 165))
	check("batch5_exterior_original_world_bounds_preserved",
		destination_bounds.position.is_equal_approx(Vector2(90, 35.7705))
		and destination_bounds.size.is_equal_approx(Vector2(168, 154.2295)))
	exterior_art.free()

	var overlay := (load(OVERLAY_PATH) as PackedScene).instantiate()
	var fade := overlay.get_node("Fade") as ColorRect
	check("batch5_overlay_serialized", overlay is CanvasLayer and overlay.layer == 40
		and fade.modulate.a == 0.0 and fade.mouse_filter == Control.MOUSE_FILTER_IGNORE)
	overlay.free()

	var scene := (load("res://scenes/harbor.tscn") as PackedScene).instantiate()
	scene.set_meta("journal_test", true)
	scene.set_meta("save_directory", "/private/tmp/coastal-editor-b5-contract-" + str(Time.get_ticks_usec()))
	root.add_child(scene)
	await process_frame
	var runtime_bed := scene.home.interior.get_node("Furniture/Bed") as Node2D
	runtime_bed.position += Vector2(72, 0)
	var unsafe_point := runtime_bed.position - Vector2(0, 20)
	scene.start_new_game("批五合同")
	scene.home.switch_room("house", scene.home.interior.spawn_point())
	scene.player.position = unsafe_point
	check("batch5_save_uses_moved_furniture_collision", scene.save_progress()
		and scene.save_service.read_save().data.position == [scene.home.interior.spawn_point().x, scene.home.interior.spawn_point().y])
	var unsafe_save: Dictionary = scene.foraging.to_data(unsafe_point)
	check("batch5_unsafe_fixture_written", scene.save_service.write_save(unsafe_save))
	check("batch5_continue_uses_moved_furniture_collision", scene.continue_game()
		and scene.player.position == scene.home.interior.spawn_point())
	check("batch5_single_player_reparent_preserved",
		scene.find_children("Returnee", "CharacterBody2D", true, false).size() == 1)
	paused = false
	scene.free()

func run_batch_6() -> void:
	const HARBOR_PATH := "res://scenes/harbor.tscn"
	const CHILD_SCENES := [
		["exterior", "res://scenes/world/harbor_exterior.tscn", "DepthSortedObjects/ExteriorDoor"],
		["interior", "res://scenes/world/house_interior.tscn", "Furniture/InteriorDoor"],
		["player", "res://scenes/actors/player.tscn", "AnimatedSprite2D"],
		["hud", "res://scenes/ui/hud.tscn", "Root/BackpackButton"],
		["journal", "res://scenes/ui/journal.tscn", "Root/MainMenu/Surface/continue"],
		["transition", "res://scenes/ui/transition_overlay.tscn", "Fade"],
	]

	check("batch6_harbor_complete_before_ready", require_nodes(HARBOR_PATH, [
		"HarborExterior",
		"HarborExterior/DepthSortedObjects/Returnee",
		"HouseInterior",
		"WorldCamera",
		"HUD",
		"Journal",
		"HouseSession",
		"HouseSession/RoomTransition",
	]))

	var harbor := (load(HARBOR_PATH) as PackedScene).instantiate()
	var exterior := harbor.get_node_or_null("HarborExterior")
	var player := harbor.get_node_or_null("HarborExterior/DepthSortedObjects/Returnee") as CharacterBody2D
	var interior := harbor.get_node_or_null("HouseInterior")
	check("batch6_player_spawn_serialized_before_ready", exterior != null and player != null
		and player.position == exterior.spawn_point())
	check("batch6_interior_initial_state_serialized_before_ready", interior != null
		and not interior.visible and interior.process_mode == Node.PROCESS_MODE_DISABLED)
	check("batch6_single_player_before_ready",
		harbor.find_children("Returnee", "CharacterBody2D", true, false).size() == 1)
	check("batch6_room_transition_owned_by_session",
		harbor.get_node_or_null("HouseSession/RoomTransition/Fade") is ColorRect)
	harbor.free()

	var harbor_source := FileAccess.get_file_as_string("res://scripts/harbor.gd")
	check("batch6_parent_ready_has_no_migrated_scene_construction",
		harbor_source.find(".tscn\").instantiate()") == -1
		and harbor_source.find("scripts/house_session.gd\").new()") == -1)
	check("batch6_player_spawn_not_overwritten_from_data",
		harbor_source.find("player.position = data.SPAWN") == -1)

	var standalone_ok := true
	for entry in CHILD_SCENES:
		if not ResourceLoader.exists(entry[1]):
			standalone_ok = false
			continue
		var packed := load(entry[1]) as PackedScene
		var instance := packed.instantiate() if packed != null else null
		standalone_ok = standalone_ok and instance != null
		if instance == null:
			continue
		standalone_ok = standalone_ok and instance.get_node_or_null(entry[2]) != null
		root.add_child(instance)
		await process_frame
		match entry[0]:
			"interior":
				standalone_ok = standalone_ok and instance.sort_layer != null and instance.door != null
			"player":
				standalone_ok = standalone_ok and instance.sprite != null \
					and instance.shadow != null and instance.doorway_material != null
			"hud":
				standalone_ok = standalone_ok and instance.prompt != null \
					and instance.panel != null and instance.bag_button != null
			"journal":
				standalone_ok = standalone_ok and instance.root != null \
					and instance.main_menu != null and instance.pause_menu != null
			"transition":
				standalone_ok = standalone_ok and instance.fade != null
		instance.free()
	check("batch6_standalone_scenes_have_resources_and_fixed_refs", standalone_ok)

	var moved_spawn_scene := (load(HARBOR_PATH) as PackedScene).instantiate()
	var moved_spawn := Vector2(352, 250)
	moved_spawn_scene.get_node("HarborExterior/Spawn").position = moved_spawn
	moved_spawn_scene.set_meta("journal_test", true)
	moved_spawn_scene.set_meta("save_directory",
		"/private/tmp/coastal-editor-b6-spawn-contract-" + str(Time.get_ticks_usec()))
	root.add_child(moved_spawn_scene)
	await process_frame
	var started: bool = moved_spawn_scene.start_new_game("批六出生点")
	var saved: Dictionary = moved_spawn_scene.save_service.read_save()
	check("batch6_new_game_uses_inspector_spawn", started
		and moved_spawn_scene.player.position == moved_spawn
		and saved.ok and saved.data.position == [moved_spawn.x, moved_spawn.y])
	paused = false
	moved_spawn_scene.free()

func run() -> void:
	var batch := 0
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--batch="):
			batch = int(arg.trim_prefix("--batch="))
	if batch >= 1:
		await run_batch_1()
	if batch >= 2:
		await run_batch_2()
	if batch >= 3:
		await run_batch_3()
	if batch >= 4:
		await run_batch_4()
	if batch >= 5:
		await run_batch_5()
	if batch >= 6:
		await run_batch_6()
	paused = false
	var passed := not checks.values().has(false)
	print("EDITOR_SCENE_CONTRACTS ", checks.size(), " passed=", passed)
	quit(0 if passed else 1)
