# 走跑时序观察器验证（synthetic）

真实Godot GPU、同一完整包玩家执行8走跑×4时序情形，114检查、1656真实物理tick、32case独立重算通过；959输入闭包复建通过。包括实际5Hz物理/渲染、4完整tick逻辑失焦暂停、公开100%速度控制与松开idle后按既有相位重启。每segment至少2真实distance循环，重启case2segment，其他1；低FPS允许跳显示pose，不用该观察替代普通world10全pose覆盖。未挪位置或人工reset重启相位。

原始数据`/private/tmp/coastal-registered-locomotion-timing-synthetic-01`，隔离工程`/private/tmp/coastal-locomotion-timing-full-fixture-13`。按实际delta/位置/距离/相位/GPU纹理SHA/暂停/速度/两段重新计算，日志无脚本或引擎错误。

本证据使用2×2 synthetic角色，只证明验收工具；与农事48时序工具证据合计80情形，不能冒充真实人物完整包、美术/接触、OS焦点、用户认可或发布。

输入清单范围补充：原合同尚未列入`construction_native.py`导入的`native_contract.py`，上述输入数是原列清单。其实际代码与Git HEAD完全一致，已补存冷重放来源；合同不追溯改写。新冻结工具已强制绑定该传递依赖并增加拒绝其变更的反例。详见上级`native-transitive-python-input-fix.json`；本工具观察不作为完整美术回执。
