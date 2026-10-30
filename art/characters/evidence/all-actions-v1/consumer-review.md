# T03全包消费者独立复查

**结论：尚不PASS；3项Important，2项Minor。无Critical。** 以下针对本次复查的冻结内容；主代理已开始修I1，后续未完成改动不混入本结论。实际完整美术与native validator尚未完成是已知范围，不作为新bug。

## Important

### I1 固定全包范围没有绑定实际母版、动作集和五个设计身份

位置：`tools/characters/review.py:59`、`:103`；`godot2d/dev/characters/character_construction_samples.gd:237`—`:247`；`character_headwear_trial.gd:152`固定衣装UI声明。

`full_action_clips`仅验证24格与hair_hat；Godot也只检查通用template_id、category与head_state，没有要求规格的adult-standard-v1/review-motion-v1、top03/original-pants/original-shoes、hair-chestnut-short-v1/hat-straw-navy-band-v1。完整测试包实际是template=test、只有top槽且design_id=top、hair/hat ID=hair/hat，依然被称为固定成年配方并安装固定衣装说明。

真实复现：将提供的strict-built fixture02复制为`/private/tmp/coastal-consumer-review-fixed-scope`，只将Godot测试重写的suite整数浮点表示恢复成Python整数。`review.construction_preflight(root, root/'art/characters/reviews/full/review.json')`返回成功。Godot同包`accepted=true`，`samples[0].data.recipe.slots={top:top}`，连pants/shoes都没有。日志`/private/tmp/coastal-consumer-probe.log`，脚本`/private/tmp/coastal-consumer-probe.gd`。

影响：其他完整配方/体型或缺少本轮衣装槽的包可被当前正式all-actions范围误接受。通用schema3与组件mapper应继续泛化；固定交付scope另绑定准确身份。测试合成像素可保持测试用途，同时使用明确实际身份。本项主代理已确认并安排修复，本报告不提前认可新修复。

### I2 Godot只核manifest已列条目，漏掉被移出inputs的实际传递依赖

位置：`character_construction_samples.gd:70`—`:78`、`:226`—`:235`。

`references_bound`仅遍历head/base recipe内直接ref，遇到adaptations ref只检查JSON本身的SHA，没有继续读取adaptation中的typed compatibility、annotation、selection等实际依赖。循环manifest.inputs也只能发现仍列出的文件变化，不能验证实际闭包完整性。

隔离复现`/private/tmp/coastal-consumer-review-missing-claim`：从合法full fixture的manifest.inputs移除`parts/hair/adaptations/test/motion/r002/compatibility/under_hat_hair.json`，将该claim改成无效内容；重算manifest artifact_digest与suite的manifest SHA。未改引擎、adaptation、配方或PNG。Godot仍`accepted=true`；Python preflight正确报`ValueError: SHA mismatch: .../compatibility/under_hat_hair.json`。同一probe日志证明两侧差异。

影响：Python launcher可拦截，但直接Godot `--construction-suite`/loader路径无法维持其声称的完整输入闭包，实际兼容输入变化可不使输出失效。需检查构建实际消费的传递ref，而非仅声明inputs。不要盲目把source bundle中所有未使用历史asset/prompt都强制视为运行依赖；本反例claim是composition必读输入。

### I3 全包trial仍先依赖旧locomotion/run/farming/五样例库启动

位置：`character_headwear_trial.gd:19`先`super._ready()`，`:28`用旧sample_error/load_error阻止全包加载；`character_wardrobe_trial.gd:18`起旧库初始化；`character_headwear_trial.gd:125`依赖旧路径生成的farming_library。

真实隔离复现：`/private/tmp/coastal-consumer-bootstrap-probe`包含完整提供fixture、对应三份Python engine及复制的Godot工程/UI/世界资源，只省掉旧人物资源库与Godot cache。直接`HeadLibrary.load_samples`为true；同一现有trial场景指定full suite后，`full_package=false/head_ready=false`，错误“抽样目录必须明确包含五个样例。”日志`/private/tmp/coastal-consumer-bootstrap.log`，脚本`/private/tmp/coastal-consumer-bootstrap-probe.gd`。

