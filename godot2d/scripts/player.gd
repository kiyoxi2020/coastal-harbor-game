extends CharacterBody2D

const Art = preload("res://scripts/atlas.gd")
const SPEED = 72.0
var sprite: AnimatedSprite2D
var walking := false
var facing := "south"
var world: Node
var doorway_hidden := 0.0
var doorway_material: ShaderMaterial

func _ready() -> void:
	motion_mode = CharacterBody2D.MOTION_MODE_FLOATING
	var shape := CollisionShape2D.new()
	var rectangle := RectangleShape2D.new()
	rectangle.size = Vector2(10,6)
	shape.shape = rectangle
	add_child(shape)
	sprite = AnimatedSprite2D.new()
	sprite.sprite_frames = Art.player_frames()
	var frame_size: float = sprite.sprite_frames.get_frame_texture("south",0).get_width()
	sprite.scale = Vector2.ONE * 48.0 / frame_size
	sprite.position = Vector2(0,-22)
	sprite.animation = facing
	add_child(sprite)
	doorway_material=ShaderMaterial.new()
	doorway_material.shader=preload("res://scripts/doorway_clip.gdshader")
	doorway_material.set_shader_parameter("frame_height",float(sprite.sprite_frames.get_frame_texture("south",0).get_height()))
	sprite.material=doorway_material
	queue_redraw()

func set_doorway_hidden(value: float) -> void:
	doorway_hidden=clampf(value,0,1)
	# The visual occupies the aperture plane, below the fixed foreground jamb (2).
	# Physics/root sorting stays untouched; this also avoids aperture-darkness overdraw.
	sprite.z_index=1
	doorway_material.set_shader_parameter("hidden_fraction",doorway_hidden)
	queue_redraw()

func reset_doorway_visual() -> void:
	set_doorway_hidden(0)
	sprite.z_index=0
	modulate=Color.WHITE
	sprite.modulate=Color.WHITE
	visible=true
	z_index=0

func _draw() -> void:
	if doorway_hidden==0:
		draw_rect(Rect2(-6,-3,12,4),Color(0.08,0.22,0.22,0.24))

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
