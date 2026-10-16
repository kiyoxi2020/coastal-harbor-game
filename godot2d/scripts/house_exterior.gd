extends Node2D

# Source atlas geometry remains available to asset/runtime verification.
const REGION := Rect2(34, 91, 488, 448)
const HOLE := Rect2(347, 382, 63, 84)
const FACTOR := 168.0 / 488.0

func source_regions() -> Array[Rect2]:
	return [
		Rect2(REGION.position, Vector2(REGION.size.x, HOLE.position.y - REGION.position.y)),
		Rect2(REGION.position.x, HOLE.position.y, HOLE.position.x - REGION.position.x, HOLE.size.y),
		Rect2(HOLE.end.x, HOLE.position.y, REGION.end.x - HOLE.end.x, HOLE.size.y),
		Rect2(REGION.position.x, HOLE.end.y, REGION.size.x, REGION.end.y - HOLE.end.y),
	]
