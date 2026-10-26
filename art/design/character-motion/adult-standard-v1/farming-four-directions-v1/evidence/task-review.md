# Farming24 Task4 窄只读复查

实际审查模型：gpt-6.1-sol / high / fork_turns=none。范围为24组加载/面板/世界试玩增量；不改代码、不嵌套、不重跑测试，不复查自有美术。已读计划交付合同与Task4、三个相关脚本、面板tscn、新v2测试及原schema1门禁/衔接测试的对应段落。主代理提供36+122及schema1相关211已过，本报告不冒称独立重跑。

## 规格结论

**通过本次Task4静态规格审查。** 发现的1项P2已由主代理先复现再最小修复，并完成只读复核。 schema2的24键完整性、合法四阶段顺序、纹理/源依赖哈希及原子拒绝逻辑符合Task4；世界/面板均按真实选择解析资源，结束/换衣状态复用当前衔接分支。schema1曾新增能把非西向资源作为west/A返回的入口，当前显式version1仅west/A守卫已关闭此问题，历史与修复证据见下。

## 质量结论

**通过：当前无未关闭P1/P2。** 历史1项P2已关闭。 其余代码增量窄，数据先验证后发布，未发现新的世界序列结束/排队换衣破坏。布局按当前候选元数据计算可容纳整画布，实际原生交互/录像仍待主代理Task5；本次不作原生验收。

## 已关闭P2：schema1显式方向字段可绕过旧西向合同，查询返回错误朝向（发现时版本）

发现时位置：godot2d/dev/character_farming_review.gd:67–81、151–155；以下问题描述绑定修复前SHA256 `47a6786ea42b38245871fad3f3345c8b31d05a29c26fb9fa380b4c58a3979cd8`。

新加载器在schema1时用record.get("direction","west")、record.get("garment","A")，随后允许所有DIRECTIONS/GARMENTS。候选方向验证跟随该record方向；但schema1仍以action单键存储，get_clip仅允许查询west/A并直接返回clips[action]。因此schema1输入可以加载north候选，随后通过west/A查询暴露north纹理，世界current_action/facing仍保持west。旧实现对candidate.direction固定验证west，原行为并非这样。

静态可达示例（按指令未运行复现）：取一份合法schema1三动作catalog，仅把water条目改成direction="north"、garment="A"，指向合法的新north-A water candidate并更新record.sha256；另两条保持合法。条目数3、各action唯一、候选/inputs/纹理hash全部匹配时load_catalog返回true，clips.water.direction为north；get_clip("water","west","A")却返回该north内容，get_clip("water","north","A")反而为空。record显式garment=B也有同样单键别名问题。

影响：保存/读取旧catalog时错误版本标识或方向字段不会fail closed，试玩可能出现世界与纹理方向/衣服不一致；这是schema1合同兼容回归，不影响目前正确schema2键的数学完整性。

建议最小修正：schema1在进入pending前强制direction=="west"且garment=="A"，并继续验证candidate.direction==west；未知扩展不要静默映射。增加schema1三记录fixture的显式north/B记录拒绝检查，确认load失败后clips/hash/version全部清空；保留缺省direction/garment的现有合法schema1用例。也可在get_clip做防御性元数据匹配，但应先在加载边界拒绝。

## 最小修复复核（已关闭）

主代理在loader:69–70新增`version == 1 and (direction != "west" or garment != "A")`拒绝守卫，位于key构造和pending发布之前；缺省字段仍解析成west/A，schema2不进入该分支。对应测试从真实24键fixture中选[6,14,22]三north/A条目和[3,11,19]三west/B条目构造schema1，验证错误范围被拒绝并清空；其后重新加载完整v2验证可恢复。

只读检查主代理提供的RED/GREEN日志：两条`schema1_wrong_scope_6`、`schema1_wrong_scope_3`在RED中失败，GREEN中通过；最终`FARMING_CATALOG_V2 checks=39 passed=true`。本代理未重跑测试。读取的日志为`/private/tmp/coastal-farming24-schema1-scope-red.log`和`/private/tmp/coastal-farming24-schema1-scope-green.log`，仅检查相关尾部，不读取大型全日志。

修复后loader SHA256 `e4d29350d77c16b411f3254450ad1b47f9ad285bfde8978cb4c7c0d936f1b9a5`；新增回归测试SHA256 `415c554cf2515200bd55a0c8a2c4c13dc1d5f0e1ddfcced35bd83b3ab3275221`。守卫关闭此次查明的scope别名路径，未发现额外P1/P2。

## 已确认的静态证据

- 24键完整：records精确24条，action/direction/garment取3×4×2有限集合，pending拒绝重复，因此24个唯一键必然全覆盖；缺一组或替换成重复组合均拒绝，不依赖输入顺序。
- 阶段：schema2至少4帧、合法phase、非递减phase序号、四阶段全覆盖；ready/lift/contact/recovery（或对应water/harvest）有序完整。允许同阶段额外帧是计划可增帧合同的一部分。
- 哈希不完整：每frame必须有合法file/sha256、source/source_sha256；source必须在inputs且摘要相同；inputs逐一读盘核验、纹理读盘核验、实际纹理canvas一致。缺失或不匹配会走_reject，clips/hash/version清空。局部pending只在全体完成后赋值clips。
- texture_hashes核验PNG文件摘要的至少4个不同值；它不等价于自动证明4个姿态语义不同或不同编码PNG的RGBA不同。这是艺术/源验证与原生观察的剩余范围，本次未把现有真实资源判成重复，也未将它另列当前P2。
- 面板：farming_clip按review_action/review_direction/trial.garment取clip，refresh_preview先清空两张texture，缺资源不残留旧帧；方向/动作选择只改面板独立相位。世界start_farming_sample按facing/garment取同library的实际clip，完整期间锁方向/移动，未拿面板review_direction替代世界朝向。
- 结束/换衣：farming_pending_garment保留最后请求，期间不改变garment；完成保存pending后cancel恢复scale/offset、清clip/时钟、回idle，然后仅在idle原子set_garment。reset取消且清队列；focus-out暂停elapsed。原衔接测试明确覆盖这些行为，v2测试覆盖24组面板/世界第二帧与回idle；同一控制分支未分叉。
- `.tscn`根位置为[51.29897,32.12371]+[256,708]×0.2371134≈[112,200]。以当前1536×1920、root[768,1600]、scale138/1164计算，整图在slot中边界约[20.95,10.31,203.05,237.94]，落在224×240内；hoe1536×1792/root[768,1544]边界约[20.95,16.95,203.05,229.40]也在内。此为元数据几何核对，不替代原生控件布局/遮挡检查。

## 审查版本绑定与限制

- character_farming_review.gd 当前修复后SHA256 `e4d29350d77c16b411f3254450ad1b47f9ad285bfde8978cb4c7c0d936f1b9a5`（发现时版本见历史P2段）
- character_motion_review.gd SHA256 `9c3272bda4bb5b692d2b34b4a907ebfc015f71582493b70c384fc01b6a0099cc`
- character_walk_trial.gd SHA256 `68ee32cee8adc28d96c5c59a90bdf6c3d9556173c8597c3038783ca7906f21c9`
- character_motion_review.tscn SHA256 `f8672a61c5df0c1b82f6f22fff64605106b27f89c8e8cb8edd1be9fdc3dad3b5`

没有执行Godot、测试、原生输入/截图或修改工程文件；只写本/tmp审查报告。完整24实资源最终加载、所有姿态/十次连续播放及世界衔接绑定由主代理继续完成。
