# 衣物组合五组抽样独立评审

评审模型gpt-6-astra/high；只读，不嵌套，不修改项目，也未重跑主代理已过的236/264来源结构检查、loader和contract回归。用户明确只取不同衣物组合的动作样例，不遍历全部组合/方向；本评审不把限定样例扩大成完整人体体系或全衣柜验收。

## 最终结论（原生完成后）

**规格符合：通过。质量：在本轮五个固定衣物配方、动作方向和matching_idle范围内通过，可交用户视觉验收。未发现未关闭P1/P2。** 五组独立槽源和绑定完整；实际原生渲染、十面板循环、世界走跑/三工具one-shot及同衣回站姿形成闭环。此结论不等于用户已认可新衣物，不外推任意衣柜混搭、所有方向、新剪裁、完整隐藏人体或生产迁移，也不包含OS键鼠/WM焦点验证。下列初步与阶段补审保留时间顺序，最终状态以本节及末尾终核为准。

## 初步结论

已冻结walk-west/run-east的来源、独立槽及范围声明通过静态审查；试玩代码的能力边界、预检查后替换及切sample原子性未发现未关闭P1/P2。证据工具曾发现1项P2，已修复并只读复核关闭。农事三样例尚未冻结，原生尚未执行，因此**最终五组规格与质量结论待补充**，不提前记全部通过。

已核对实际sample SHA：walk-west 94f786472c86f5c8225bd9a5e76abd157c0e4fee43f81e5bdd89b590432f2ac6；run-east fa1b11913f8facc8527b8c6c0d76ebb44cfe13b2ae394c1f844fe5dc19fe76d8。

## walk/run来源和真实槽位

阅读两组sample/README/implementation-report、原pose层序、build_sample/check_sample及独立槽板。每组4运动姿态加matching_idle；walk为top03+pants02+原鞋，run为top04+原裤+shoes04，与要求一致。

- 三槽实际保存独立pants、shoes、top（远袖/完整衣身/近袖）文件，另有shared_body和逐pose ownership/visible_mask/frame_alpha；不是只有配方字段或整张换装PNG。独立槽板可见裤鞋、完整衣身和前后袖，shared_body排除这些可见槽位。
- 原same-pose层序明确记录body/远臂/远袖/torso/近臂/近袖及各hide_mask，coverage与部件完整源分开；衣身使用额外无臂GPT源，隐藏衣料不永久挖手洞，实际遮挡由原pose mask表示。run四个torso原ownership在hidden_mask范围内均有alpha，未发现用空洞torso冒称完整衣身。
- walk运动torso复用同一完整源，袖子各pose；run逐pose完整torso，第4帧短下摆失败稿保留后改同坐标孤立torso源修复。source完整1024×1536、prompt、引用、失败稿与投影中间图保留；整画布0.5 nearest回既有512×768坐标，不按part bbox拟合、单独缩放或任意挪脚。
- 原布料alpha提供同版型精确接口，手工踝口/鞋口和下装包络约束下槽；颜色辅助仅限定局部原裤/皮肤边界，并非自动按颜色给整个人体分层。非衣RGBA及原alpha保留由主代理独立重跑检查；本评审没有把该统计等同完整动态兼容。
- 这些是新设计在原版型/原pose接口上的适配款，仅证明两固定配方、方向和5姿态。并不证明任意换成更宽衣摆/不同鞋形仍成立，也不证明隐藏裸体齐全或全库存自由组合。两组文档的同版型/非穷举范围清楚，没有用加载成功冒称混搭通过。

## 试玩集成与原子性

