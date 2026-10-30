# 港口空间观察器验证（synthetic，非人物交付验收）

真实Godot GPU在原港口场景使用2×2 synthetic完整配方执行树/柜台绕行、关闭/半开/全开门碰撞和三处各三工具动作。145检查、14场景、1528实际物理tick、52PNG。原始位置/连续tick/各waypoint/门碰撞及全部PNG哈希独立复核，959输入闭包重建通过，日志无脚本/引擎错误。工具空间停帧观察明确使用0.25倍率，常速时序另验。

原始PNG和完整观察保留`/private/tmp/coastal-registered-spatial-synthetic-06`，隔离工程`/private/tmp/coastal-spatial-observer-full-fixture-12`。此前03内建函数重名导致parse失败、04路线触真实柜台且采集跨工具完成边界、05短帧GPU采样漏姿态，均未计通过；依据真实碰撞改路线并显式慢速空间观察后06通过。01/02仅冻结候选、未执行采集。

本证据仅证明采集器、同玩家控制链与真实港口碰撞；不证明真实角色美术、工具合法目标、完整接触、OS输入、用户认可或生产发布。

输入清单范围补充：原合同尚未列入`construction_native.py`导入的`native_contract.py`，上述输入数是原列清单。其实际代码与Git HEAD完全一致，已补存冷重放来源；合同不追溯改写。新冻结工具已强制绑定该传递依赖并增加拒绝其变更的反例。详见上级`native-transitive-python-input-fix.json`；本工具观察不作为完整美术回执。
