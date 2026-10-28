# 条纹西向锄地：帽头贴合与遮挡修复

修复范围为 `hoe-west` 待机与四个锄地关键帧。东向已认可 v5、原人物脸/身体/条纹衣/锄头、原裸头和完整短发状态及动作时序均保留。

旧待机帽切图混入生成皮肤，旧运动遮罩按每列帽下沿无限向上删发。新帽层只提取真实帽面，按完整头部核实整源登记；近远帽面分离，按远帽→原人物→兼容帽下发→近帽合成。key1 复用兼容的原完整发，其余四姿态使用 GPT 生成并提取的帽下可见发片，完整 hair-only 资源保持。

原图、提示词与窗口回填映射见 `under-hat-hair-sources/`；帽归属/近远面与登记证据见 `extraction/`；发片及其对应帽 manifest SHA 绑定见 `under-hat-hair-extraction/`。窗口回填不是部件登记；运行时使用已经登记的完整画布，placement 为零。

已构建 `sample-build/sample.json`，活动 `headwear-sampling-v1/catalog.json` 仅更新 hoe-west。10 个独立合成逐 RGBA 检查通过，裸头、完整短发、时序及其他三个目录条目保持；五姿态帽审计 55 项、四姿态帽下发审计 48 项通过。工具回归 4 项与真实资源加载 98 项通过。

Apple M4/OpenGL 原生 GPU **114 项全部通过**：四种头部状态各十循环、五姿态明暗停帧、世界四关键帧、挥锄启动、动作中切换保持时钟、动作结束匹配 idle；2408 次时序采样、201 张采集 PNG、210 项输出。原始证据完整保留在 `evidence/native-02/`，输入与全部输出 SHA、严格覆盖/时序及四个实际调用校验工具的绑定均通过，`archive-receipt.json` 的 archive_allowed=true。原生报告仍绑定冻结候选，不为改验收布尔重写 sample。

主代理已查看 8 张原生明暗板和帽/发帽的世界四姿态图，未见明显空缝、露头皮斜条、穿冠/带或裁檐。源软边差异未补色掩盖。原生有时序采样与截图，未录逐帧连续视频；未验证 OS 键鼠、跨平台、导出包，用户已明确认可本修复效果，绑定见 `visual-acceptance-2026-10-28.json`；冻结 sample 和原生证据不改写验收布尔。

双击 `launch-hoe-review.command` 可直接打开条纹西向锄地，默认短发＋草帽；`before-after-common-root.png` 是离线对比，`hoe-hair-hat-offline.gif` 是按原时长播放的离线资产预览，实际 GPU 五姿态见 `evidence/native-02/boards/hoe-west-hair_hat-dark.png`。

实施提取由 `gpt-6.1-sol/high` 完成；主代理负责构建、集成与 Godot 原生验收。内置 imagegen 不使用本地 API 密钥。用户要求本地提交相关文件；未推送或导出。
