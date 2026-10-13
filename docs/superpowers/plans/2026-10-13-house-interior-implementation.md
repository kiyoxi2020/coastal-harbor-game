# House Interior and Door Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成单屏小屋、独立门扇、双向动画、稳定存档和最新 Mac 试玩。

**Architecture:** 一个持久玩家与库存、两个互斥场景根；HouseSession 路由场景及坐标，RoomTransition 管理开门/跨门/淡入淡出/关门与输入锁，门对象管理三姿态及门洞碰撞。

**Tech Stack:** Godot 4.7.1 / GDScript / 原有图集分区渲染与原生像素家具绘制。

## Global Constraints

- 用户已批准住宅规格并明确要求继续到开发与自验完成，当前会话逐项执行，不另派代理。
- executing-plans 技能未提供，沿用测试驱动与逐项检查点流程。
- 内部 1280×720，室外 640×416、2 倍镜头；桌面默认面积 50%。
- 存档 v2 兼容 v1，测试仅专用临时存档；未知版本不得覆盖。
- 只交付当前 2D 版本，旧版完整移入 Git 忽略的 archive；3D 不变。
- 本阶段不实现交易、换日或料理；不展示伪造的可用功能。
- 房屋主体采用图集四片绘制剔除旧门，不破坏原图；家具为可编辑原生像素组件，不是整张静态室内图。

## Task 1: 先验证缺失能力

- [x] 新增 godot2d/tests/test_house.gd，资源守卫报告 FAIL missing_room_data，退出 1。
- [x] house_driver.gd 覆盖实机 E、门碰撞/姿态、进出、场景互斥、共享仓储、20 次切换、物理碰撞、旧档及异常。
- [x] 捕获并修复绘制层级、缺失目标恢复；测试将渲染帧后的操作改为实际键盘事件。

Run: `/Applications/Godot.app/Contents/MacOS/Godot --headless --log-file /private/tmp/house-source-all.log --path godot2d --script res://tests/test_house.gd`。
Expected: HOUSE passed=true；任何 SCRIPT ERROR 均不视为通过。

## Task 2: 场景与独立门

**Files:** 以下每个代码块为 godot2d/scripts/ 对应文件的完整实现，绝对工程根为 /Users/wyq/Documents/code/coastal-harbor-game。

**Interfaces:** Room 提供布局、交互点及碰撞；Door 提供 can_interact(point)、set_pose(value)、pose/collision/approach；Interior 提供 sort_layer 与 door。

- [x] 实现以下完整代码。

### room_data.gd

```gdscript
extends RefCounted
const FLOOR := Rect2(80,64,480,288)
const SPAWN := Vector2(320,328)
const DOOR := Vector2(320,352)
const STORAGE := Vector2(448,288)
const OUTSIDE_APPROACH := Vector2(209,194)
const OUTSIDE_DOOR := Vector2(209,165)

static func furniture() -> Array[Dictionary]:
	return [
		{"id":"bed","rect":Rect2(112,96,80,112)},
		{"id":"nightstand","rect":Rect2(200,112,32,32)},
		{"id":"kitchen","rect":Rect2(400,88,128,56)},
		{"id":"table","rect":Rect2(128,250,80,40)},
		{"id":"chair","rect":Rect2(96,256,24,30)},
		{"id":"chest","rect":Rect2(426,264,44,32)},
		{"id":"shelf","rect":Rect2(272,80,96,32)},
		{"id":"plant","rect":Rect2(510,292,24,24)}]

static func blockers() -> Array[Rect2]:
	var result: Array[Rect2]=[
		Rect2(64,48,512,32),Rect2(64,64,24,304),Rect2(552,64,24,304),
		Rect2(80,348,220,24),Rect2(340,348,220,24)]
	for item in furniture(): result.append(item.rect)
	return result

static func locations() -> Array[Dictionary]:
	return [
		{"id":"bed","point":Vector2(152,226),"title":"祖辈留下的床","body":"洗晒过的被子还带着阳光的味道。\n休息换日将在后续版本开放。"},
		{"id":"kitchen","point":Vector2(460,162),"title":"旧屋的小厨房","body":"旧瓷碗与铜壶已经摆好。\n料理功能尚未开放。"},
		{"id":"photo","point":Vector2(320,132),"title":"一张旧合照","body":"照片里的人站在热闹的渔港前。\n你把它放回了原来的位置。"}]
```

### house_exterior.gd

```gdscript
extends Node2D
# Draw the existing atlas in non-overlapping pieces, omitting the old leaf.
# Pixel coordinates are source-atlas coordinates, not destructive image edits.
const REGION := Rect2(34,91,488,448)
const HOLE := Rect2(347,382,63,84)
const FACTOR := 168.0/488.0
var texture: Texture2D
func _ready() -> void:
	texture=load("res://assets/environment.png")
	set_meta("door_cutout",true)
	queue_redraw()
func part(source: Rect2) -> void:
	var point: Vector2=(source.position-REGION.position)*FACTOR+Vector2(-84,-448*FACTOR)
	draw_texture_rect_region(texture,Rect2(point,source.size*FACTOR),source)
func _draw() -> void:
	if not texture: return
	part(Rect2(REGION.position,Vector2(REGION.size.x,HOLE.position.y-REGION.position.y)))
	part(Rect2(REGION.position.x,HOLE.position.y,HOLE.position.x-REGION.position.x,HOLE.size.y))
	part(Rect2(HOLE.end.x,HOLE.position.y,REGION.end.x-HOLE.end.x,HOLE.size.y))
	part(Rect2(REGION.position.x,HOLE.end.y,REGION.size.x,REGION.end.y-HOLE.end.y))
```

### interactive_door.gd

