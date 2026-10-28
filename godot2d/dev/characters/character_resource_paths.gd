extends RefCounted
## Explicit authoring library roots; absent roots support isolated legacy fixtures.
const LIBRARY_ROOT := "art/characters"

static func relative_file(value: Variant) -> bool:
	return value is String and not value.is_empty() and not value.is_absolute_path() and not ":" in value and not "\\" in value and not ".." in value.split("/") and not "" in value.split("/") and not "." in value.split("/")

static func base(project_root: String, manifest_path: String, data: Dictionary) -> String:
	if not data.has("resource_root"):
		return manifest_path.get_base_dir()
	if data.resource_root != LIBRARY_ROOT or not project_root.is_absolute_path():
		return ""
	return project_root.path_join(LIBRARY_ROOT).simplify_path()
