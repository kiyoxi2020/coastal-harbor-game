extends RefCounted
const FLOOR := Rect2(176,112,288,208)
const SPAWN := Vector2(320,288)
const DOOR := Vector2(320,320)
const ENTRANCE_NORMAL := Vector2.UP
const OUTSIDE_ENTRANCE_NORMAL := Vector2.DOWN
const STORAGE := Vector2(416,282)
const OUTSIDE_APPROACH := Vector2(209,194)
const OUTSIDE_DOOR := Vector2(209,165)

static func furniture() -> Array[Dictionary]:
	return [
		{"id":"bed","rect":Rect2(192,144,48,80),"base":Rect2(192,144,48,80)},
		{"id":"nightstand","rect":Rect2(248,126,24,42),"base":Rect2(250,157,20,11)},
		{"id":"kitchen","rect":Rect2(360,128,80,48),"base":Rect2(362,160,76,16)},
		{"id":"table","rect":Rect2(208,258,48,38),"base":Rect2(212,285,40,11)},
		{"id":"chair","rect":Rect2(184,263,18,29),"base":Rect2(187,284,12,8)},
		{"id":"chest","rect":Rect2(400,264,32,24),"base":Rect2(402,279,28,9)},
		{"id":"shelf","rect":Rect2(256,90,40,22)},
		{"id":"photo","rect":Rect2(266,73,20,18)},
		{"id":"window_left","art":"window","rect":Rect2(184,72,48,42)},
		{"id":"window_right","art":"window","rect":Rect2(408,72,48,42)},
		{"id":"plant","rect":Rect2(436,272,24,40),"base":Rect2(442,303,12,9)}]

static func blockers() -> Array[Rect2]:
	var result: Array[Rect2]=[
		Rect2(160,96,320,32),
		Rect2(160,112,16,224),Rect2(464,112,16,224),
		Rect2(176,320,124,16),Rect2(340,320,124,16)]
	for item in furniture():
		if item.has("base"): result.append(item.base)
	return result

static func locations() -> Array[Dictionary]:
	return [
		{"id":"bed","point":Vector2(216,240),"title":"祖辈留下的床","body":"洗晒过的被子还带着阳光的味道。\n休息换日将在后续版本开放。"},
		{"id":"kitchen","point":Vector2(400,192),"title":"旧屋的小厨房","body":"旧瓷碗与铜壶已经摆好。\n料理功能尚未开放。"},
		{"id":"photo","point":Vector2(280,142),"title":"一张旧合照","body":"照片里的人站在热闹的渔港前。\n你把它放回了原来的位置。"}]