```gdscript
extends Node2D
# Separate interactive body, frame, darkness and leaf. No rotated smooth sprites.
var inside := false
var approach := Vector2.ZERO
var pose := 0
var collision: CollisionShape2D
var body: StaticBody2D
var texture: Texture2D

func _ready() -> void:
	texture=load("res://assets/environment.png")
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	body=StaticBody2D.new()
	body.name="DoorCollision"
	collision=CollisionShape2D.new()
	var shape:=RectangleShape2D.new()
	shape.size=Vector2(38 if inside else 26,8)
	collision.shape=shape
	body.add_child(collision)
	add_child(body)
	set_pose(0)

func can_interact(point: Vector2) -> bool:
	var offset:=point-approach
	return offset.length()<=24 and absf(offset.x)<=16 and (point.y<=position.y-4 if inside else point.y>=position.y+12)

func set_pose(value: int) -> void:
	pose=clampi(value,0,2)
	if is_instance_valid(collision): collision.set_deferred("disabled",pose==2)
	queue_redraw()

func _draw() -> void:
	var width:=32.0 if inside else 22.0
	var height:=16.0 if inside else 29.0
	var r:=Rect2(-width/2,-8.0 if inside else -height,width,height)
	draw_rect(r.grow(3),Color("264d51"))
	draw_rect(r.grow(1),Color("769185"))
	draw_rect(r,Color("172e34"))
	# Hinged leaf uses three integer widths, reusing the exact original teal leaf.
	var leaf_width: float=[width,roundf(width*0.5),3.0][pose]
	if texture:
		draw_texture_rect_region(texture,Rect2(r.position,Vector2(leaf_width,height)),Rect2(348,383,61,81))
	if pose>0:
		draw_rect(Rect2(r.position+Vector2(leaf_width-2,0),Vector2(2,height)),Color("38747b"))
	draw_rect(Rect2(-width/2-3,8 if inside else 0,width+6,3),Color("d6c7a0"))
```

### house_furniture.gd

```gdscript
extends Node2D
var kind := "bed"
var extent := Vector2(80,112)
func block(x: float,y: float,w: float,h: float,c: String) -> void:
	draw_rect(Rect2(x,y,w,h),Color(c))
func _draw() -> void:
	var w:=extent.x
	var h:=extent.y
	# Local origin is the object's feet; all highlights use hard pixel rectangles.
	draw_set_transform(Vector2(-w/2,-h))
	block(3,h-2,w,6,"473e3540")
	match kind:
		"bed":
			block(0,0,w,h,"594633");block(4,2,w-8,h-6,"a0774f")
			block(4,5,w-8,17,"cb9e67");block(8,8,w-16,3,"ecd1a0")
			block(8,25,w-16,h-33,"f6e7bf");block(12,27,w-24,21,"fff3d3")
			block(12,43,w-24,4,"cbb78f");block(7,54,w-14,h-63,"477e82")
			block(10,57,w-20,5,"82b3aa");block(12,65,w-24,3,"326775")
			for x in range(16,int(w)-12,16): block(x,60,4,h-73,"b4cabb")
			block(3,h-9,w-6,7,"795838");block(8,h-7,w-16,2,"c29a62")
			for x in [17,41]:
				for y in [70,87]:
					block(x,y,8,2,"d3dfb8");block(x+3,y-3,2,8,"d3dfb8")
			block(10,30,3,13,"e0cea5");block(w-16,30,3,13,"e0cea5")
		"kitchen":
			block(0,0,w,h,"5b5040");block(3,3,w-6,h-6,"b48959")
			block(2,2,w-4,21,"dfd8b8");block(5,5,w-10,3,"fbefce")
			for x in range(5,int(w)-10,32):
				block(x,27,28,23,"815d3d");block(x+2,29,24,18,"b59165");block(x+18,32,5,2,"5c5945")
			block(12,7,37,15,"4a6870");block(15,9,31,10,"83b5b8");block(22,1,3,8,"537378")
			block(84,5,32,17,"364e51");block(88,8,10,10,"738581");block(102,8,10,10,"738581")
			block(61,8,11,12,"bd694e");block(62,5,9,4,"e6b66b")
			block(66,0,3,6,"799577");block(61,0,6,3,"92ad75")
			block(78,-4,13,9,"c7b37f");block(81,-7,7,3,"8c744e")
		"table":
			block(7,h-4,7,9,"68503c");block(w-14,h-4,7,9,"68503c")
			block(0,0,w,h-3,"6c4e35");block(3,3,w-6,h-10,"b88651")
			for y in range(8,int(h)-7,10): block(4,y,w-8,2,"986e45")
			block(20,2,27,h-9,"ead6a4");block(23,2,3,h-9,"a95d49")
			block(30,8,12,10,"f3ecd4");block(32,10,8,5,"be9460")
			block(55,12,13,2,"efe5ca");block(53,14,17,9,"efe5ca");block(55,23,13,2,"cab895")
			block(58,16,7,5,"cda366");block(6,6,8,1,"d7ad76")
		"chair":
			block(2,0,w-4,h,"684e35");block(5,3,w-10,9,"bf945c");block(4,16,w-8,10,"c6a572")
		"chest":
			block(0,0,w,h,"524533");block(2,3,w-4,h-6,"b18a52")
			block(3,5,w-6,3,"d6b679");block(2,13,w-4,3,"725133")
			block(7,2,4,h-3,"447375");block(w-11,2,4,h-3,"447375")
			block(w/2-4,12,8,9,"e0bd70");block(w/2-1,15,2,4,"70512f")
		"shelf":
			block(0,0,w,h,"644c38");block(3,3,w-6,h-6,"b28a5a")
			for x in range(6,42,7): block(x,6,5,19,["668c86","c88761","e8c98e"][x%3])
			block(53,1,24,27,"69492f");block(56,4,18,21,"eee0b7")
			block(58,17,14,5,"61949a");block(62,10,6,9,"bc875e");block(81,12,9,14,"78927b")
		"plant":
			block(5,12,w-10,h-12,"ab6850");block(3,11,w-6,4,"d59568")
			block(10,-10,4,24,"547b58");block(0,-5,11,9,"698c5c");block(12,-13,11,10,"8bad69")
			block(-4,-2,9,6,"52754f");block(14,-7,12,7,"658955");block(7,-18,7,10,"93af72")
			block(7,16,3,6,"d8966a")
		_:
			block(0,0,w,h,"846045");block(3,3,w-6,h-6,"c79962")
			block(w/2-3,h/2,6,3,"e6c275")
			block(9,-13,14,13,"eee3bb");block(12,-18,8,6,"d4b67c")
```

