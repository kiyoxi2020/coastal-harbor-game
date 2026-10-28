# 同配方西向行走：素材准备与最小适配包

日期：2026-10-29。范围：成年母版、top03条纹上衣、原橄榄裤/棕鞋，西walk四pose及四头部状态。阶段目标是核清可复用源、实测映射和下一实现边界；没有把本轮诊断登记为正式游戏人物能力。

## 结论

**目前可用现有GPT同源像素推进有限西向行走小样，无须因缺walk专用发帽PNG就立即生图。** 新四走候选保留locomotion原下身与脸手，仅替换已登记条纹上衣可见区；头部可尝试以完整西idle视图作多pose映射。既有r002精确idle直接沿用，不重做待机。

可查看[五pose四状态离线总览](walk-west-preparation/candidate-overview-diagnostic.png)、[头部源像素对照](walk-west-preparation/candidate-heads-diagnostic.png)及[无损APNG诊断循环](walk-west-preparation/candidate-loop-diagnostic.apng)。它们是离线诊断，不是Godot原生录像、已注册part或新strict build，也不作为后续构建的身体/source输入。

![离线四头状态诊断，最后一行为既有精确idle](walk-west-preparation/candidate-overview-diagnostic.png)

## 衣装的像素级来源桥接

旧wardrobe-walk-west实际为top03＋pants02牛仔裤＋original-brown-shoes-v1，不能改名算成目标配方。locomotion B则保留固定橄榄裤与棕鞋，元数据明确不是可独立换装的裤鞋。

已确认：西锄original-pants与original-shoes的idle，在各自coverage内与locomotion B_1逐RGBA差异都为0，并且source_references明确含B_1。由此可以为“同一个B_1原下身的walk姿态适配候选”建立真实来源桥接；这比仅按颜色/原裤命名推定更具体，但仍需新动作设计身份与覆盖范围登记。

以四walk和一个idle原B帧为底，仅在旧top-visible二值支撑内选入条纹样例像素。五张临时candidate_bare的alpha与B相同；裤/鞋区差异均0，top区之外差异0。没有改脸手、腿鞋或位置。完整registered源、原分层/层序均可定位；原GPT A v5 atlas、prompt及登记可从Git379a9bc精确恢复，不必重生。

| pose | top支撑像素 | 相对B的RGBA差异 | 裤区/鞋区差异 |
|---|---:|---:|---|
| walk_west_0 | 28,867 | 28,706 | 0 / 0 |
| walk_west_1 | 26,753 | 26,544 | 0 / 0 |
| walk_west_2 | 24,794 | 24,553 | 0 / 0 |
| walk_west_3 | 26,596 | 26,422 | 0 / 0 |
| 临时walk idle（仅诊断） | 22,999 | 22,870 | 0 / 0 |

这些数字不证明独立裤鞋、隐藏裸身体或任意混搭能力。新适配仍要记录source ownership、target coverage、occlusion/真实层序和所作用表面；不能为满足现行schema1三个mask的字段要求虚造mask或互换语义。

## 精确idle保持不变

临时walk idle与当前已交付西锄exact idle有22,853个RGBA差异，全部在top区域并集内；top以外差异0。两者top03同ID不代表条纹/袖褶像素相同。见[idle差异对照](walk-west-preparation/idle-difference-diagnostic.png)。

推荐正式小样复用 `recipes/wardrobe-hoe-west/r002.json` 的现有idle clip，保持其确切输出。最终诊断总览已采用该exact idle；四种头状态重组与现有四strict构建的idle逐RGBA一致。

## 头部：同投影候选与实测锚点

现行hair/hat pose-map没有walk条目；来源索引、相关prompt和2986项迁移映射的定向检索未找到已登记的walking发帽专源。这是限定检索范围的结果，不等于外部任意目录不存在。

四walk头部同向、近似同投影。耳弓、眼上缘、颅顶的实际ROI测量支持源idle到walk的整数平移；暗线阈值仅辅助定位，不作为正式ownership。source_view_pose始终为idle_west_0，target_pose分别记录，不能把静态源pose改写为walk。

| target pose | target耳弓锚 | 相对idle锚[292,282]的delta | 头边界最大源像素残差 | 1×逻辑显示残差 |
|---|---|---|---:|---:|
| walk_west_0 | [293,281] | [1,-1] | 3.162 | 0.750 |
| walk_west_1 | [293,281] | [1,-1] | 2.828 | 0.671 |
| walk_west_2 | [292,281] | [0,-1] | 3.162 | 0.750 |
| walk_west_3 | [294,281] | [2,-1] | 2.236 | 0.530 |

这不是逐RGBA相同的头或严格刚体。0.750为源距离×display_scale后的**1×逻辑显示像素**，不是已测物理屏幕误差；若再应用2×Canvas变换，理论可约1.5物理像素。没有本轮GPU测量，不据此宣称屏幕误差≤1px或严格接触通过。

