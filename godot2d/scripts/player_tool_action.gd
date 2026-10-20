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
func begin(kind: String, target: Vector2) -> void:
	if active or kind not in ["hoe","water","harvest"]: return
	var offset: Vector2=target-actor.global_position
	if offset.length()>0.1:
		direction=("east" if offset.x>0 else "west") if abs(offset.x)>abs(offset.y) else ("south" if offset.y>0 else "north")
	else: direction=actor.facing
	actor.facing=direction
	action=kind
	expected_animation=kind+"_"+direction
	active=true
	actor.sprite.play(expected_animation)
func _animation_finished() -> void:
	if active and actor.sprite.animation==expected_animation: finish()
func finish() -> void:
	active=false
	if is_instance_valid(actor):
		actor.sprite.stop()
		actor.sprite.animation=actor.facing
		actor.sprite.frame=0
