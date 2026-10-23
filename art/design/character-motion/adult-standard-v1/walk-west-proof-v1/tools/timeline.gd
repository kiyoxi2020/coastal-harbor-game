extends RefCounted
## One authoritative elapsed time determines every displayed recipe frame.
var durations_ms: Array = []
var cycle_ms: float = 0.0

func configure(durations: Array) -> void:
	durations_ms = durations.duplicate()
	cycle_ms = 0.0
	for duration in durations_ms:
		assert(float(duration) > 0.0)
		cycle_ms += float(duration)

func frame_at(elapsed_ms: float) -> int:
	var phase: float = fposmod(maxf(0.0, elapsed_ms), cycle_ms)
	var edge: float = 0.0
	for i in range(durations_ms.size()):
		edge += float(durations_ms[i])
		if phase < edge:
			return i
	return durations_ms.size() - 1

func loop_at(elapsed_ms: float) -> int:
	return floori(maxf(0.0, elapsed_ms) / cycle_ms)

func start_ms(frame: int) -> float:
	var elapsed: float = 0.0
	for i in range(frame):
		elapsed += float(durations_ms[i])
	return elapsed