### house_interior.gd

```gdscript
extends Node2D
const Data=preload("res://scripts/room_data.gd")
var sort_layer: Node2D
var door
func _ready() -> void:
	texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	sort_layer=Node2D.new()
	sort_layer.y_sort_enabled=true
	add_child(sort_layer)
	for item in Data.furniture():
		var node:=Node2D.new()
		node.set_script(preload("res://scripts/house_furniture.gd"))
		node.kind=item.id
		node.name=item.id.capitalize()
		node.extent=item.rect.size
		node.position=Vector2(item.rect.get_center().x,item.rect.end.y)
		sort_layer.add_child(node)
	for rect in Data.blockers():
		var body:=StaticBody2D.new()
		var shape:=CollisionShape2D.new()
		var box:=RectangleShape2D.new()
		box.size=rect.size
		shape.shape=box
		body.position=rect.get_center()
		body.add_child(shape)
		add_child(body)
	door=Node2D.new()
	door.set_script(preload("res://scripts/interactive_door.gd"))
	door.name="InteriorDoor"
	door.position=Data.DOOR
	door.approach=Data.SPAWN
	door.inside=true
	# Cutaway southern wall: the leaf is behind the actor, never hiding their feet.
	add_child(door)
	move_child(door,0)

func block(r: Rect2,c: String) -> void:
	draw_rect(r,Color(c))
func _draw() -> void:
	block(Rect2(-200,-200,1040,900),"183039")
	block(Rect2(72,42,496,318),"493e35")
	block(Data.FLOOR,"b08b5b")
	for row in range(18):
		for column in range(11):
			var x:=80+column*48-(24 if row%2 else 0)
			var rect:=Rect2(x,64+row*16,46,14).intersection(Data.FLOOR)
			if rect.size.x<=0: continue
			block(rect,["c19b69","c8a573","b99565","bc9766"][(row*7+column*3)%4])
			block(Rect2(rect.position+Vector2(4,4),Vector2(maxf(0,rect.size.x-10),1)),"d4b17d")
			if rect.size.x>20: block(Rect2(rect.position+Vector2(9,10),Vector2(9,1)),"aa8256")
	# Wallpaper, teal wainscoting, mullioned windows and sparse seaside ornaments.
	block(Rect2(80,50,480,46),"e2d5b2")
	for x in range(88,552,16): block(Rect2(x,53,1,29),"cec3a2")
	block(Rect2(80,84,480,12),"467375")
	block(Rect2(80,93,480,3),"a9b9a0")
	for x in [126,416]:
		block(Rect2(x,53,60,35),"355860");block(Rect2(x+3,56,54,28),"8cbec3")
		block(Rect2(x+6,59,20,9),"d6e1cc");block(Rect2(x+31,59,22,9),"c5ddd0")
		block(Rect2(x+28,55,3,31),"f4e5bd");block(Rect2(x+3,69,54,3),"f4e5bd")
		block(Rect2(x-4,50,6,35),"efdfb7");block(Rect2(x+59,50,6,35),"efdfb7")
		block(Rect2(x-5,85,70,5),"d4b17c")
	block(Rect2(84,84,5,264),"65796a");block(Rect2(551,84,5,264),"65796a")
	block(Rect2(80,348,220,7),"6b5c44");block(Rect2(340,348,220,7),"6b5c44")
	block(Rect2(298,346,44,9),"d2b88b")
	block(Rect2(252,179,136,92),"547e7e");block(Rect2(256,183,128,84),"92ada0")
	block(Rect2(260,187,120,76),"6c9690")
	for x in range(262,380,10):
		block(Rect2(x,182,4,3),"efe1b5");block(Rect2(x,267,4,3),"efe1b5")
	for x in range(277,372,30): block(Rect2(x,218,8,8),"c6cfaf")
	block(Rect2(113,211,78,15),"b46f51")
	for x in range(117,188,9): block(Rect2(x,214,3,9),"dfb37b")
```

- [x] 运行上述 house 测试；独立检查旧场景回归，不删除旧覆盖。

## Task 3: 切换控制与会话

**Files:** 以下每个代码块为 godot2d/scripts/ 对应文件的完整实现，绝对工程根为 /Users/wyq/Documents/code/coastal-harbor-game。

**Interfaces:** HouseSession 消费 world 的持久玩家/foraging/HUD，产出 switch_room、safe_position、active_door、storage_point；Transition 消费 home，产出 begin、busy、phase_changed、stable_snapshot 与 exit_pending。

- [x] 实现以下完整代码。

### room_transition.gd

