# I3 full-package bootstrap修复交付

完成并冻结，仅修改独占范围：

- `godot2d/dev/characters/character_walk_trial.gd`：将原_ready中输入/CLI、相机和既有UI信号的共同前缀提为`initialize_trial_shell()`，一次初始化；原_ready继续调用该前缀，再按原顺序加载原locomotion/run/farming资源与原逻辑。没有第二套物理或动作播放器。
- `godot2d/dev/characters/character_headwear_trial.gd`：识别全包suite后先用同一HeadLibrary完成全包校验，再初始化共享shell并装入全包，直接返回；不进入wardrobe/walk旧人物库_ready。安装器显式初始化既有farming容器、preview绑定/可见性、固定衣装控件与当前pose，消除对旧初始化副作用的依赖。坏full包关闭显示、拒绝动作，不回退旧人物库。schema1 construction和默认旧headwear仍走旧_ready链。
- 新增`godot2d/tests/characters/test_character_construction_full_bootstrap.gd`：从实际临时工程根启动现有场景，使用真实strict-built完整fixture，明确要求五个旧人物库入口缺失；不手动注入library、不手动创建farming容器或preview绑定。覆盖实际_ready、四向六动作预览、12次农事、world移动/stop、UI速度/重置信号、失焦、坏full包失败关闭与不回退。

## TDD证据

修改实现前，新测试在合法full fixture loader成功后出现预期RED：`ready_loads_full_package_without_legacy`与`ready_has_no_old_loader_errors`失败，错误“抽样目录必须明确包含五个样例。”见`/private/tmp/coastal-full-bootstrap-red.log`。

修复后基于主代理fixture03完整固定身份、复制的Godot工程及其世界/UI美术，临时根`/private/tmp/coastal-full-bootstrap-fixed-03`内仍没有locomotion/run/farming/wardrobe/headwear五个旧字符库。两条实际启动路径均GREEN：

| 验证 | 结果 | 日志 |
|---|---|---|
| 真实场景_ready，override指定suite | 103 checks PASS | `/private/tmp/coastal-full-bootstrap-fixed-03-green.log` |
| 真实`--construction-suite` CLI启动 | 103 checks PASS | `/private/tmp/coastal-full-bootstrap-cli-green.log` |
| 现有full_trial回归（fixture03） | 原149 checks PASS | `/private/tmp/coastal-bootstrap-full-trial-regression.log` |
| 旧walk/idle locomotion | 28 checks PASS | `/private/tmp/coastal-bootstrap-legacy-locomotion.log` |
| 旧headwear trial | 90 checks PASS | `/private/tmp/coastal-bootstrap-legacy-headwear.log` |
| 旧四向农事trial v2 | 122 checks PASS | `/private/tmp/coastal-bootstrap-legacy-farming.log` |

`git diff --check`对两份修改脚本通过。Godot日志只有当前macOS环境既有`get_system_ca_certificates`的ret/noErr提示；无SCRIPT ERROR、测试FAIL或非零退出。测试不读写玩家存档。

## 冻结SHA

- walk_trial：`ba140f0debfd860e482b8351a377b9f32a57a0bb82a8ba31cc412a9e50e45c28`
- headwear_trial：`ae8c43b8a167fdbfa3f056ad8ab5f3daac17b36e6f2a4f84350d509db82551f0`
- 新bootstrap test：`4806180f17a7c2c0b71fa82e322914551e67c95266453d165f0f6f0e2b0631e9`

原消费者复查的冻结临时副本`/private/tmp/coastal-consumer-bootstrap-probe/godot2d`已恢复至修前headwear_trial SHA`f8eea799...`，保持旧I3复现可审查；新GREEN工程另存上述fixed-03目录，没有以新结果覆盖原RED证据。

## 边界与交接

未修改共同Python engine、loader、full_trial/full_loader测试、任何实际资源/manifest/baseline；未提交。主代理已确认在其他T03修复冻结后统一执行Python discover/check最终门禁，本子任务未重复跑之前195套件。实际完整美术、原生渲染、屏幕接触/连续动作与生产发布不由本次逻辑fixture授予认可。

共享shell只拆原有初始化前缀；旧路径的资源加载及UI策略保留，现有full_trial也仍可在既有场景上安装合法full library。I1身份门禁、I2传递闭包及事件排序由主代理独立负责，本报告只交付I3及受影响旧播放器回归。
