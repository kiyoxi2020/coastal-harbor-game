extends Node2D
# All actions use the same AnimatedSprite2D as walking and the door mask.
var active := false
var action := ""
var actor: CharacterBody2D
var direction := "south"
var expected_animation := ""
func _ready() -> void:
	actor=get_parent()
	actor.get_node("AnimatedSprite2D").animation_finished.connect(_animation_finished)
func _direction_for(target: Vector2) -> String:
	var offset: Vector2=target-actor.global_position
	if offset.length()>0.1:
		return ("east" if offset.x>0 else "west") if abs(offset.x)>abs(offset.y) else ("south" if offset.y>0 else "north")
	return actor.facing
func can_begin(kind: String, target: Vector2) -> bool:
	if active or kind not in ["hoe","water","harvest"] or not is_instance_valid(actor): return false
	var animation := kind+"_"+_direction_for(target)
	var frames: SpriteFrames = actor.sprite.sprite_frames
	if frames == null or not frames.has_animation(animation) or frames.get_frame_count(animation) == 0 or frames.get_animation_loop(animation): return false
	if frames.get_animation_speed(animation) <= 0: return false
	for frame in range(frames.get_frame_count(animation)):
		if frames.get_frame_texture(animation,frame) == null or frames.get_frame_duration(animation,frame) <= 0: return false
	return true
func begin(kind: String, target: Vector2) -> void:
	if not can_begin(kind,target): return
	direction=_direction_for(target)
	var animation := kind+"_"+direction
	actor.facing=direction
	action=kind
	expected_animation=animation
	active=true
	actor.velocity=Vector2.ZERO
	actor.walking=false
	actor.running=false
	actor.sprite.stop()
	actor.sprite.play(expected_animation)
	actor.sprite.set_frame_and_progress(0,0.0)
func _animation_finished() -> void:
	if active and actor.sprite.animation==expected_animation: finish()
func finish() -> void:
	if not active: return
	active=false
	action=""
	expected_animation=""
	if is_instance_valid(actor):
		actor.play_idle()