```gdscript
extends Node
signal phase_changed(phase: String)
var home
var busy := false
var phase := "Idle"
var stable_snapshot: Dictionary = {}
var exit_pending := false
var fade: ColorRect
func _ready() -> void:
	var layer:=CanvasLayer.new()
	layer.layer=40
	add_child(layer)
	fade=ColorRect.new()
	fade.color=Color(0.06,0.12,0.14,1)
	fade.modulate.a=0
	fade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	fade.mouse_filter=Control.MOUSE_FILTER_IGNORE
	layer.add_child(fade)
func set_phase(value: String) -> void:
	phase=value
	phase_changed.emit(value)
func begin() -> bool:
	var world=home.world
	if busy or not world.session_started or world.journal.mode!="" or world.hud.panel.visible:
		return false
	var door=home.active_door()
	if not door.can_interact(world.player.position): return false
	stable_snapshot=world.foraging.to_data(home.safe_position(world.foraging.location,world.player.position))
	busy=true
	world.hud.dismiss()
	world.player.velocity=Vector2.ZERO
	world.player.z_index=1
	world.release_input=true
	run.call_deferred()
	return true
func pause_for(seconds: float) -> void:
	await get_tree().create_timer(seconds,false).timeout
func walk_to(point: Vector2,duration: float) -> void:
	var player=home.world.player
	var delta: Vector2=point-player.position
	player.facing="south" if delta.y>=0 else "north"
	if absf(delta.x)>absf(delta.y): player.facing="east" if delta.x>0 else "west"
	player.sprite.play(player.facing)
	var tween:=create_tween()
	tween.tween_property(player,"position",point,duration)
	await tween.finished
	player.sprite.stop()
func animate_door(door,opening: bool) -> void:
	for pose in ([0,1,2] if opening else [2,1,0]):
		door.set_pose(pose)
		await pause_for(0.1)
func opacity(value: float) -> void:
	var tween:=create_tween()
	tween.tween_property(fade,"modulate:a",value,0.15)
	await tween.finished
func run() -> void:
	var world=home.world
	var source: String=world.foraging.location
	var destination: String="house" if source=="harbor" else "harbor"
	var door=home.active_door()
	set_phase("Approach")
	await walk_to(door.approach,0.15)
	set_phase("Opening")
	await animate_door(door,true)
	set_phase("Crossing")
	await walk_to(door.position+Vector2(0,2 if door.inside else -2),0.2)
	set_phase("FadeOut")
	await opacity(1)
	set_phase("Swap")
	if not home.switch_room(destination,Vector2.ZERO,true):
		home.switch_room(source,Vector2(stable_snapshot.position[0],stable_snapshot.position[1]))
		await opacity(0)
		busy=false
		world.player.z_index=0
		world.hud.show_toast("房间暂时无法进入，已回到门前。",6)
		set_phase("Idle")
		if exit_pending: world.request_exit()
		return
	door=home.active_door()
	door.set_pose(2)
	world.player.position=door.position+Vector2(0,-2 if door.inside else 2)
	set_phase("FadeIn")
	await opacity(0)
	set_phase("Arrival")
	await walk_to(door.approach,0.2)
	set_phase("Closing")
	await animate_door(door,false)
	world.player.velocity=Vector2.ZERO
	world.player.z_index=0
	stable_snapshot=world.foraging.to_data(world.player.position)
	# Save the stable destination before accepting held input again.
	busy=false
	world.save_progress()
	busy=true
	set_phase("AwaitRelease")
	while held_input() and not exit_pending: await get_tree().process_frame
	world.release_input=false
	busy=false
	set_phase("Idle")
	if exit_pending: world.request_exit()
func held_input() -> bool:
	for action in ["inspect","left","right","up","down","reset","journal"]:
		if Input.is_action_pressed(action): return true
	return false
```

### house_session.gd

```gdscript
extends Node
const Room=preload("res://scripts/room_data.gd")
var world
var outdoor: Node2D
var interior
var exterior_door
var transition
func _ready() -> void:
	outdoor=Node2D.new()
	outdoor.name="HarborExterior"
	world.add_child(outdoor)
	world.move_child(outdoor,0)
	# Preserve the existing sort layer and its references for outdoor regressions.
	for child in world.get_children():
		if child==world.sort_layer or child.name=="Terrain" or child is StaticBody2D:
			child.reparent(outdoor)
	var house=world.sort_layer.get_node("House")
	house.get_child(0).hide()
	house.set_script(preload("res://scripts/house_exterior.gd"))
	house.z_index=0
	house._ready()
	exterior_door=Node2D.new()
	exterior_door.set_script(preload("res://scripts/interactive_door.gd"))
	exterior_door.name="ExteriorDoor"
	exterior_door.position=Room.OUTSIDE_DOOR
	exterior_door.approach=Room.OUTSIDE_APPROACH
	exterior_door.z_index=0
	world.sort_layer.add_child(exterior_door)
	interior=Node2D.new()
	interior.set_script(preload("res://scripts/house_interior.gd"))
	interior.name="HouseInterior"
	world.add_child(interior)
	interior.hide()
	interior.process_mode=Node.PROCESS_MODE_DISABLED
	transition=Node.new()
	transition.set_script(preload("res://scripts/room_transition.gd"))
	transition.home=self
	add_child(transition)
func active_door():
	return interior.door if world.foraging.location=="house" else exterior_door
func switch_room(location: String,point: Vector2,transient: bool=false) -> bool:
	if location not in ["harbor","house"]: return false
	var inside:=location=="house"
	if inside and not is_instance_valid(interior): return false
	# Reparent before disabling the source so the one persistent player stays live.
	world.player.reparent(interior.sort_layer if inside else world.sort_layer)
	outdoor.visible=not inside
	outdoor.process_mode=Node.PROCESS_MODE_DISABLED if inside else Node.PROCESS_MODE_INHERIT
	if is_instance_valid(interior):
		interior.visible=inside
		interior.process_mode=Node.PROCESS_MODE_INHERIT if inside else Node.PROCESS_MODE_DISABLED
	world.foraging.location=location
	exterior_door.set_pose(0)
	if is_instance_valid(interior): interior.door.set_pose(0)
	world.player.position=point if transient else safe_position(location,point)
	world.player.velocity=Vector2.ZERO
	world.hud.dismiss()
	world.hud.region.text="旧屋 / 海风入窗" if inside else "晴 / 渔港的一天"
	world.hud.controls.text="WASD / 方向键 移动   E 查看 / 开门   B / Tab 手账   R 回入口" if inside else "WASD / 方向键 移动   E 拾取 / 查看   B / Tab 手账   R 回路口"
	world.get_node("WorldCamera").update_position()
	world.get_node("WorldCamera").force_update_scroll()
	world.refresh_pickups()
	return true
func safe_position(location: String,point: Vector2) -> Vector2:
	var inside:=location=="house"
	var bounds: Rect2=Room.FLOOR if inside else world.data.WORLD_BOUNDS
	var fallback: Vector2=Room.SPAWN if inside else world.data.SPAWN
	if not bounds.grow(-6).has_point(point): return fallback
	var blocks: Array[Rect2]=Room.blockers() if inside else world.data.blockers()
	for rect in blocks:
		if rect.grow(6).has_point(point): return fallback
	var door_position: Vector2=Room.DOOR if inside else Room.OUTSIDE_DOOR
	if Rect2(door_position-Vector2(24,10),Vector2(48,20)).has_point(point): return fallback
	return point
func storage_point() -> Vector2:
	return Room.STORAGE+Vector2(0,24) if world.foraging.location=="house" else world.STORAGE_POINT
func reset_player() -> void:
	world.player.position=Room.SPAWN if world.foraging.location=="house" else world.data.SPAWN
	world.player.velocity=Vector2.ZERO
	world.hud.dismiss()
```

