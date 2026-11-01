extends CharacterBody2D

const SPEED = 72.0
const RUN_SPEED = 108.0
var running := false
@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var shadow: Polygon2D = $Shadow
var action_busy: bool:
	get: return $ToolAction.active
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
	# Door movement uses walk and idle; measure both with the scene's actual origin.
	for direction in ["north", "south", "west", "east"]:
		for action in ["idle", "walk"]:
			var animation: String = action + "_" + direction
			if not sprite.sprite_frames.has_animation(animation): continue
			for frame in range(sprite.sprite_frames.get_frame_count(animation)):
				var texture := sprite.sprite_frames.get_frame_texture(animation, frame)
				if texture == null: continue
				var bounds := texture.get_image().get_used_rect()
				var origin := sprite.offset.y - (texture.get_height() * 0.5 if sprite.centered else 0.0)
				var top := sprite.position.y + (bounds.position.y + origin) * sprite.scale.y
				var bottom := sprite.position.y + (bounds.end.y + origin) * sprite.scale.y
				visual_top = minf(visual_top, minf(top, bottom))
				visual_bottom = maxf(visual_bottom, maxf(top, bottom))
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

func play_tool_action(kind: String, target: Vector2) -> void:
	$ToolAction.begin(kind,target)

func can_play_tool_action(kind: String, target: Vector2) -> bool:
	return $ToolAction.can_begin(kind,target)

func play_idle() -> void:
	walking = false
	running = false
	var animation := "idle_" + facing
	if not sprite.sprite_frames.has_animation(animation) or sprite.sprite_frames.get_frame_count(animation) == 0:
		sprite.stop()
		return
	sprite.play(animation)

func _physics_process(_delta: float) -> void:
	if action_busy:
		velocity=Vector2.ZERO
		return
	if is_instance_valid(world) and world.get("home") != null and world.home.transition.busy:
		velocity=Vector2.ZERO
		return
	if is_instance_valid(world) and world.get("release_input") == true:
		velocity = Vector2.ZERO
		play_idle()
		return
	var direction := Input.get_vector("left","right","up","down")
	if direction != Vector2.ZERO:
		if abs(direction.x) > abs(direction.y):
			facing = "east" if direction.x > 0 else "west"
		else:
			facing = "south" if direction.y > 0 else "north"
	running=direction!=Vector2.ZERO and Input.is_action_pressed("run")
	velocity = direction * (RUN_SPEED if running else SPEED)
	move_and_slide()
	walking = get_real_velocity().length() > 2.0
	if walking:
		sprite.play(("run_" if running else "walk_")+facing)
	else:
		play_idle()
