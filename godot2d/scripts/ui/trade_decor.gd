@tool
extends Control
# Small pixel decorations stay outside the slots and interactive controls.
func _draw():
	var rope=Color("a17a49")
	var shade=Color("5b4e38")
	for i in range(5):
		var start=Vector2(-20+i*12,-8)
		draw_line(start,start+Vector2(-24,112),shade,4)
		draw_line(start+Vector2(2,0),start+Vector2(-22,112),rope,2)
	for i in range(8):
		var start=Vector2(-38,-8+i*14)
		draw_line(start,start+Vector2(76,0),rope,2)
	for y in [56,100]:
		draw_line(Vector2(924,0),Vector2(924,y),shade,2)
		draw_rect(Rect2(916,y,16,24),shade)
		draw_rect(Rect2(918,y+2,12,10),Color("c76542"))
		draw_rect(Rect2(918,y+12,12,10),Color("fff0cb"))
	for i in range(4):
		draw_rect(Rect2(886+i*8,610-i*4,10,20),shade)
		draw_rect(Rect2(888+i*8,612-i*4,6,14),rope)