- [x] 运行上述 house 测试；独立检查旧场景回归，不删除旧覆盖。

## Task 4: 现有入口接入

**Files:** 以下每个代码块为 godot2d/scripts/ 对应文件的完整实现，绝对工程根为 /Users/wyq/Documents/code/coastal-harbor-game。

**Interfaces:** Harbor 持有 home，Player 显式持有 world；Camera 按 foraging.location 切换室内固定镜头。只修改接入所需职责，库存逻辑保持不变。

- [x] 实现以下完整代码。

### harbor.gd

```gdscript
extends Node2D

const data = preload("res://scripts/harbor_data.gd")
const Art = preload("res://scripts/atlas.gd")
var player: CharacterBody2D
var sort_layer: Node2D
var hud: CanvasLayer
var foraging = preload("res://scripts/foraging_state.gd").new()
var pickup_nodes: Dictionary = {}
const STORAGE_POINT = Vector2(274,194)
var journal
var save_service
var settings
var persistence_enabled := false
var session_started := false
var release_input := false
var save_message := ""
var home

func _ready() -> void:
	# Size the native window once per launch, preserving manual resizing thereafter.
	var window := get_window()
	if DisplayServer.get_name() != "headless" and not window.has_meta("startup_window_sized"):
		var available := DisplayServer.screen_get_usable_rect(window.current_screen)
		window.mode = Window.MODE_WINDOWED
		window.size = Vector2i((Vector2(available.size)*sqrt(0.5)).round())
		window.position = available.position+(available.size-window.size)/2
		window.set_meta("startup_window_sized",true)
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	configure_input()
	var terrain := Node2D.new()
	terrain.name = "Terrain"
	terrain.set_script(load("res://scripts/terrain.gd"))
	add_child(terrain)
	var water_detail := Node2D.new()
	water_detail.name = "WaterDetail"
	water_detail.set_script(load("res://scripts/water_detail.gd"))
	terrain.add_child(water_detail)
	sort_layer = Node2D.new()
	sort_layer.name = "DepthSortedObjects"
	sort_layer.y_sort_enabled = true
	add_child(sort_layer)
	add_prop("house",Vector2(174,190),168)
	add_prop("market",Vector2(442,218),144)
	add_prop("garden",Vector2(126,224),78)
	add_prop("garden",Vector2(212,224),78)
	add_prop("crates",Vector2(523,233),29)
	add_prop("boat",Vector2(532,370),114)
	var tree_variants := [0,1,0,2,3]
	for i in range(data.TREES.size()):
		var tree := Node2D.new()
		tree.name = "CoastalTree%d" % i
		tree.position = data.TREES[i]
		tree.set_meta("tree_variant",tree_variants[i])
		var sprite := Sprite2D.new()
		sprite.texture = load("res://assets/tree-set-v4/tree-%d.png" % tree_variants[i])
		# Native-size 96px canvas, with trunk anchor (48,94).
		sprite.position = Vector2(0,-46)
		tree.add_child(sprite)
		sort_layer.add_child(tree)
	for rectangle in data.blockers():
		var body := StaticBody2D.new()
		body.position = rectangle.get_center()
		var collision := CollisionShape2D.new()
		var shape := RectangleShape2D.new()
		shape.size = rectangle.size
		collision.shape = shape
		body.add_child(collision)
		add_child(body)
	player = CharacterBody2D.new()
	player.set_script(load("res://scripts/player.gd"))
	player.world=self
	player.name = "Returnee"
	player.position = data.SPAWN
	sort_layer.add_child(player)
	var camera := Camera2D.new()
	camera.name = "WorldCamera"
	camera.set_script(preload("res://scripts/world_camera.gd"))
	camera.target = player
	add_child(camera)
	hud = CanvasLayer.new()
	hud.set_script(load("res://scripts/hud.gd"))
	add_child(hud)
	for entry in data.pickups():
		var pickup := Node2D.new()
		pickup.set_script(preload("res://scripts/forage_pickup.gd"))
		pickup.kind = entry.kind
		pickup.position = entry.point
		pickup.name = entry.id
		sort_layer.add_child(pickup)
		pickup_nodes[entry.id] = pickup
	hud.show_toast("低潮赶海：沿台阶下沙滩。暂不保存，重开重置。",8.0)
	var args := OS.get_cmdline_user_args()
	var old_verification: bool = get_meta("skip_verification",false)
	for arg in args:
		if arg.begins_with("--verify-") and arg not in ["--verify-journal","--verify-house"]:
			old_verification = true
	persistence_enabled = (DisplayServer.get_name() != "headless" and not old_verification) or get_meta("journal_test",false) or args.has("--verify-journal") or args.has("--verify-house")
	var save_directory: String = get_meta("save_directory","user://coastal-progress")
	if args.has("--verify-journal") or args.has("--verify-house"):
		save_directory = "/private/tmp/coastal-export-journal-"+str(Time.get_unix_time_from_system())
		for arg in args:
			if arg.begins_with("--test-save-directory=/private/tmp/coastal-"):
				save_directory = arg.trim_prefix("--test-save-directory=")
	save_service = preload("res://scripts/save_service.gd").new(save_directory)
	settings = preload("res://scripts/settings_service.gd").new(save_service.directory)
	journal = CanvasLayer.new()
	journal.set_script(preload("res://scripts/ui/journal.gd"))
	journal.world = self
	add_child(journal)
	hud.bag_requested.connect(func():
		if persistence_enabled and session_started and not hud.panel.visible and journal.mode == "" and not home.transition.busy:
			journal.selected_side = "bag"
			journal.selected_index = 0
			journal.show_page("bag"))
	if persistence_enabled:
		add_prop("crates",STORAGE_POINT,22)
		get_tree().auto_accept_quit = false
		hud.controls.text = "WASD / 方向键 移动   E 拾取 / 查看   B / Tab 手账   R 回路口"
		hud.show_toast("沿台阶赶海；旧屋东侧木箱可存放收获。",8)
		journal.show_page("title")
	home=Node.new()
	home.set_script(preload("res://scripts/house_session.gd"))
	home.world=self
	add_child(home)
	if args.has("--verify-house"):
		var runner:=Node.new()
		runner.set_script(load("res://tests/house_driver.gd"))
		add_child(runner)
		return
	if args.has("--verify-journal"):
		var runner := Node.new()
		runner.set_script(load("res://tests/journal_driver.gd"))
		add_child(runner)
		return
	# Explicit opt-in integration harness also runs inside an exported app.
	if get_meta("skip_verification",false):
		return
	if OS.get_cmdline_user_args().has("--verify-foraging"):
		var runner := Node.new()
		runner.set_script(load("res://tests/foraging_driver.gd"))
		add_child(runner)
	elif OS.get_cmdline_user_args().has("--verify-interaction"):
		var runner := Node.new()
		runner.set_script(load("res://tests/interaction_driver.gd"))
		add_child(runner)
	elif OS.get_cmdline_user_args().has("--verify-route"):
		var runner := Node.new()
		runner.set_script(load("res://tests/route_driver.gd"))
		add_child(runner)
	elif OS.get_cmdline_user_args().has("--verify-environment"):
		var runner := Node.new()
		runner.set_script(load("res://tests/verify_environment_render.gd"))
		add_child(runner)

func add_prop(id: String, feet: Vector2, width: float) -> void:
	var root := Node2D.new()
	root.name = id.capitalize()
	root.position = feet
	var sprite := Sprite2D.new()
	sprite.texture = Art.region(id)
	var factor := width / sprite.texture.get_width()
	sprite.scale = Vector2.ONE * factor
	sprite.position = Vector2(0,-sprite.texture.get_height()*factor/2)
	root.add_child(sprite)
	sort_layer.add_child(root)

func configure_input() -> void:
	var keys = {"left":[KEY_A,KEY_LEFT],"right":[KEY_D,KEY_RIGHT],"up":[KEY_W,KEY_UP],"down":[KEY_S,KEY_DOWN],"inspect":[KEY_E],"reset":[KEY_R],"journal":[KEY_B,KEY_TAB]}
	for action in keys:
		if InputMap.has_action(action):
			continue
		InputMap.add_action(action)
		for key in keys[action]:
			var event := InputEventKey.new()
			event.physical_keycode = key
			InputMap.action_add_event(action,event)

func nearest_location(point: Vector2) -> Dictionary:
	var nearest: Dictionary = {}
	var distance := 28.0
	var locations: Array=preload("res://scripts/room_data.gd").locations() if foraging.location=="house" else data.locations()
	for location in locations:
		var gap := point.distance_to(location.point)
		if gap < distance:
			distance = gap
			nearest = location
	return nearest

func nearest_pickup(point: Vector2) -> Dictionary:
	if foraging.location=="house" or not data.BEACH.has_point(point):
		return {}
	var nearest: Dictionary = {}
	var distance := 24.0
	for entry in data.pickups():
		if foraging.collected.has(entry.id):
			continue
		var gap := point.distance_to(entry.point)
		if gap <= 24.0 and (nearest.is_empty() or gap < distance):
			distance = gap
			nearest = entry
	return nearest

func _process(_delta: float) -> void:
	if home != null and home.transition.busy: return
	if release_input:
		for action in ["inspect","reset","journal","left","right","up","down"]:
			if Input.is_action_pressed(action):
				return
		release_input = false
		return
	if persistence_enabled and Input.is_action_just_pressed("journal") and not hud.panel.visible:
		journal.show_page(journal.last_page)
		return
	if Input.is_action_just_pressed("inspect"):
		if hud.panel.visible:
			hud.dismiss()
		elif persistence_enabled and home.active_door().can_interact(player.position):
			home.transition.begin()
			return
		elif persistence_enabled and player.position.distance_to(home.storage_point()) <= 28:
			journal.selected_side = "bag"
			journal.selected_index = 0
			journal.show_page("storage")
			return
		else:
			var target := nearest_pickup(player.position)
			if not target.is_empty():
				if foraging.collect(target.id,target.kind):
					pickup_nodes[target.id].hide()
					hud.show_toast(data.ITEM_NAMES[target.kind]+" +1")
					save_progress()
				else:
					hud.show_toast("背包已满，物品留在原地。")
			else:
				hud.show_location(nearest_location(player.position))
	if Input.is_action_just_pressed("reset"):
		home.reset_player()
	hud.update_location(nearest_location(player.position))
	var target := nearest_pickup(player.position)
	for id in pickup_nodes:
		pickup_nodes[id].highlighted = not hud.panel.visible and target.get("id","") == id
	if not target.is_empty():
		hud.prompt.text = "[ E ] 拾取" + data.ITEM_NAMES[target.kind]
	elif persistence_enabled and home.active_door().can_interact(player.position):
		hud.prompt.text="[ E ] 走出小屋" if foraging.location=="house" else "[ E ] 进入小屋"
	elif persistence_enabled and player.position.distance_to(home.storage_point()) <= 28:
		hud.prompt.text = "[ E ] 打开旧屋储物箱"
	elif foraging.location=="house" and nearest_location(player.position).is_empty():
		hud.prompt.text="回到熟悉的屋子；床、厨房和旧照片可查看。"
	elif foraging.collected.size() == data.pickups().size() and nearest_location(player.position).is_empty():
		hud.prompt.text = "今日赶海收获已集齐；市集交易将在后续版本开放。"

func refresh_pickups() -> void:
	for id in pickup_nodes:
		pickup_nodes[id].visible = not foraging.collected.has(id)

func _set_state(value) -> void:
	foraging = value
	refresh_pickups()

func start_new_game(chosen_name: String) -> bool:
	var state = preload("res://scripts/player_state.gd").new()
	state.player_name = state.clean_name(chosen_name)
	if persistence_enabled and not save_service.write_save(state.to_data(data.SPAWN)):
		journal.note = save_service.last_error
		journal.render()
		return false
	_set_state(state)
	home.switch_room("harbor",data.SPAWN)
	session_started = true
	journal.dismiss()
	hud.show_toast("欢迎回来，"+foraging.player_name+"。E 赶海，B 打开手账。",8)
	return true

func continue_game() -> bool:
	var result: Dictionary = save_service.read_save()
	if not result.ok:
		journal.note = result.message
		journal.render()
		return false
	var state = preload("res://scripts/player_state.gd").new()
	if not state.restore(result.data): return false
	_set_state(state)
	var position := Vector2(result.data.position[0],result.data.position[1])
	var safe: bool=home.safe_position(state.location,position)==position
	home.switch_room(state.location,position)
	session_started = true
	journal.dismiss()
	hud.show_toast(result.message if result.message != "" else ("已继续上次的生活。" if safe else "已回到安全路口。"),8)
	return true

func save_progress() -> bool:
	if not persistence_enabled or not session_started: return true
	var snapshot: Dictionary=home.transition.stable_snapshot if home.transition.busy else foraging.to_data(home.safe_position(foraging.location,player.position))
	var ok: bool = save_service.write_save(snapshot)
	save_message = "进度已保存。" if ok else save_service.last_error
	if not ok:
		hud.show_toast(save_message,10)
		journal.note = save_message
	return ok

func return_to_title() -> void:
	if not save_progress():
		show_save_error(false)
		return
	session_started = false
	journal.from_title = false
	journal.show_page("title")

func request_exit() -> void:
	if home != null and home.transition.busy:
		home.transition.exit_pending=true
		return
	if save_progress():
		get_tree().quit()
	else:
		show_save_error(true)

func show_save_error(exit_game: bool) -> void:
	if journal.mode == "": journal.show_page("settings")
	journal.show_save_failure(save_service.last_error,exit_game)

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST and persistence_enabled:
		request_exit()
```

