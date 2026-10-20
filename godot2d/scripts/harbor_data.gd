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
const TREES = [Vector2(46,128), Vector2(308,110), Vector2(568,184), Vector2(614,114), Vector2(40,184)]

static func blockers() -> Array[Rect2]:
	var out: Array[Rect2] = [
		Rect2(-32,-32,704,64), Rect2(-32,0,48,448), Rect2(624,0,48,448),
		Rect2(92,126,104,60),Rect2(222,126,34,60),Rect2(196,126,26,8), Rect2(378,191,128,27),
		Rect2(510,217,23,16)
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
		{"id":"garden", "point":Vector2(168,234), "title":"门前小菜园", "body":"两片菜地共16格，可走入田间。\n1–4 选工具，点击或面朝菜格按 E。"},
		{"id":"market", "point":Vector2(442,236), "title":"补帆海鲜摊", "body":"旧帆布又缝上了一块新的补丁。\n靠近按 E 买种子、出售背包里的海产和作物。"},
		{"id":"pier", "point":Vector2(440,364), "title":"归航的小码头", "body":"浪花轻拍木桩，渔船停在岸旁。\n沿着台阶看看潮位，今天不必急着出海。"},
		{"id":"tide", "point":Vector2(296,302), "title":"潮汐台阶", "body":"现在是低潮，沿台阶走下沙滩。\n靠近海产按E拾取；本版暂不模拟涨落潮。"}
	]