复用对象是保留完整源的hair-only、真实near/far帽、专用under-hat hair。原ownership重提取与registered图逐RGBA相同；帽近远无重叠并可重建整帽。四walk只按测得锚点作完整头层诊断平移，不缩放/镜像/换脸手/擦目标身体。帽下发仍限定兼容原草帽，正式登记必须保留其兼容和层序合同。

## 显示与时间基准

所有walk源512×768、root=[256,708]、display_scale=138/582，源帧各80ms；这些值属于当前walk B variant。总览按约121×182的整画布逻辑大小缩放作离线诊断，历史文件名中的native-scale不表示真实原生采集。

APNG为四帧×80ms=320ms的无损源时序循环。当前locomotion walk.playback_rate=0.75；在无暂停、连续同速条件下，运行时理论每帧约106.667ms、周期426.667ms。离线APNG没有应用此倍率，也没有模拟世界位移、脚接触或输入时钟。

## 当前合同缺口及旧交付保护

[证据JSON](walk-west-preparation/evidence.json)包含来源、坐标、诊断SHA与既有四build依赖影响，作为只读资料，不是新的运行权威清单。

- schema2当前要求部件源登记与target pose一致，并从design的适配清单读取实际views。新walk需要诚实表达“一个source view映射多个target pose”，保留实际源pose、测量依据和目标注册，不能伪造旧sample/来源身份。
- 款式ID、动作适配revision与source view应分别绑定。不要就地追加/重写旧r001使历史输入失效，更不能以整个sample的哈希代替逐源/选择/注册绑定。
- top03/original-pants/original-shoes的design、共用idle poses、三构建器源码如改变，会影响现有全部四build；hair/hat的design及r001 views分别影响hair/hair_hat和hat/hair_hat。单独walk poses当前不在旧四build的闭包中。
- 当前artifact严格绑定实际engine与inputs，新代码或已依赖登记变化导致旧build过期是现行规则。下一实现必须明确新revision、新build ID及原manifest/PNG/native回执的历史保全与重验路径，不能覆盖旧输出、忽略engine SHA或刷新baseline。
- Godot strict消费者、launcher和原生validator目前有界限定hoe-west、四state和其时序，不能把walk suite写进去假定自动支持。扩展仍使用原构建入口/消费者/时间轴，不另造人物播放器。

本轮未改合同或资源，既有四build保持当前有效。

## 下一独立实施包

1. **来源准入与身份登记。** 以B_1精确idle祖先为桥，确认固定橄榄裤/棕鞋在这四walk姿态的适配范围；从确切Git对象准入必要原atlas/prompt/整帧登记，新revision保留旧ID作用域，不合并旧鞋款名。
2. **新增pose映射与完整层语义。** 先复用exact idle；新四walk各有实际部件源、ownership、coverage、occlusion/有序层。头部多对一view映射要分source/target pose，锚点不能按身高百分比或反复挪到“看顺眼”。当前没有必须补画的可见像素缺口；若层序/衣型露出未画区域或原生证明投影不足，再定向GPT补单侧小样。
3. **统一合同及制品生命周期。** 在修改引擎前确定旧构建/旧验证工具的可恢复保全和新current build引用方式；依赖校验不放宽。随后才扩通用注册合同、建立strict walk配方与四状态构建，禁止把本轮诊断PNG作为新身体源。
4. **实际接入与原生出口。** 同一评审支持walk真实能力，四state明暗停帧、至少十循环、移动/急停/转向、walk→exact idle及切换时钟验证；记录源时长与playback_rate。新证据绑定实际纹理/pose/mask/配置；不将前述离线轮廓残差当严格足接触验收。

本阶段到来源准备和最小适配包交付为止。正式walk配方/原生能力、完整人物动作四向、其他体型和生产发布均未在本轮新增。

## 本轮验证与留存

主代理逐SHA核对245条来源/产物引用记录，保留三张诊断PNG和一份APNG及其SHA；机器证据同时保留原始诊断目录路径，未拷入正式人物资源库。完整过程诊断仍在`/private/tmp/coastal-walk-west-prep`，它不是永久归档；本阶段无新的用户认可证据依赖这些过程图。

114项人物Python测试通过；check.py通过（strict_recipes=5、strict_builds=4、frozen_legacy_recipes=9），原已交付四构建保持有效。主报告本地链接、诊断SHA及五pose数据检查通过，git diff --check通过。本轮没有改运行代码/正式美术/配方/基线，也没有新增strict build、Godot实际加载或GPU采集；没有把上一阶段原生结果扩为walk通过。

分工：两位gpt-6.1-sol/high分别核衣装来源与头部实测映射，主代理核合同/旧交付依赖影响并集成资料，gpt-6-astra/high独立核查证据及结论边界。未提交或推送。

[独立复查](2026-10-29-walk-west-readiness-review.md)：规格与证据质量PASS，无阻碍交付的问题；结论仅限本准备阶段。
