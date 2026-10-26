# 锄地B衣色修订窄评审

评审模型gpt-6-astra/high。只读检查、不改项目、不嵌套、不重跑已过测试。依据用户原话“锄地的衣服颜色比其他动作浅，其他没问题”，仅审四方向hoe B的衣服颜色；不重开已认可姿态、其他20组或人体管线任务。

## 初审结论

规格设计/已冻结西东产物符合本轮限定范围；当前未发现P1/P2。最终规格和质量结论待南北冻结、全16帧来源/保持验证、20条目不变及新原生采集前后门禁完成，当前不提前判定整体完成或新色获用户认可。

## 已检查内容

读计划、compose_color.py及4项测试、test_revision.py、catalog选择工具、定向原生脚本；西/东实际candidate、build_color_revision.py、implementation-report；用户认可记录的原话/诊断解释/分组合处置。目视西东各四帧ownership板与before/after板，共八个姿态。

- 范围：用户原话与BlueB诊断分开记录；20组已显示外观认可，四hoe-B只保留非颜色视觉认可，旧24纹理/时序/catalog/346报告均按历史输入绑定。没有把此反馈改写为新色已认可。
- 合成来源：paint是人工同pose衣身/袖子polygon与原蓝布/GPT蓝布的交集；cool_mask阈值仅选像素，不计算新色。输出的每个paint像素RGB直接取自同坐标完整GPT raw，alpha全图来自原图，paint外完整原RGBA保留。没有颜色矩阵/自动调色、局部位移/缩放、镜像、重建脸手或新姿态覆盖。
- 人工ownership：已见西/东四姿态逐帧坐标表及红色覆盖板，覆盖衣身、可见衣缘、袖子；未见覆盖脸、手、裤鞋或完整锄具。蓝色辅助分割限定在人工表面内，不将全图颜色相近像素自动认作衣服。
- 保留边缘：GPT非蓝/偏离处保留原像素；fallback只占已声明原蓝布，固定上限5%。西/东实际记录约0.114%–0.734%；未把其等价为整张衣服重绘，也未用该阈值自动证明外观一致。before/after可见衣色收深，姿态、脸手工具及轮廓不变；边缘最后仍由原生目视验收。
- 失败处理：西lift首稿发生上移导致16.2%不匹配，被同一5%门禁拒绝；保留raw与失败记录，第二稿改变输入为单原图/坐标锁定后通过，未移动raw或放宽门禁修补。
- 几何和时间：candidate沿原canvas/root/display_scale/source密度及四帧整数translation，180/220/140/260ms不变；新source仅替换衣服RGB，再用原整帧登记烘焙。test_revision分别检查父candidate hash、同几何/时序/translation、原alpha、mask外0RGB差及mask内等于GPT RGB；独立source/登记验证负责实际文件依赖。
- 版本：西candidate be58b7d2886ac08ef5d34846de67decef77a4b7abe3d825174b3398566c60a77；东d854afcaa34f6a826a285de1e1a5ca9178465ce41b871b00f88f851bac033cff。parent哈希、mask/raw/ownership/compositor快照都保留，accepted及palette_user_accepted未升为true。
- catalog：build_review_catalog基于catalog-before-color-v2副本，仅改四个action=hoe/garment=B记录的candidate/hash/note；其他记录原样保留。独立test_revision按原索引逐条比较20记录，24完整加载仍由现有schema2与新预快照验证。
- 原生设计：新test_character_hoe_color_native只调用四B/16停帧、每组十面板循环与一次世界one-shot，并抓同向B的认可water参考；加载24组并检查20记录不变。复用现有UI/世界助手，无玩法或存档增量。旧346结论不被重写为新色覆盖；fresh snapshot/receipt负责当前输入，report明确新色待用户确认。

## 尚待最终证据

南北最终source、ownership和candidate冻结；全16帧实际来源/alpha/非衣保持测试结果；catalog-color-v2确实只改四B并保持20条目；16原生停帧、四组十面板循环/世界one-shot及同向water颜色对照；fresh输入快照、报告和后验回执的确切SHA一致。原生衣色视觉符合反馈仍需用户确认，不由亮度统计或结构测试替代。

## 四方向最终源与catalog独立复核

按主代理本轮明确要求，对全部16帧做独立只读像素审计，没有运行或修改现有测试/绑定输入。

- 四candidate均完整4帧，全部inputs及实际registered文件SHA匹配；每个parent_candidate_sha256与原hoe/B候选文件一致。
- 原source与修订source全图alpha逐字节一致；paintmask严格二值；mask外RGB无任何差异，连同alpha即mask外RGBA精确保持；mask内每个RGB均等于对应rawGPT同坐标像素。未发现从其他像素程序调色或混入非GPT新色。
- 每个registered完整RGBA与修订source按原whole_frame_translation整数平移置入原canvas的结果完全一致。canvas、root、display_scale、source密度、phase、duration、translation均与父版一致；16帧无异常。
- 原/新catalog均24条，逐字段比较只改变hoe/south/B、hoe/west/B、hoe/east/B、hoe/north/B四条，其他20条完全相同。catalog-before-color-v2文件SHA与visual-acceptance-2026-10-26.json的原catalog SHA相同，未借副本切换改写旧认可范围。