### player.gd

```gdscript
extends CharacterBody2D

const Art = preload("res://scripts/atlas.gd")
const SPEED = 72.0
var sprite: AnimatedSprite2D
var walking := false
var facing := "south"
var world: Node

func _ready() -> void:
	motion_mode = CharacterBody2D.MOTION_MODE_FLOATING
	var shape := CollisionShape2D.new()
	var rectangle := RectangleShape2D.new()
	rectangle.size = Vector2(10,6)
	shape.shape = rectangle
	add_child(shape)
	sprite = AnimatedSprite2D.new()
	sprite.sprite_frames = Art.player_frames()
	var frame_size: float = sprite.sprite_frames.get_frame_texture("south",0).get_width()
	sprite.scale = Vector2.ONE * 48.0 / frame_size
	sprite.position = Vector2(0,-22)
	sprite.animation = facing
	add_child(sprite)
	queue_redraw()

func _draw() -> void:
	draw_rect(Rect2(-6,-3,12,4),Color(0.08,0.22,0.22,0.24))

func _physics_process(_delta: float) -> void:
	if is_instance_valid(world) and world.get("home") != null and world.home.transition.busy:
		velocity=Vector2.ZERO
		return
	if is_instance_valid(world) and world.get("release_input") == true:
		velocity = Vector2.ZERO
		sprite.stop()
		return
	var direction := Input.get_vector("left","right","up","down")
	if direction != Vector2.ZERO:
		if abs(direction.x) > abs(direction.y):
			facing = "east" if direction.x > 0 else "west"
		else:
			facing = "south" if direction.y > 0 else "north"
	velocity = direction * SPEED
	move_and_slide()
	walking = get_real_velocity().length() > 2.0
	if walking:
		sprite.play(facing)
	else:
		sprite.stop()
		sprite.animation = facing
		sprite.frame = 0
```

