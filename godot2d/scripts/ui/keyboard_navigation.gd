extends RefCounted
# Directional movement considers only visible, enabled controls in the active page/modal.
static func eligible(control:Control) -> bool:
	if not control.is_visible_in_tree() or control.focus_mode==Control.FOCUS_NONE:return false
	if control is Button:return not control.disabled
	if control is Slider:return control.editable
	return false
static func next(scope:Node,current:Control,direction:Vector2i) -> Control:
	var candidates:Array[Control]=[]
	for node in scope.find_children("*","Control",true,false):
		if node!=current and eligible(node):candidates.append(node)
	if candidates.is_empty():return null
	if current==null:return candidates[0]
	var origin:=current.get_global_rect().get_center()
	var best:Control=null
	var best_score:=INF
	for candidate in candidates:
		var delta:=candidate.get_global_rect().get_center()-origin
		var forward:float=delta.dot(Vector2(direction))
		if forward<=2:continue
		var sideways:float=absf(delta.cross(Vector2(direction)))
		var score:=forward+sideways*3.0
		if score<best_score:
			best=candidate;best_score=score
	return best
