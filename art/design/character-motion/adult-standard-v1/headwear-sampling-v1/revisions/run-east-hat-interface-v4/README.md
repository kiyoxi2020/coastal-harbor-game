# 东向帽口恢复 v4：未通过，不接入试玩

当前路线按用户“遮罩方案改成直接调用imagegen吧”使用内置 imagegen，遮罩是可视参考而非硬mask参数。无需 API 密钥；没有实际调用API。`masked-edit-preflight/` 与 CLI dry-run 仅是历史备选，已标记 superseded，不能再将密钥列为当前路线阻塞。

## 实际制作与结果

冻结合同和mask在 `contracts/`，由复用的 gpt-6-astra/high 提供，主代理不修改合同迎合源图。原身体、整帧零placement、完整方形窗口nearest归一、帽冠/帽带/外轮廓冻结要求不变。原两份局部源及提示词仍在 `sources/`；八个剩余接触点仅是一项源完整性阻塞，补查还发现旧v2侵入紧邻开口650点、完整可见头带926点，故新尝试必须重做整条内唇。

`builtin-mask-edit/manifest.json` 绑定本轮两次实际内置调用的目标、可视mask、提示词、原始输出与归一图SHA：

- `source-v1.png` / `prompt.txt`：完整接触带与放大导图编辑。模型把帽冠下移44px并放大外框约8%；虽然接触464点全覆盖，却把开口928点和完整可见头带2831点全部盖住。`source-v1-screen.json`记录拒绝；不靠挪缩配准补救。
- `wearing-source-v2.png` / `wearing-edit-prompt.txt`：根据首稿居中漂移证据，改用固定原身体+帽的完整穿戴画面编辑。布局更近，但近侧真实边界左段低于、右段高于固定曲线；指定帽面位置仍有生成皮肤，不能作为合格帽接口。输出全不透明，alpha255不是帽归属，不能把生成身体、背景或脸边采用进部件。`source-v2-screen.json`保存具体源点反例及拒绝。

两份均未合成合格候选或接入活动catalog。可视mask提示不是模型内的硬约束。两次后停止同类尝试，不继续第三次参考图重试，不裁出未经创作的新帽边、改alpha、任意挪缩，或把超出的近侧帽沿假称远侧。没有接纳生成脸、身体或中性底色。完整新源保留供审计；不得把工具返回图片称为已验收游戏画面。

## 验证与未完成

复用gpt-6-astra/high独立只读复查。新增两个先失败的检查反例后最小修复：实际选帽层alpha也须达到实体门槛，不能由底下不透明身体掩盖；侵入检查包含整个 `visible_head_in_edit_band`，不限于前四行开口。`contract_checks.py`、`audit_baselines.py`及 `test_interface.py`相应更新。

`python3 -m unittest discover -s <本目录> -p 'test_*.py'` 七项工具测试通过。旧提取与ownership回收在加强门禁下仍失败，记录为 `baseline-failures.json`；冻结合同SHA为 b79157cf8428165211d9146765a3162fb0835969bbd2a57f5a4a7b790b7031a4，全部mask哈希未变。

工具测试不代表美术通过。本轮没有合格新帽合成，没有新版Godot原生截图或连续动作验收；旧434项不作为此轮视觉证据。原身体/已认可美术/活动目录不变，hair_hat及东跑四姿态未展开。下一步需要符合固定接口的真实GPT帽源，或明确的新接口设计，不能静默放松曲线。未提交、推送或导出。
