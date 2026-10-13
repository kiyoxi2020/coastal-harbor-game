extends RefCounted
const FLOOR := Rect2(80,64,480,288)
const SPAWN := Vector2(320,300)
const DOOR := Vector2(320,352)
const STORAGE := Vector2(448,288)
const OUTSIDE_APPROACH := Vector2(209,194)
const OUTSIDE_DOOR := Vector2(209,165)

static func furniture() -> Array[Dictionary]:
	return [
		{"id":"bed","rect":Rect2(128,128,48,80)},
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