### world_camera.gd

```gdscript
extends Camera2D

const Data = preload("res://scripts/harbor_data.gd")
var target: Node2D

func _ready() -> void:
	zoom = Vector2(2,2)
	position_smoothing_enabled = false
	get_viewport().size_changed.connect(update_position)
	update_position()
	reset_smoothing()
	force_update_scroll()

func _process(_delta: float) -> void:
	update_position()

func update_position() -> void:
	if not is_instance_valid(target):
		return
	if target.get("world") != null and target.world.foraging.location=="house":
		position=Vector2(320,200)
		return
	var half_view := get_viewport_rect().size / zoom / 2.0
	var bounds: Rect2 = Data.WORLD_BOUNDS
	var desired := target.position + Vector2(0,-40)
	for axis in range(2):
		if bounds.size[axis] <= half_view[axis]*2.0:
			desired[axis] = bounds.get_center()[axis]
		else:
			desired[axis] = clampf(desired[axis],bounds.position[axis]+half_view[axis],bounds.end[axis]-half_view[axis])
	position = desired.round()
```

### harbor_data.gd

```gdscript
extends RefCounted

const SPAWN = Vector2(330,250)
const WORLD_BOUNDS = Rect2(0,0,640,416)
const BEACH = Rect2(224,317,144,51)
const ITEM_NAMES = {"clam":"蛤蜊", "snail":"海螺", "kelp":"海带"}

static func pickups() -> Array[Dictionary]:
	return [
		{"id":"clam_a", "kind":"clam", "point":Vector2(244,330)},
		{"id":"snail_a", "kind":"snail", "point":Vector2(294,330)},
		{"id":"kelp_a", "kind":"kelp", "point":Vector2(344,330)},
		{"id":"clam_b", "kind":"clam", "point":Vector2(244,353)},
		{"id":"snail_b", "kind":"snail", "point":Vector2(294,353)},
		{"id":"kelp_b", "kind":"kelp", "point":Vector2(344,353)}
	]
const TREES = [Vector2(46,128), Vector2(308,110), Vector2(568,184), Vector2(614,114), Vector2(40,225)]

static func blockers() -> Array[Rect2]:
	var out: Array[Rect2] = [
		Rect2(-32,-32,704,64), Rect2(-32,0,48,448), Rect2(624,0,48,448),
		Rect2(92,126,104,60),Rect2(222,126,34,60),Rect2(196,126,26,8), Rect2(378,191,128,27),
		Rect2(88,201,76,23), Rect2(174,201,76,23), Rect2(510,217,23,16)
	]
	for tree in TREES:
		out.append(Rect2(tree - Vector2(5,5), Vector2(10,8)))
	# The sea is blocked except the pier and the dry portion of tidal steps.
	out.append(Rect2(0,272,272,45))
	out.append(Rect2(0,317,224,131))
	out.append(Rect2(320,272,88,45))
	out.append(Rect2(368,317,40,131))
	out.append(Rect2(472,272,168,176))
	out.append(Rect2(224,368,144,80))
	out.append(Rect2(408,392,64,56))
	return out

static func locations() -> Array[Dictionary]:
	return [
		{"id":"house", "point":Vector2(209,194), "title":"祖辈的旧屋", "body":"青绿门廊还留着旧船板的纹路。\n靠近门口按 E 开门，回家歇一歇。"},
		{"id":"garden", "point":Vector2(168,234), "title":"门前小菜园", "body":"两畦蔬菜挨着海风生长。\n本版可查看场景，种植和收获尚未开放。"},
		{"id":"market", "point":Vector2(442,236), "title":"补帆海鲜摊", "body":"旧帆布又缝上了一块新的补丁。\n鱼摊陈列已就位，交易系统尚未开放。"},
		{"id":"pier", "point":Vector2(440,364), "title":"归航的小码头", "body":"浪花轻拍木桩，渔船停在岸旁。\n沿着台阶看看潮位，今天不必急着出海。"},
		{"id":"tide", "point":Vector2(296,302), "title":"潮汐台阶", "body":"现在是低潮，沿台阶走下沙滩。\n靠近海产按E拾取；本版暂不模拟涨落潮。"}
	]
```