进一步手动注入合法full library调用installer，仍在`:125`访问Nil的`.clips`，证明只绕过旧错误判断还不够。日志`/private/tmp/coastal-consumer-event-order.log`。需独立完成共享UI/输入/预览容器初始化，不能先要求旧人物动作库加载成功。共享世界/UI美术依赖与旧字符动作依赖是不同范围。

当前full_trial GREEN测试在旧人物库齐全的真实仓库中先创建场景，再手动注入新library，掩盖了这个启动依赖及预览绑定条件；未覆盖合法新包在无旧人物资源下启动。

## Minor

### M1 full_loader测试恢复suite时改变了JSON数值表示，污染后续Python预检

`test_character_construction_full_loader.gd`读取parse后的original，再`JSON.stringify`写回。Godot写成schema_version2.0、runtime version1.0、at_ms100.0、transition duration100.0，而Python严格要求type(int)。提供fixture02当前即是此状态：Godot接受，Python会按错误schema分支或runtime整数条件拒绝。

建议测试恢复原始bytes；若选择两侧统一数值语义，应显式定界，不因为Godot内部全用JSON number而无意放宽Python合同。此项是测试恢复/预检一致性，不是有效PNG被误渲染。

### M2 合法多事件配置允许乱序，低帧率越过时日志按数组顺序倒时记录

`review.validate_runtime`与Godot `runtime_valid`不约束events按at_ms排序；`character_headwear_trial.gd:208`附近`record_action_events`直接遍历配置数组。

定点probe给hoe-south配置有效`late@250/pose2`、`early@100/pose1`，runtime_valid=true，一次advance1s日志为late250、early100、complete300，同一instance、无重复但时间倒序。日志`/private/tmp/coastal-consumer-event-order-initialized.log`，脚本`/private/tmp/coastal-consumer-event-order-probe.gd`。为隔离I3，该probe显式初始化了共享farming容器/preview trial绑定；未修改共享代码或正式资源。

当前fixture每动作只有一个contact，因此未影响现有contact+complete GREEN；若合同允许多事件，应要求配置非递减，或按越过时间顺序发出。

## 已检查且未发现同等级新问题

农事start通过refresh_pose先产生新instance，然后处理at_ms=0事件；跨帧用(before,after]区间和实例内event_id去重；completion先记录再回idle，下次重播产生新instance。农事倍率作用于同一elapsed，失焦在推进与事件处理前返回；转向/移动锁沿同一farming_clip维持。walk/run世界pose相位基于实际位移，UI预览是独立时钟。stable-idle路径在世界物理入口阻断直接walk/run同帧号切换。声明geometry、pose顺序、每PNG canvas/RGBA、全24clip/20samples、canonical四idle、头部唯一hair_hat、当前三份Python engine均有实际检查。

这些是代码/合成fixture范围结论，不代表实际足握接触、屏幕≤1px、持续动作或美术验收。

## 版本与验证范围

复查Godot冻结副本保留在`/private/tmp/coastal-consumer-bootstrap-probe/godot2d`：

- construction_samples SHA `02acb3a72690c8dd9c7adc373d2dcb8fd51e6f86107859be8c22e5d42bc87452`
- headwear_trial SHA `f8eea7998025ed85d2caff1e4e1ec8fbc1818bce6b3433d8262d5dd892405cbe`
- headwear_samples SHA `213c0bd08f24680b85c5f9ea18d0e62ac1efb915c7ac063f73f2421659df18b5`
- motion_review SHA `00739837498727716e5f6e802b6d411c8cc6f6bfcc9f74eeeb185d341c191032`
- full_loader test SHA `72432062c09014b1bdc702618bcbc85c7e72c00ddd1b49a6b50afafac5cec02d`
- full_trial test SHA `ff8ae87f36f7fa85d4827a37fc5e42bddaf2eb9a480c880f5b5a9e4caa3752af`
- 已读review.py SHA `e515b02fe4c1cf26153b84e07863522b8370250a8d9ee883d3a2a6143caa429f`

独立执行上述Python预检正/负探针与Godot定点探针；均在/private/tmp资源上。未改共享代码，未提交，未重跑已GREEN195工具测试或149/72/旧路径套件。原149 GREEN日志已读，不能覆盖本报告的三个反例。
