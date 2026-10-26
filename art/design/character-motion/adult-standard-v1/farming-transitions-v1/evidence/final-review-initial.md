# 农事续作最终跨交付评审

评审：gpt-6-astra，high。只读检查，未重跑已有211项逻辑、78项原生、两块各8项静态板检查，未修改项目文件。本报告针对限定三项交付，不判定完整人体管线或生产农事完成。

## 结论

- 规格符合：三项限定范围基本符合；未发现P1。当前有1项P2证据依赖绑定缺口，补齐后可通过本轮合同评审。
- 质量：世界衔接实现和诊断候选可作为本轮交付。两新候选的完整源、登记、依赖及能力边界诚实；原生静态参照可靠。图像可审阅不等于几何/接触通过或用户认可；保留的完整动作、分层及生产任务无需在本轮强行补齐。

## P2：世界衔接原生证据未绑定实际走跑/idle及世界渲染依赖

位置：godot2d/tests/test_character_farming_transitions_native.gd:87–92，及 farming-transitions-v1/evidence/native/report.json 的inputs/ clips。

报告inputs仅含trial脚本、trial场景、farming loader、catalog、native测试脚本五文件；clips绑定三份农事candidate及其姿态时长。未绑定实际加载的locomotion export-manifest及其纹理/源合同、run candidate及run-garments、场景递归依赖、world_camera及project.godot。这些输入参与从run进入、结束idle、换B、场景缩放和画面，却不能从报告证明其版本。

可复现方式（无需改变仓库）：比较report.inputs及clips与实际加载路径，可见上述清单不存在。若在副本中只替换locomotion的idle输出并同步其清单，或只改变WorldCamera/project渲染配置，既有report列出的文件和三个农事candidate仍全部哈希相同；只核对现有inputs的“input_hashes_current”仍会成立。证据不会随其实际依赖失效。

这不是当前78项原生结果失败，也不意味着当前美术被改动。是人体规范§7/§9所要求实际输入依赖闭包与后续失效规则未完整落盘，影响本轮可追溯性。

最低修复：可新增独立post-run dependency-contract.json，不改已有report或认可素材、不无故重跑原生。绑定原report/checks/native测试脚本、locomotion清单及实际纹理/source_contract、run candidate/inputs/纹理和已加载run-garments/inputs、trial递归静态依赖及project.godot。明确这是补充关联而非运行时采样，并保留本次运行到补证期间这些文件未改的依据。验证器拒绝缺失类别及任一绑定文件改动。后续归档应强制该合同通过，才给出整体input_hashes_current=true。

主代理已提出上述补证方案；该方案能解决此P2。最低验收为当前合同通过、/private/tmp副本中缺locomotion/run/world合同各被拒绝、代表性的idle/run/world文件改动各被拒绝。不需要扩大玩法或画面测试。评审时补证尚未实施，本报告不提前记为已修复。

## 已核实的跨交付合同

1. 认可素材保护：git diff仅修改隔离trial脚本；新增目录各自独立，旧catalog/候选/纹理不在修改列表。world从现有farming library取得west/A并按源时序播放，south/A与west/B候选未写入catalog。未知方向/上衣明确拒绝，没有自动转向换衣。
2. 世界与诊断分界：world只增加显式开关下的一次播放、移动/方向冻结、结束idle、排队换衣、重置取消、失焦暂停；未派发农事事务。硬切、两姿态water/harvest不是完整动作已明确写入交付。独立候选accepted/native_checked/modular/gameplay_available未冒标通过。
3. candidate依赖：直接复核两个新candidate的全部inputs、输出纹理SHA-256均无不一致；candidate完整文件哈希与native-static报告一致，报告中capture脚本哈希也匹配当前脚本。water implementation-report所列artifact_digest与native报告candidate_sha256不同是语义digest/文件digest两种口径，不是陈旧文件证据。
4. 比例/登记/时序：water 1280×1728/root[640,1480]，hoe-B 1536×1792/root[768,1544]，display_scale均138/1164、源密度为idle两倍。整数整帧平移保留完整源图。world时序water500/500、hoe180/220/140/260、harvest500/500与报告一致；hoe-B仅ready/contact180/140，loop/review_repeat=false，文档未偷换成完整循环。
5. 同向同衣原生板：脚本按candidate.direction及garment查询认可locomotion manifest中的idle条目，不按固定索引猜测。water实际取idle_south_0/A，hoe-B实际取idle_west_0/B；相应文件哈希由报告绑定。候选按自身root/scale、nearest渲染，idle按当前冻结512×768/root[256,708]/138÷582基线渲染。明暗、1x/2x板已目视，完整工具/水流在画面中，无明显背景矩形或裁去工具。
6. 诊断候选局限：water头部投影与参考偏差、root推定/非批准轨迹、隐藏关节null、工具刚性及精确握点未通过均明确记录。hoe-B缺lift/recovery、完整穿衣图不等于独立衣物/隐藏身体/动态兼容，袖腕/腰接口及A/B同身体还原仍留待下一阶段。没有把两静态板的8项结构/捕获检查当作接触或运动验证。
7. 生产/存档隔离：新启动器明确加载dev trial而非harbor入口；project.godot无autoload，trial所含world外景/相机不读写玩家档。新行为不改生产场景、碰撞或业务。日志与测试证据落在/private/tmp/coastal-*。测试继承的native助手仅复用输入/截图/结束方法，运行覆写创建trial，不启动其原生产测试run。

## 非本轮缺陷，保留后续工作

- 没有新工具收放过渡帧；现有硬切是本轮明确范围。
- 南向water和西向hoe-B仍待用户视觉评审；两关键姿态不能证明完整动作或精确支撑/握点。
- 农事分层、隐藏身体、衣裤鞋/发帽组合、完整轨迹、四方向、世界遮挡碰撞和正式生产迁移尚未完成。
- 原生静态README补充段解释native_checked=false保留制作时状态；子任务implementation-report中的“未运行Godot/后续独立审查”是历史子任务范围，有README的后补记录，不构成虚假原生声明。可在最终交接用统一时间口径提升可读性，但不列为P2。
- 169张连续捕获来自原生viewport下采样到1280×720；“无损归档恢复”只指保存后的PNG可无损恢复，不应扩写为169张全分辨率原生停帧。现有报告没有做后一声明。

## 评审限制

未复跑测试或重新生成素材；未独立重看169帧全序列、未验导出或跨平台；本次依据实际代码/候选/报告、源依赖哈希核对及两张原生诊断板。Task1具体逻辑另有窄评审，本报告不重复替代该评审。
