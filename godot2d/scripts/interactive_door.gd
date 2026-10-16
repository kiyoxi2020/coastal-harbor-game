extends Node2D

@export var inside := false
@export var entrance_normal := Vector2.DOWN
@export var pilot_frames: Array[Texture2D] = []
@export var leaf_textures: Array[Texture2D] = []
@export var pose_sizes: Array[Vector2] = [Vector2(22, 29), Vector2(11, 29), Vector2(3, 29)]
@export var leaf_visual_offset := Vector2.ZERO
@export var aperture_offset := -29.065574
@export var pilot_anchor := Vector2(15, 54)
@export var pilot_leaf_height := 0
@export var pilot_frame_top := -9.0
@export var render_size := Vector2(22, 29)
@export var pose := 0

var body: StaticBody2D
var collision: CollisionShape2D
var _approach_fallback := Vector2.ZERO
var approach: Vector2:
	get:
		var marker := get_node_or_null("Approach") as Marker2D
		return position + marker.position if marker != null else _approach_fallback
	set(value):
		_approach_fallback = value
		var marker := get_node_or_null("Approach") as Marker2D
		if marker != null:
			marker.position = value - position

func _ready() -> void:
	body = $DoorCollision
	collision = $DoorCollision/CollisionShape2D
	set_pose(pose)

func can_interact(point: Vector2) -> bool:
	var offset:=point-position
	var depth:=offset.dot(entrance_normal)
	var lateral:=offset.dot(Vector2(entrance_normal.y,-entrance_normal.x))
	return depth>=0 and depth<=56 and absf(lateral)<=24

func aperture_top() -> float:
	return global_position.y + aperture_offset

func crossing_point(player) -> Vector2:
	# South cutaway conceals below the threshold; exterior above the actual awning.
	var y: float = aperture_top() - (player.visual_top if entrance_normal.y < 0 else player.visual_bottom)
	return Vector2(position.x, y - entrance_normal.y * 0.75)

func set_pose(value: int) -> void:
	pose = clampi(value, 0, 2)
	var channel := get_node_or_null("DoorCollision/CollisionShape2D") as CollisionShape2D
	if channel != null:
		channel.set_deferred("disabled", pose == 2)
	var leaf := get_node_or_null("DoorLeaf") as Sprite2D
	var frames := leaf_textures if leaf_textures.size() == 3 else pilot_frames
	if leaf != null and frames.size() == 3 and pose_sizes.size() == 3:
		leaf.texture = frames[pose]
		if leaf.texture != null:
			leaf.scale = pose_sizes[pose] / leaf.texture.get_size()
			if leaf_visual_offset != Vector2.ZERO:
				leaf.offset = Vector2(
					leaf_visual_offset.x / leaf.scale.x,
					leaf_visual_offset.y / leaf.scale.y)
	var edge := get_node_or_null("LeafEdge") as Polygon2D
	if edge != null:
		edge.visible = not inside and pose > 0
		var edge_left := leaf_visual_offset.x + pose_sizes[pose].x - 2.0
		edge.polygon = PackedVector2Array([
			Vector2(edge_left, leaf_visual_offset.y),
			Vector2(edge_left + 2.0, leaf_visual_offset.y),
			Vector2(edge_left + 2.0, leaf_visual_offset.y + pose_sizes[pose].y),
			Vector2(edge_left, leaf_visual_offset.y + pose_sizes[pose].y),
		])