- 新SampleLibrary限定五个id且精确五条，无重复便可得完整集合；要求三slots、四pose、hash绑定纹理/输入、matching_idle同向身份、实际尺寸等。load_samples清旧状态，局部pending只有全部验证后才发布，失败不会保留部分新样例。
- apply_samples分两遍：先对全部样例核验原已加载pose_id、duration、canvas/root/scale及idle基线，再替换内存B配方纹理。未在检查中途修改其他sample；没有改磁盘认可24catalog/纹理或生产场景。
- select_sample是无await的同步切换：先reset取消当前工具/清队列/恢复几何，再设B和新方向、active_sample、该方向matching_idle，最后重置面板动作相位并refresh。旧sample同方向idle即使先前被替换，也在选择新sample时整套覆盖；没有渲染帧跨越的半套衣物状态。
- 面板方向/动作按钮禁用，原1/2/Shift外观/跑步键被过滤；只有选定walk/run的同向移动允许，农事样例不接受移动，工具键只允许对应动作。主角只在此隔离派生场景使用新纹理，原已认可角色、生产逻辑和存档路径不改。
- 启动或apply失败时展示sample_error，尚未选中active_sample，不允许世界输入误跑样例。未知sample id不会改当前选择。
- 原生脚本明确非OS键鼠/WM焦点验证：控件signals及逻辑Input actions驱动真实GPU渲染。计划覆盖20pose明暗背景、五matching_idle、每组十面板循环、walk/run实际运动物理与三工具one-shot，并检查未采样工具/方向拒绝。实际结果仍待运行，不能以脚本存在代替通过。

## 已关闭P2：回执可覆盖冻结输入/原生报告

发现版本的evidence_contract.validate在最后无条件Path(receipt).write_text；若CLI把receipt指定为contract/report同一路径，工具会先读取原证据再将其覆写，破坏其原始SHA。旧farming工具有保护，新wrapper初版遗漏。

主代理先建立/private/tmp失败回归，再修复：任何读取验证/写回执之前，用resolve比较两输入路径，目标存在时再samefile检查，拒绝直接路径、symlink和hardlink别名。只读检查现行守卫确在try与写入之前；拒绝抛ValueError，原输入字节保持。主代理提供最终9项GREEN（本评审未重跑），包括contract/report/symlink/hardlink别名保护；此P2关闭。原生尚未快照，所以修复没有破坏既有采集绑定。

## 证据工具范围

新工具扩展现有farming预采集合同，保留旧认可locomotion/run/farming及新trial/native静态依赖，再加入五sample自身与其全部inputs；后验重算依赖集合、工具SHA、报告输入契约SHA、五clip id、全true checks和UTC先后。范围声明为保守依赖超集，不是实际文件访问追踪。

snapshot/归档仍必须在五实际sample冻结后创建并通过新运行报告门禁。基线24纹理的静态加载/原报告不能替代这五套新组合的动态原生证据。最终还需核对report中的sample SHA/pose/时长与冻结catalog确实对应，不能只看到五id和全true就推断范围无误。

## 留待下一次复审

只检查已经冻结的walk/run，未对未冻结hoe/water/harvest值作任何通过判断。待三农事来源、独立槽/coverage、matching_idle全部冻结后补审；再核对真实原生报告/停帧/循环/世界衔接及预后门禁。用户尚未认可这些衣物适配小样，不能继承原衣色或原24动作的衣物组合认可。

## water-south与harvest-north冻结后补审

两组限定资源合同与静态质量审查通过，未发现新增P1/P2；hoe尚未冻结、五组原生尚未运行，仍不提前给全五组最终结论。只读检查sample、ownership、实施报告、构建器/验证器对应逻辑和1×/2×明暗对照板，没有重跑主代理已通过的像素/结构测试。

实际文件SHA匹配主代理冻结值：water-south 9b2c74d2755c658545c9b15e86d77d1212d715e167d7c05a7a39d6bef730fc11；harvest-north 0c5e81663fed72376e11dcec609c41a95df17adabc0540e8773b6cac599020f9。

### 配方与范围调整

water保持原蓝长袖，换pants02+shoes04。harvest最终保持原蓝长袖和原鞋，只换pants02，recipe.changed_slots=[pants]；前期红毛衣袖口/后领越界失败源及修订稿保留，未当作成功top04输入使用。用户要求不同组合各动作的代表性抽样，没有要求每个动作都新增上衣；红毛衣已由run-east覆盖，因此此调整不缩减五动作代表性目标，也不冒称未成功的harvest红毛衣通过。

已核对UI标签为“北向收获 · 蓝长袖与牛仔裤”和“牛仔·收获”，sample scope及ownership亦写明原蓝top/原鞋保持，没有新旧配方文字错配。

### 独立槽与来源

