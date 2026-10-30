# 南走 0 top03：有限真实布料登记

完成的是 frozen `walk_south_0` / variant B 的单姿态材料视图，状态 review-only。没有截短 canonical clip、创建单帧配方或构建，也没有原生动态或用户认可。其它三帧与 idle 仍待补齐。

## 实际源与投影

新包 `sources/gpt-top03-walk-south-0-trim-v1` 保留 GPT 原始完整 1024×1536 PNG、两次提示词、实际使用的参考与 SHA。r005 是完整 shirt-only 原图；r007 是完整 pose 编辑原图，但生成的脸、手、身体、裤鞋均不进入新部件。二者均整源 NEAREST 1/2 到 512×768，源帧 root [512,1416] → canonical frame root [256,708]；源到目标 anchor 差 [0,0]。这个 root 是冻结完整参考画布的注册坐标，不声称孤立衣物具有可见人体 foot root。没有部件缩放、局部平移、任意裁切或补色。

r003/r004 虽曾通过 30655 点 alpha 诊断，下摆和袖腕 ribbing 实际低于冻结版型，因此本次不选用。r005 主体的 ribbed hem 位于约 y506–519，能跟随原有腰线；r006 试图补边后反而收窄，拒绝。随后以完整 B4 pose 作编辑目标生成 r007；它的非衣物变化不能当 body 使用。

## 覆盖与真实边界

旧 30655 点池来自命名 torso/sleeve 纹理及现有可见分层，纹理里本身带有颈部皮肤、棕色裤腰与中性轮廓，不能把这个池全部认作布料。例：B4 (222,381)=(152,95,76,253) 为颈部皮肤；(295,520)=(64,56,37,253) 为裤边。中心蓝布最后一点 (255,518)=(59,83,108,253)，下一行 (255,519)=(30,26,21,253) 已是棕黑腰线。把这些点补成 navy 会改坏原皮肤/裤子。

采用经 collar、肩、左右袖腕和腰线逐区对照的有限可见蓝布材料表面 29586 点。旧池剩余 1069 点保持冻结原 RGBA；黑色/中性原轮廓也保留。调色与 alpha 检测仅用于提出候选，正式归属是本次保存的人工语义核验二值 PNG，不能把颜色规则或 alpha 门槛单独当正式 mask。`semantic-boundary-review.png` 同列原图、材料结果、未覆盖池与 r007 选择点，供复核。

r005 提供主体与 trim；r007 仅选入 434 点真实边缘布料。候选按 r005 缺材点定位后检查 source7 实际皮肤、轮廓与接缝，选中的点均属于该姿态 cloth，不选其偏移手肤。三空间显式登记：raw1024×1536、normalized source512×768、target512×768；二值选择先在 normalized source 空间进行，随后用独立 source ownership 提取，再按 canonical anchor 映射。selection、source ownership、target coverage 分开文件/角色，软 alpha 不重复相乘。登记材质点 alpha 最低 200，保留原始 RGBA。

`source-visible-material-ownership.png` 不是通用完整衣物层；完整原图仍保存，当前 view 只承诺前景已经确定的可见材料。早前 139 点 hidden sidegap 的完整 B 层能力没有因此补齐，也不声称支持新遮挡或不同下身。

## 登记文件

- `parts/top03/revisions/south-walk0-r001/design.json`
- `parts/top03/adaptations/adult-standard-v1/review-motion-v1/south-walk0-r001/views.json` 与 masks/textures。
- `templates/adult-standard-v1/motions/review-motion-v1/annotations/south-walk0-r001/poses.json`：SHA 绑定原 r001 canonical poses、variant B、同 pose 原 frame 与 geometry；不修改共用 r001。

采用既有 `normalized-source-selection-v1`，base=r005、additional=r007，二者均绑定实际 raw PNG、同一完整 source bundle、相同 source_pose annotation 和各自 whole-source normalization。view/mapping 名 `walk-south-0-visible-material`，anchor 名 `canonical-frame-root`。coverage 绑定 `visible-shirt-material` / `body` 表面，composition 为 ownership-replace；无 occlusion。后续完整 clip 可直接引用这个真实适配，不需离线合成后伪称 GPT 源。

## 验证与限制

临时测量入口 `/private/tmp/coastal-south-walk0-admission/register.py` 调用公开 `RegisteredAdaptations.component`，重新读取两个 raw PNG、source bundle、独立二值选择/ownership、annotation、canonical poses/action/frame 和登记纹理，逐 RGBA 重建一致。它是单组件准入探针，不是新增合成器或正式构建入口。receipt 在同目录 `component-registration-receipt.json`，正式适配目录另保留副本。

目标 coverage 外的 RGBA 改变量为 0：原脸、颈肤、手、裤鞋、轮廓均保持不变。512×768 诊断与约121×182逻辑显示尺寸静态预览已目视检查；原源/领口/肩袖/腕/下摆的对照没有沿用 r003 的下垂 trim。完整 clip、Godot原生显示与连续运动、服装切换、四向及用户视觉认可均未验证。`build verify` 未运行，因为不能伪造缺失的完整 walk/idle 资源。


最终工具门禁：`python3 -m unittest discover -s tools/characters/tests`：196 tests，135.799s，OK；`python3 tools/characters/check.py`：passed=true，strict_recipes=5，strict_builds=4，frozen_legacy_recipes=9，production_release closed。日志分别为 `/private/tmp/coastal-south-walk0-admission/character-tests.log` 和 `character-check.log`。作用域内 diff whitespace 检查通过。没有提交或推送。