本次复核候选完整文件SHA：

| 方向 | SHA256 |
|---|---|
| south B | 6e7a6f3c2133760a5e7eb2b0c5399f49272ef0eb6f569089d4f315dcd90c03d3 |
| west B | be58b7d2886ac08ef5d34846de67decef77a4b7abe3d825174b3398566c60a77 |
| east B | d854afcaa34f6a826a285de1e1a5ca9178465ce41b871b00f88f851bac033cff |
| north B | 6bf8e60f1cb6bc4be433aef34da120fd8781a24ba140ec3bcb037e80f1e548b8 |

南北approved-color-comparison.png均已目视：同向认可water/harvest B与四个hoe B新色在明暗1x/2x对照，颜色较原浅蓝收敛；没有观察到皮肤/工具/裤鞋受染，内部明暗仍随原姿态保留。离线色板用于衣色比较，不替代原生全画布或用户配色认可。

新native脚本与初审相同：加载新24catalog、检查20条未变，定向四B的16停帧/每组十面板循环/一次world，并抓同向water B参考；report仅列四修订clip，scope明确不扩展旧346或用户色彩认可。当前源及选择合同通过，未发现P1/P2；最终交付结论仍待主代理fresh native报告和采集后回执核对。

## 最终限定结论（第3轮原生渲染夹具完成）

**规格通过，质量通过本次衣色修订交付门槛；无未关闭P1/P2。** 四方向hoe B只改衣服RGB，16帧原alpha/非衣RGBA/姿态/几何/时序与其余20条目保持已由独立像素复核确认；新色可交用户确认，不能把本评审当作用户已认可新配色。

### 原生验证口径变更

前两轮OS事件注入不稳定，失败运行分别保留于/private/tmp/coastal-hoe-color-v2-native-reference-click-attempt1和/private/tmp/coastal-hoe-color-v2-native-input-attempt2。第一轮water参考点击hover失败，第二轮存在方向键/按钮事件丢失；没有重写失败记录为成功。

第3轮改为明确的**Godot原生渲染夹具**：按钮直接发出真实控件signals，工具键直接调用实际trial handler；方向由fixture赋值，focused也由fixture设置true。它验证实际纹理、原生非headless画面、控件信号驱动的选择/停帧、面板连续播放和世界权威时间轴one-shot，**不验证OS键鼠输入、转向移动输入或窗口管理器焦点**。同向water参考由显式select_clip选择，只是颜色参照，不冒充water输入测试。源码check名已改为fixture_selection/fixture_direction/fixture_action，report scope明确不是OS keyboard/mouse automation。

这个范围适合本次纯衣色资源变更：生产/UI输入逻辑未因衣色修改，颜色显示验证不必依赖不稳定OS注入。旧346输入验证仍是旧24图历史结论，不被移植为新色的新输入通过；此前原生失焦恢复未验证也未被此次fixture覆盖。

### 最终证据核对

直接读取/private/tmp/coastal-hoe-color-v2-native/report.json、input-contract.json、input-validation.json，未重跑测试或采集。

- 69项check全部true；3420样本、148连续捕获。4方向B、16张全画面停帧、4块对照板、4张认可water参照截图存在。
- 四方向各有ten_cycles和world_all_poses_locked_then_idle通过：每组十次**面板**循环、一次世界one-shot，不扩大为世界各十次。
- 四个report candidate SHA和逐帧时长与新快照对应hoe/{direction}/B条目一致，也与上节独立像素审计冻结版本一致。
- 快照完整SHA：d6674e71e4f34a192568a71f7a9ac89feb80a6277fcceef4fef038428d2ebfdf。
- report完整SHA：2590e0d1cf7d3369790109d27b3131b2723ee6bd5442cd63fb759357eaafa7a9。
- 回执绑定以上两个实际文件完整字节SHA，input_hashes_current=true、archive_allowed=true；24候选/96帧/1685保守依赖/11角色。24/96是快照目录覆盖，**本次原生覆盖仅四B/16帧**。
- 原生started UTC 09:51:16、finished 09:52:09，门禁验证09:52:26；capture_time_order_verified=true，精度明确1秒。
- accepted_20_records_exactly_unchanged及四个accepted_water_reference检查为true。原色认可记录没有改写给新candidate。
- 主代理已目视四原生板；本次独立追加目视南/北原生板，衣身袖子色调收深，工具/完整姿态未被裁断，没有观察到脸手或裤鞋越界染色。西/东已有八帧ownership和before/after独立观察。原生外观判断不替代用户最终色调确认。

原生渲染fixture的局限与两轮失败均如实保留后，本轮目标与证据相符。最终汇报应称“69项原生渲染夹具检查通过”，不要简称为“新OS键鼠/焦点验证通过”，也不要因未改的几何已认可而提升新palette认可状态。
