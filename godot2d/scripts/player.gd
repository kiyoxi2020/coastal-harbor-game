extends CharacterBody2D

const SPEED = 72.0
@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var shadow: Polygon2D = $Shadow
var walking := false
var facing := "south"
var world: Node
var doorway_hidden := 0.0
var doorway_material: ShaderMaterial
var visual_top := 0.0
var visual_bottom := 0.0
var initial_modulate := Color.WHITE
var initial_z_index := 0
var initial_visible := true
var initial_sprite_modulate := Color.WHITE
var initial_sprite_z_index := 0
var initial_shadow_visible := true

func _ready() -> void:
	motion_mode = CharacterBody2D.MOTION_MODE_FLOATING
	doorway_material = sprite.material as ShaderMaterial
	initial_modulate = modulate
	initial_z_index = z_index
	initial_visible = visible
	initial_sprite_modulate = sprite.modulate
	initial_sprite_z_index = sprite.z_index
	initial_shadow_visible = shadow.visible
	# Include every walking frame so fade starts only after the last opaque pixel.
	for direction in ["north", "south"]:
		for frame in range(sprite.sprite_frames.get_frame_count(direction)):
			var texture := sprite.sprite_frames.get_frame_texture(direction, frame)
			var bounds := texture.get_image().get_used_rect()
			visual_top = minf(visual_top, sprite.position.y + (bounds.position.y - texture.get_height() * 0.5) * sprite.scale.y)
			visual_bottom = maxf(visual_bottom, sprite.position.y + (bounds.end.y - texture.get_height() * 0.5) * sprite.scale.y)
	queue_redraw()

func set_doorway_hidden(value: float) -> void:
	doorway_hidden=clampf(value,0,1)
	shadow.visible = initial_shadow_visible and doorway_hidden == 0.0
	# Diagnostic progress only; the shader clips fixed world geometry.

func reset_doorway_visual() -> void:
	set_doorway_hidden(0)
	doorway_material.set_shader_parameter("clip_enabled",false)
	sprite.z_index = initial_sprite_z_index
	modulate = initial_modulate
	sprite.modulate = initial_sprite_modulate
	visible = initial_visible
	z_index = initial_z_index
	shadow.visible = initial_shadow_visible

func _physics_process(_delta: float) -> void:
	if is_instance_valid(world) and world.get("home") != null and world.home.transition.busy:
		velocity=Vector2.ZERO
		return
	if is_instance_valid(world) and world.get("release_input") == true:
		velocity = Vector2.ZERO
		sprite.stop()
		return
	var direction := Input.get_vector("left","right","up","down")
	if direction != Vector2.ZERO:
		if abs(direction.x) > abs(direction.y):
			facing = "east" if direction.x > 0 else "west"
		else:
			facing = "south" if direction.y > 0 else "north"
	velocity = direction * SPEED
	move_and_slide()
	walking = get_real_velocity().length() > 2.0
	if walking:
		sprite.play(facing)
	else:
		sprite.stop()
		sprite.animation = facing
		sprite.frame = 0
