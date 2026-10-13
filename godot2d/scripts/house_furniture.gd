extends Node2D
const CottageArt=preload("res://scripts/cottage_art.gd")
var kind := "bed"
var extent := Vector2(80,112)
var pilot_texture: Texture2D
var pilot_pivot := Vector2.ZERO
func _ready() -> void:
	if kind=="bed":
		var data:=CottageArt.entry("bed")
		pilot_texture=CottageArt.texture_for("bed")
		if data.has("pivot"): pilot_pivot=Vector2(data.pivot[0],data.pivot[1])
		texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
func block(x: float,y: float,w: float,h: float,c: String) -> void:
	draw_rect(Rect2(x,y,w,h),Color(c))
func _draw() -> void:
	if kind=="bed" and pilot_texture:
		draw_texture(pilot_texture,-pilot_pivot)
		return
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