每帧及matching_idle都有独立top/pants/shoes源、可见槽文件、source ownership、visible coverage和occlusion；共享层明确名为shared_same_pose_foreground_and_contour，保留原手/壶/水流/作物、轮廓和alpha边缘，不称隐藏裸体。外观固定在原版型接口，只验证本配方/方向/五姿态。

water可见新裤鞋从完整GPT稿原坐标取RGB，原top可见表面引用同pose旧图；必要隐藏衣料来自人工限定的同pose completion，ready top和裤腰使用不同明确登记来源。当前手/壶遮挡不永久挖入需要保留的布面源，coverage与完整source分开。构建器快照以references/build_samples.py.txt绑定在inputs，避免共享helper后续变化静默改写来源依据。

harvest最终只有pants选新GPT可见面，top/shoes使用原同pose图，source_surface_repairs当前为空；红稿的修补记录以rejected_red_surface_repairs_archive留存，不参与最终选择。ready/reach保留人工声明隐藏裤面，其他不需要的隐藏区没有虚填为已验证人体。其本地构建器快照和语义检查工具亦绑定；原blue top没有被失败raw中的皮肤或红袖替换。

主代理已独立validate两组：原alpha、mask外RGBA、实际独立槽重建、input/source哈希及几何时序均通过；harvest7项本地测试亦由主代理重跑通过。代码核查确认重建按二值ownership取原alpha，避免把soft alpha反复相乘；每个visible slot须有源表面且槽间不重叠，最终baked按原整数整帧位移登记。

直接比对sample与当前父candidate的四pose_id/时长一致：water ready/raise/pour/recovery=200/200/350/250ms，harvest ready/reach/pluck/recovery=200/250/250/300ms。动作canvas1536×1920、root[768,1600]、scale138/1164；matching_idle独立512×768、root[256,708]、scale138/582。原动作到idle硬切保持既有策略，没有借换装修改原动作。

### 视觉与能力边界

两组原/新1×/2×明暗板已独立目视。water牛仔及搭扣可辨，原手壶水流和衣袖保持；harvest只见裤面改为牛仔，后领/袖口为原蓝、原作物及手脚没有明显染色或缺失。原生连续播放、腰/踝接口动态及matching_idle衔接尚待后续；静态slot重建不等于新增任意剪裁、全隐藏体或所有衣柜组合兼容。必要隐藏腰/腋的纹理接缝和准确解剖没有被本次可见画面测试批准，未来若暴露必须重新验收。

## hoe-west最终冻结补审

最后一组源合同与静态质量审查通过，未发现新增P1/P2。sample.json实际SHA为99f31cfecc7cdc3c84d4d22fcfa1f1dc9a64e5359ffa7493a867be1b1c7949bd，catalog冻结SHA为8b12f260337c1692dc68f1e3a2e04fbe62dbd0c06612a1eed94af8dddb287c87。此节取代上文hoe尚未冻结的阶段状态；五组最终动态结论仍待本轮原生报告及receipt。

只读核对sample、source-selection、ownership、实施报告和构建/验证关键逻辑，并目视1×/2×明暗对照板、独立槽源板与lift肩缘诊断图，没有重跑已通过的8项资源测试或实际validate。配方为top03+原裤鞋，四动作与matching_idle均保存独立top/pants/shoes完整衣料源、可见coverage及原same-pose前景/轮廓。原脸手、锄头、裤鞋和alpha边界保持，未把共享原轮廓宣称为已补全裸体。

lift只在人工声明肩缘面板中，针对主raw3 alpha=0且属于原衣物ownership的120点，采用同pose raw2原坐标有效条纹衣料。supplement_surface仅Image.composite选源，未位移、缩放、插值或程序调色；验证重建selected-density与声明raw选择逐字节一致，并拒绝补面越出人工面板、替换主稿非空面或越出原衣物表面。raw1/2/3、补面mask、selected-density和选择注记均作为输入保留绑定。此为同pose布面选择，不是新姿态或新人体生成通过。

原版型领口/腕口少量GPT新增皮肤保留为旧接口，范围由人工声明限定，范围外皮肤会拒绝；contact的5个深色轮廓点保留为共享原前景。实施报告明确这些保留限制，不把它们隐去后宣称任意剪裁兼容。独立源板可见袖、身、裤、鞋分别存在，最终对照板未见明显肩缘空洞、锄头截断或非衣染色。

