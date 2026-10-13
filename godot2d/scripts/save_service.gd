extends RefCounted
const State = preload("res://scripts/player_state.gd")
var directory: String
var last_error := ""

func _init(path: String = "user://coastal-progress") -> void:
	directory = ProjectSettings.globalize_path(path)

func _read(path: String):
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null or file.get_length() > 1048576:
		return null
	var json := JSON.new()
	return json.data if json.parse(file.get_as_text()) == OK else null

func read_save() -> Dictionary:
	var main = _read(directory.path_join("progress.json"))
	if main is Dictionary and main.get("version",1) != 1:
		return {"ok":false, "future":true, "message":"存档版本不兼容，已保护原文件。"}
	if State.valid_data(main):
		return {"ok":true, "recovered":false, "data":main, "message":""}
	var backup = _read(directory.path_join("progress.backup.json"))
	if State.valid_data(backup):
		return {"ok":true, "recovered":true, "data":backup, "message":"主存档异常，已恢复上一份备份。"}
	return {"ok":false, "future":false, "message":"尚无有效存档。" if not has_files() else "存档与备份均无法读取，原文件已保留。"}

func has_files() -> bool:
	return FileAccess.file_exists(directory.path_join("progress.json")) or FileAccess.file_exists(directory.path_join("progress.backup.json"))

func write_save(value: Dictionary) -> bool:
	last_error = ""
	if not State.valid_data(value):
		last_error = "进度校验失败，尚未保存。"
		return false
	if read_save().get("future",false):
		last_error = "无法覆盖不兼容版本的存档。"
		return false
	if DirAccess.make_dir_recursive_absolute(directory) != OK:
		last_error = "无法创建存档目录，尚未保存。"
		return false
	var main := directory.path_join("progress.json")
	var temporary := directory.path_join("progress.pending.json")
	var file := FileAccess.open(temporary, FileAccess.WRITE)
	if file == null:
		last_error = "无法写入存档，尚未保存。"
		return false
	file.store_string(JSON.stringify(value))
	file.flush()
	file.close()
	if not State.valid_data(_read(temporary)):
		last_error = "存档写入校验失败，旧进度仍保留。"
		return false
	if State.valid_data(_read(main)):
		if DirAccess.copy_absolute(main, directory.path_join("progress.backup.json")) != OK:
			last_error = "备份失败，旧进度仍保留。"
			return false
	if DirAccess.rename_absolute(temporary, main) != OK:
		last_error = "无法替换存档，旧进度仍保留。"
		return false
	return true
