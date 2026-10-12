extends RefCounted

const SPAWN = Vector2(330,250)
const TREES = [Vector2(46,128), Vector2(308,110), Vector2(568,184), Vector2(614,114), Vector2(40,225)]

static func blockers() -> Array[Rect2]:
	var out: Array[Rect2] = [
		Rect2(-32,-32,704,64), Rect2(-32,0,48,448), Rect2(624,0,48,448),
		Rect2(92,126,164,60), Rect2(378,191,128,27),
		Rect2(88,201,76,23), Rect2(174,201,76,23), Rect2(510,217,23,16)
	]
	for tree in TREES:
		out.append(Rect2(tree - Vector2(5,5), Vector2(10,8)))
	# The sea is blocked except the pier and the dry portion of tidal steps.
	out.append(Rect2(0,272,272,176))
	out.append(Rect2(320,272,88,176))
	out.append(Rect2(472,272,168,176))
	out.append(Rect2(272,320,48,128))
	out.append(Rect2(408,392,64,56))
	return out

static func locations() -> Array[Dictionary]:
	return [
		{"id":"house", "point":Vector2(226,194), "title":"祖辈的旧屋", "body":"青绿门廊还留着旧船板的纹路。\n先熟悉这座小渔港吧，屋内暂未开放。"},
		{"id":"garden", "point":Vector2(168,234), "title":"门前小菜园", "body":"两畦蔬菜挨着海风生长。\n本版可查看场景，种植和收获尚未开放。"},
		{"id":"market", "point":Vector2(442,236), "title":"补帆海鲜摊", "body":"旧帆布又缝上了一块新的补丁。\n鱼摊陈列已就位，交易系统尚未开放。"},
		{"id":"pier", "point":Vector2(440,364), "title":"归航的小码头", "body":"浪花轻拍木桩，渔船停在岸旁。\n沿着台阶看看潮位，今天不必急着出海。"},
		{"id":"tide", "point":Vector2(296,302), "title":"潮汐台阶", "body":"红白刻度杆记录海水来过的高度。\n这里是静态观景点，暂不模拟涨落潮。"}
	]
