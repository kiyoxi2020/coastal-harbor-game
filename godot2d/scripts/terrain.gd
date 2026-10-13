extends Node2D

const GRASS = preload("res://assets/environment-v2/grass.png")
const SHALLOW = preload("res://assets/environment-v2/shallow.png")
const DEEP = preload("res://assets/environment-v2/deep.png")
const STONE = preload("res://assets/environment-v2/stone.png")

func _ready() -> void:
	texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED

func _draw() -> void:
	draw_texture_rect(DEEP,Rect2(0,272,640,144),true)
	# Continuous depth bands; offset source sampling avoids a tile checkerboard.
	for row in range(18):
		var opacity := clampf(1.0-float(row)/17.0,0.0,1.0)*0.8
		draw_texture_rect_region(SHALLOW,Rect2(0,272+row*8,640,8),Rect2(0,row*8,640,8),Color(1,1,1,opacity),false,false)
	draw_rect(Rect2(0,272,640,144),Color(0.16,0.55,0.62,0.28))
	# Submerged rock silhouettes are fixed, low contrast and only at the edges.
	for i in range(12):
		var x := 12+(i*19)%104 if i < 7 else 559+(i*17)%70
		var y := 354+(i*13)%56
		draw_rect(Rect2(x+2,y-2,9+i%5,7),Color(0.10,0.37,0.43,0.22))
		draw_rect(Rect2(x,y,14+i%5,5),Color(0.10,0.37,0.43,0.18))
		draw_rect(Rect2(x+3,y-2,7,1),Color(0.36,0.71,0.67,0.25))
	draw_texture_rect(GRASS,Rect2(0,0,640,272),true)
	draw_rect(Rect2(0,0,640,272),Color(0.53,0.68,0.41,0.32))
	# Rectangular terrain cells are reused, separate from building sprites.
	for y in range(32,272,16):
		for x in range(16,624,16):
			if y >= 224 or (x >= 272 and x < 352) or (x >= 208 and x < 240 and y >= 176):
				stone(Vector2(x,y), (x/16*7+y/16*11)%16)
	# Low-contrast irregular verge: denser at edges, quiet in the path center.
	for i in range(36):
		var x := 20+(i*47)%600
		var y := 223 if i%3 != 0 else 33+(i*29)%177
		if i%3 == 0:
			x = 270 if i%2 == 0 else 353
		draw_rect(Rect2(x,y,4,2),Color("71965d"))
		draw_rect(Rect2(x+1,y-3,1,4),Color("87b26b"))
		draw_rect(Rect2(x+3,y-1,1,3),Color("a6c37b"))
	for at in preload("res://scripts/harbor_data.gd").TREES:
		draw_rect(Rect2(at-Vector2(16,3),Vector2(32,4)),Color(0.25,0.40,0.26,0.20))
		draw_rect(Rect2(at-Vector2(10,5),Vector2(20,8)),Color(0.25,0.40,0.26,0.16))
	# Two-row seawall with openings for the pier and stairs.
	for x in range(0,640,16):
		if (x >= 272 and x < 320) or (x >= 408 and x < 472):
			continue
		draw_rect(Rect2(x,272,16,19),Color("5d8583"))
		draw_rect(Rect2(x+1,273,14,8),Color("abc2b2"))
		draw_rect(Rect2(x+1,283,14,7),Color("8da9a0"))
		draw_rect(Rect2(x,271,16,3),Color("e0dec1"))
		if x%32 == 0:
			draw_rect(Rect2(x+2,292,12,1),Color("c0e8dc"))
		# Salt-worn joints and a restrained damp band at the wall foot.
		draw_rect(Rect2(x+1,288,14,3),Color("527e76"))
		if x%48 == 0:
			draw_rect(Rect2(x+4,287,3,2),Color("749568"))
	# Low-tide pocket: quiet dry sand, damp rim and broken shoreline.
	var beach: Rect2 = preload("res://scripts/harbor_data.gd").BEACH
	draw_rect(beach,Color("bda980"))
	draw_rect(Rect2(228,317,136,45),Color("dfc798"))
	draw_rect(Rect2(232,319,128,37),Color("ebd7ab"))
	for i in range(34):
		var p := Vector2(233+(i*37)%126,322+(i*17)%32)
		draw_rect(Rect2(p,Vector2(2+i%2,1)),Color("cbb58a") if i%3 else Color("f6e6bb"))
	for x in range(225,367,11):
		draw_rect(Rect2(x,366,6,1),Color("e7ead1"))
	# Five dry steps connect the promenade to the low-tide beach.
	for step in range(5):
		draw_rect(Rect2(272,272+step*9,48,9),Color("96aba0"))
		draw_rect(Rect2(273,272+step*9,46,5),Color("d8d9bd"))
		draw_rect(Rect2(273,272+step*9,46,1),Color("f1e8ca"))
	for i in range(8):
		draw_rect(Rect2(260,261+i*6,4,6),Color("dc826b") if i%2==0 else Color("fff0c9"))
		draw_rect(Rect2(264,263+i*6,2,1),Color("385c60"))
	# Pier planks are repeated modules, not painted into the boat.
	draw_rect(Rect2(408,274,64,124),Color("5c7168"))
	for i in range(15):
		draw_rect(Rect2(408,272+i*8,64,7),Color("b68b5c"))
		draw_rect(Rect2(409,272+i*8,62,1),Color("e3bd82"))
		draw_rect(Rect2(414+(i*7)%26,275+i*8,12,1),Color("a27950"))
		for x in [411,468]:
			draw_rect(Rect2(x,274+i*8,1,1),Color("77694c"))
	for y in [280,328,386]:
		for x in [408,467]:
			draw_rect(Rect2(x-3,y-9,7,15),Color("735f46"))
			draw_rect(Rect2(x-4,y-10,9,4),Color("dfbb82"))
			draw_rect(Rect2(x-3,y-1,7,2),Color("f2d7a2"))
	for i in range(18):
		var x := 18+(i*131)%608
		var y := 50+(i*43)%150
		if x > 80 and x < 520:
			continue
		draw_rect(Rect2(x,y,1,4),Color("54865a"))
		draw_rect(Rect2(x-1,y,3,2),Color("eae5ae"))

func stone(point: Vector2, variant: int) -> void:
	draw_texture_rect_region(STONE,Rect2(point,Vector2(16,16)),Rect2((variant%4)*16,(variant/4)*16,16,16))
	if variant == 3 or variant == 11:
		draw_rect(Rect2(point+Vector2(0,11),Vector2(1,4)),Color("8d9d78"))
		draw_rect(Rect2(point+Vector2(1,14),Vector2(3,1)),Color("a6b68b"))
