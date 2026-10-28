extends "res://dev/characters/character_headwear_trial.gd"
## Open this bounded repair directly on the affected sample.
func _ready() -> void:
 super._ready()
 if head_ready:
  select_sample("hoe-west")
  select_head_state("hair_hat")