几何时序沿用父color-v2西向B：1536×1792、root[768,1544]、density2、四pose时长180/220/140/260ms及整帧登记不变；matching_idle保留既有512×768基线。主代理提供的真实validate覆盖input哈希、原alpha、mask外RGBA、独立槽重建与原几何时序，结果通过。本评审结论仍只适用于本样例固定方向、配方和五姿态，未给未露出的衣料解剖、不同衣摆或全库存混搭背书。

## 原生终核待办

当前五组已冻结；采集脚本新增实际world四姿态及回idle截图，并生成五组1×world板和明暗2×面板。其触发仍为真实控件signals、处理函数与逻辑Input actions，不能称OS键鼠或WM焦点验证。待原生完成后只核对报告/快照/receipt的实际SHA、五配方pose/时序和对应画面，不改绑定输入或重跑已通过资源测试。

## 最终原生证据与范围终核

最终原生目录/private/tmp/coastal-wardrobe-sampling-native；实际report.json SHA256为a58995268633aad5badef314ff3059cecab1f740a7bd6ff88216b33c64e54a22，input-contract.json为f13b6f0063d322d3e14d55ac7207dc8eb63512cd1f3d655c808cfe12b9c0fe36。报告引用该snapshot，receipt引用这两实际SHA，archive_allowed=true、input_hashes_current=true、sample_count=5，三者一致。预快照13:39:06 UTC、原生开始13:39:27、结束13:40:43、验证13:41:17，顺序正确；没有以运行后补采替代本轮预快照。

快照含855个sample输入及继承的1688项保守基线依赖；两集合可能重叠，不能相加当实际运行加载数。scope明确包含静态可达/未执行分支而非运行时文件访问追踪。catalog SHA与冻结8b12f260…一致；抽核trial.gd、SampleLibrary、trial.tscn和本次native脚本当前SHA全部与快照绑定值一致。未重跑全量测试或资源验证。

直接比较报告五clip与当前冻结sample.json：五组sample SHA、recipe完整对象、四pose_id和duration全部逐项对应；harvest正确记录changed_slots=[pants]及原蓝top，不含被拒红稿。119项checks均为true，3928行时间采样，188个continuous/world captures全部文件存在。walk/run各累计3205ms以上，hoe8009ms以上，water/harvest10005ms以上，各到达10个原动作周期且均出现四pose；没有以静态数量替代这项连续时间证据。

报告和采集代码对应覆盖20pose的明/暗停帧、五matching_idle、每组十面板循环、walk/run逻辑Input驱动实际位移，以及三个工具one-shot的四pose锁位和结束回同配方idle。各组保存四张实际world姿态及结束idle，形成五张1×world板；还有五明背景板、五暗背景板。本人独立目视全部五world板及hoe/run暗背景2×板；衣物方向与配方相符，完整工具/水流/作物可见，没有明显截断、肩缘空洞或非衣染色。其余面板完整目视由主代理承担。静帧和时间采样支持本轮动态播放结论，不足以给未测试姿态或全部可组合能力背书。

采集通过真实Godot GPU画面、控件signals/handler及逻辑Input actions完成，脚本主动设focused=true。报告scope明确排除OS keyboard/mouse/focus验证，未拿旧OS输入结论移植为本次新通过。本次画面也不是导出包验证。

首轮JSON数字Array与父整数Array严格类型比较导致apply拒绝，失败目录/private/tmp/coastal-wardrobe-sampling-native-timing-attempt1保留。新child的same_durations仅先检查长度、再逐项float数值严格相等，没有引入容差或更改资源时序。实际数据回归检查五组加载、初始选择、每组idle与首pose纹理，共13项；主代理提供RED→GREEN结果，本评审只读检查未重跑。最终fresh snapshot绑定已修版本，失败运行未合并成成功证据。

最终遗留属于明确下一阶段：用户确认五组视觉风格及细微接口；其他衣物/方向/剪裁、暴露隐藏腰腋的姿态和全库存动态混搭需另行来源与动态验收；生产体系迁移及OS焦点/物理输入不是本轮已通过范围。当前限定交付没有因此新增P1/P2。
