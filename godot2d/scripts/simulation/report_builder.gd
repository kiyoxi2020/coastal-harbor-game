extends RefCounted
static func daily(data: Dictionary) -> Dictionary:
	var life: Dictionary=data.life
	var lines: Array[String]=[]
	if life.daily_reports.is_empty():
		lines.append("尚无日结记录")
		return {"day_id":0,"current_day":int(life.day_id),"lines":lines}
	var report: Dictionary=life.daily_reports[-1]
	lines.append("收入 %d G    支出 %d G" % [report.cash_in,report.cash_out])
	lines.append("今日采集 %d 个 · 新成熟作物 %d 格" % [report.pickups,report.mature_plots.size()])
	for line in report.summary:lines.append(str(line))
	return {"day_id":int(report.day_id),"current_day":int(life.day_id),"lines":lines}
