extends Node2D
## Scene-authored props and customers mirror the durable business state.
## Decorative customers never participate in household consumption/population.
func refresh(restaurant:Dictionary)->void:
	var status:String=restaurant.get("status","closed")
	var opened:bool=status!="closed"
	$ClosedSign.visible=not opened
	$OpenSign.visible=opened
	$MenuBoard.visible=opened
	$Smoke.visible=opened
	$Customers/Customer1.visible=opened
	$Customers/Customer2.visible=status=="operating"