- [x] 运行上述 house 测试；独立检查旧场景回归，不删除旧覆盖。

## Task 5: 回归、实机与交付

- [x] 跑完 test_item_catalog、test_inventory_container、test_inventory_operations、test_save_state、test_house_save、test_foraging、test_interaction、test_world、test_tree_set、test_environment、test_display、test_journal、test_house。分别核对 passed 和脚本日志，而非仅看进程退出码。
- [x] 使用导出应用的 --verify-house --record-house，确认实际关键帧与房间截图。
- [x] 同一临时存档执行 --verify-house --resume-check；独立临时档执行 --verify-house --exit-check。
- [x] 使用导出应用 --verify-journal 检查背包、仓储、缩放、全屏恢复与默认窗口面积。
- [x] 生成动画 GIF 与 MP4，校验压缩包 CRC、签名、源码逐文件一致性，归档旧版后替换最新交付。

发布指令：`/Applications/Godot.app/Contents/MacOS/Godot --headless --log-file /private/tmp/coastal-v052-export.log --path godot2d --export-release macOS`。版本 v0.5.2，输出 builds/godot2d-v0.5.2/CoastalHarbor2D-v0.5.2-macOS.zip。

计划自查：动画顺序、相互独立职责、数据接口、旧档及失败保护均映射到规格；像素素材的实现路径变为原生绘制脚本，源图无需破坏性改写。最终验收结果单独记录，不由本计划中的实现代码推断已通过。
