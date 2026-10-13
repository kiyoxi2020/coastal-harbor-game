extends RefCounted
const FLOOR := Rect2(176,112,288,208)
const SPAWN := Vector2(320,160)
const DOOR := Vector2(320,128)
const ENTRANCE_NORMAL := Vector2.DOWN
const STORAGE := Vector2(416,282)
const OUTSIDE_APPROACH := Vector2(209,194)
const OUTSIDE_DOOR := Vector2(209,165)

static func furniture() -> Array[Dictionary]:
	return [
		{"id":"bed","rect":Rect2(192,144,48,80)},
		{"id":"nightstand","rect":Rect2(248,144,24,24)},
		{"id":"kitchen","rect":Rect2(360,136,80,40)},
		{"id":"table","rect":Rect2(208,264,48,32)},
		{"id":"chair","rect":Rect2(184,268,18,24)},
		{"id":"chest","rect":Rect2(400,264,32,24)},
		{"id":"shelf","rect":Rect2(256,96,40,16)},
		{"id":"plant","rect":Rect2(440,288,16,24)}]

static func blockers() -> Array[Rect2]:
	var result: Array[Rect2]=[
		Rect2(160,96,140,32),Rect2(340,96,140,32),
		Rect2(160,112,16,224),Rect2(464,112,16,224),Rect2(176,320,288,16)]
	for item in furniture():
		if item.id!="shelf": result.append(item.rect)
	return result

static func locations() -> Array[Dictionary]:
	return [
		{"id":"bed","point":Vector2(216,240),"title":"祖辈留下的床","body":"洗晒过的被子还带着阳光的味道。\n休息换日将在后续版本开放。"},
		{"id":"kitchen","point":Vector2(400,192),"title":"旧屋的小厨房","body":"旧瓷碗与铜壶已经摆好。\n料理功能尚未开放。"},
		{"id":"photo","point":Vector2(280,142),"title":"一张旧合照","body":"照片里的人站在热闹的渔港前。\n你把它放回了原来的位置。"}]
