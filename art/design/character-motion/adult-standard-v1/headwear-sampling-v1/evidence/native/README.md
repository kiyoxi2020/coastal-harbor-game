# 原生发帽抽样证据

Apple M4 / Godot4.7.1 Compatibility，2560×1440；434项真实GPU检查通过，18981采样、852采集图。四组×四状态，各明暗idle+四姿态、10面板循环及世界跑步/三工具one-shot、动作中切状态保持时钟、结束idle。控件信号/handler/逻辑Input actions由fixture调用，focused由fixture设置；未验证OS键鼠或WM失焦恢复，不代表用户已认可外观。

- `report.json` 原报告，`input-contract.json`采集前快照，`receipt.json`原采集后核验，均不改写。
- `boards/`32张原生停帧板，`review/`8张明暗四状态合并板+4张世界合并板，`overview.png`实际窗口总览。主代理已目视全部。
- `raw-native.tar.xz`保存原始`sequence/`852张无损PNG；实际解包后885个原生输出（含32板+总览）逐SHA一致，见`archive.json`。
- `videos/`16段原生面板采样VFR预览，帧间隔取report中真实wall_ms，非完整帧率系统录屏；`derived-previews.json`绑定录像及派生板SHA。

在仓库根目录恢复并复核（临时目录必须是新的隔离目录，避免混入其他任务文件）：

```sh
mkdir -p /private/tmp/coastal-headwear-review-restore
cp -R art/design/character-motion/adult-standard-v1/headwear-sampling-v1/evidence/native/. /private/tmp/coastal-headwear-review-restore/
tar -xJf /private/tmp/coastal-headwear-review-restore/raw-native.tar.xz -C /private/tmp/coastal-headwear-review-restore
python3 art/design/character-motion/adult-standard-v1/headwear-sampling-v1/evidence_contract.py validate --contract /private/tmp/coastal-headwear-review-restore/input-contract.json --report /private/tmp/coastal-headwear-review-restore/report.json --receipt /private/tmp/coastal-headwear-review-restore/rechecked-receipt.json
```

复核比较当前源依赖；后续改源或代码使其失败是预期的证据失效，不能改写旧报告或当作新版本通过。源目录历史candidate native_checked=false保持原创建状态，本外部证据只绑定此次实际文件。
