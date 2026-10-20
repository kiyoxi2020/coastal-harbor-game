extends Label
# Read-only number display: quantity is changed by the surrounding real buttons.
signal value_changed(amount:float)
@export_range(1,20,1) var value:float=1.0:
 set(next):
  var clean:=clampf(roundf(next),1.0,20.0)
  if clean==value:return
  value=clean
  text=str(int(value))
  value_changed.emit(value)
func _ready():text=str(int(value))
