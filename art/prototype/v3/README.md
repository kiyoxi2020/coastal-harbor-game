# 修补渔港：Blender 场景建模 v3

完成日期：2026-10-10。依据已确认的第三版概念图优化现有 v2 场景。本目录提供可编辑三维模型和实际 Blender 渲染，不是 AI 概念图；尚未替换 Unity 试玩版。

## 先看图片

- [日景总览](overview-day.png)
- [旧屋门廊与菜园](old-house-detail.png)
- [补帆鱼摊与潮汐台阶](market-tide-detail.png)
- [黄昏总览](overview-dusk.png)
- [同机位 v2 对照](comparison-v2-same-camera.png)

五张均为 1600 × 1000 的 Blender Cycles 离线渲染。v2 对照采用相同机位、日景光照和曝光，便于比较建模与材质，不用于判断实时性能。

## 文件与打开方式

- `coastal-harbor-v3.blend`：完整可编辑场景，包括环境、日景灯光、相机及原有人物的 22 骨骼和 Idle / Walk / Run 动作。
- `coastal-harbor-v3-environment.fbx`：仅含环境几何与基础材质，不含人物、动画、灯光或相机，不能替换当前人物 FBX。
- `validation.json`：保存后重新打开文件的场景检查。
- `fbx-validation.json`、`export-manifest.json`：环境导出及独立回读检查。
- `source-preservation.json`：原 v2 场景、人物源文件、Unity 场景和 Unity 人物 FBX 的校验值；本轮均未改变。

使用 Blender 5.2.1 LTS 打开 `.blend`，数字键盘 0 查看相机，F12 渲染。人物默认 Idle；选中 `Returnee_Rig`，在 Action Editor 切换动作。Idle / Walk / Run 的循环范围分别为 1–60、1–32、1–24，均为 30 fps 原地动作。`V3_CharacterPlacement` 只负责场景内放置，不改变骨骼动作坐标。

## 已完成的模型变化

1. 旧屋：偏置入口、较低的侧门廊、青绿拼板、重复筒瓦、砌石基座、圆形通气口；新增船板长凳、工作布、晾晒盘和接雨链／盆。
2. 鱼摊：靛蓝起伏帆布替换条纹棚，增加浅色补片、简化缝线、绑绳、鱼形木牌、秤具与小灯。
3. 岸线：模块化岸墙、五级潮汐台阶、带刻度潮位杆；减少整齐排列的岸边石头。
4. 船与码头：赭黄船舷、防撞轮胎、侧舱玻璃、短桅杆、盘绳和修补木板。
5. 植被与菜园：非对称树冠、背景陆地延伸、香草畦、竹架和少量草簇。
6. 材质：移除细碎程序化凹凸，以哑光底色、结构层次和局部色差区分材料。

新增模型按 OldHouse、PatchedMarket、TideQuay、WorkingBoat、WindGarden 分组，名称带 `V3_` 前缀。沿用部分在 `V3_00_RetainedBase`，人物在独立 `Returnee` 集合。

## 验证结果

- 保存后场景检查 **16 / 16 通过**；环境 FBX 独立回读 **12 / 12 通过**。
- 环境求值后 **68,603 三角面**；人物 **56,916 三角面**，合计 **125,519**。
- 环境导出含 **769 个网格对象**；全场景统计 **847 个几何对象、54 个材质**，包含人物，不等同于 Draw Call 数。
- Walk / Run 小腿骨采样旋转约 45.9° / 77.0°，确认动作可驱动骨架，不代表完整动作穿插验收。
- 修正并复测：导入后未激活动作未保留、移动花盆后口沿留在原位。原始文件校验值保持不变。
- 日志有 Blender 未来版本弃用提示及后台模式不启动 Blender MCP 的提示；不宣称零警告，核心检查与渲染均完成。

## 当前边界

这是概念图的第一轮三维落地，不是逐像素复刻。轮廓、人物、树形、局部材质和光照仍有差异，需以实际模型继续审阅。

本轮没有修改 Unity 或新增经营玩法。潮位杆、台阶、鱼摊和菜园目前只是美术资产；没有潮汐模拟、浇水、交易或新 NPC。海面是简化静态表面。

接入 Unity 前仍需整理材质／图集和重复对象、核对单面朝向与缩放、设置碰撞与 LOD、验证台阶通行、重建 URP 光照和水面，并在目标设备测试性能。当前对象数量仍偏多，不把结构检查通过等同于游戏性能达标。

## 重建

项目根目录的 `art/prototype/build_v3.py` 从 v2 派生 v3，`v3_geometry.py` 提供建模组件，`validate_v3.py` 负责场景检查，`export_v3.py` 负责导出与回读，`preview_v3.py` 负责真实渲染。

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python-exit-code 1 --python art/prototype/build_v3.py
/Applications/Blender.app/Contents/MacOS/Blender -b art/prototype/v3/coastal-harbor-v3.blend --python-exit-code 1 --python art/prototype/validate_v3.py -- art/prototype/v3/validation.json
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python-exit-code 1 --python art/prototype/export_v3.py
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python-exit-code 1 --python art/prototype/export_v3.py -- --verify
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python-exit-code 1 --python art/prototype/preview_v3.py -- --view day
```

预览参数还支持 `house`、`market`、`dusk`、`before`。重建会覆盖 v3 生成结果，手工修改前请另存新版本。交付包不含草稿和 `.blend1` 自动备份，这些仍留在项目源目录。
