# 潮港旧屋：可行走原型

将第二版 Blender 场景与返乡青年骨骼人物接入 Unity，验证行走、小跑、镜头、碰撞、地点提示和日夜配色。

## 环境与启动

- Unity `6000.6.4f1`，URP `17.6.0`；依赖见 `Packages/packages-lock.json`。
- C#，当前使用 Unity 传统输入接口和键鼠操作。
- 双击 `Builds/macOS/CoastalHarbor.app` 试玩。
- 或在 Unity Hub 中添加本目录，打开 `Assets/Scenes/Harbor.unity` 并点击播放。
- macOS 是当前本机验证目标；Windows / Steam 仍为计划中的首发目标，尚未构建 Windows 版本。
- 中文字体 Noto Sans CJK SC，SIL Open Font License 随附于 `Assets/Fonts/OFL.txt`。

## 操作

| 功能 | 按键 |
| --- | --- |
| 行走 | WASD / 方向键，方向跟随镜头 |
| 小跑 | 左 Shift |
| 转动镜头 | 鼠标右键拖动 |
| 缩放距离 | 滚轮 |
| 总览 / 跟随 | Tab |
| 日景 / 黄昏 | T |
| 查看附近地点 | E |
| 回到起点 | R |
| 退出应用 | Command + Q |

旧屋、菜地、鱼摊和码头各有文字交互。靠近时显示提示，按 E 查看。种植、收获、交易、存档和联机尚未实现。

## 工程组织

- `Assets/Art/Harbor/`：FBX、9 张 2048 × 2048 底色图和材质记录。
- `Assets/Materials/`：30 个 URP 材质。
- `Assets/Scenes/Harbor.unity`：可行走场景。
- `Assets/Scenes/Harbor-StaticArchive.unity`：接入新人物前的场景备份。
- `Assets/Characters/Returnee/`：人物 FBX、底色／光滑度图集、Prefab 与 Animator。
- `Assets/Scripts/`：角色、镜头、地点交互、光照切换和实机验证。
- `Assets/Editor/HarborSetup.cs`：场景生成和打包入口。
- `Assets/Tests/Editor/`：移动与场景完整性检查。

角色采用 CharacterController；地面、房屋、菜畦、摊位、树干和码头配置独立简化碰撞。镜头对第 8 层碰撞做遮挡检测，人物跌出场景会自动复位。

新人物保留 22 根骨骼，合并为一个蒙皮网格和一个材质。Generic Animator 混合 Idle / Walk / Run，行走速度为 1.35 m/s，小跑为 2.8 m/s，并相应调整动作播放速率。动画读取实际水平位移，撞墙停下时回到待机，复位时清零；位移由控制器负责，不启用 Root Motion。

## 重建与验证

Unity 菜单 `Harbor → Create Walkable Scene` 重建生成场景并提示保存当前修改。它会覆盖 `Harbor.unity`，手动精修后请先另存。

`Harbor → Build macOS Prototype` 打包本机开发版。自动检查在 Unity Test Runner 的 EditMode 页签运行。

实际应用支持 `--harbor-smoke <输出目录>` 参数：自动检查移动、持续撞墙、码头通行和跌落复位，保存日景、黄昏截图及 `smoke-result.json` 后退出。

人物专项使用 `--character-smoke <输出目录>`，自动演示待机、行走、小跑和转向，检查墙体、码头、复位与脚底间隙，保存逐帧画面和 `character-result.json` 后退出。它只在显式传入此参数时运行。

### 本轮验证记录（2026-10-09）

- EditMode 检查 11 / 11 通过：包含原有 5 项，以及人物骨架、材质、三动作循环、UV 图集、朝向／身高／骨骼运动、实际位移和撞墙停步等回归检查。
- 中文界面裁切回归测试先复现失败，再修正提示区域高度并通过；随工程附带字体，避免依赖本机字体。
- 新版 macOS 应用专项 8 项通过：待机、行走、小跑、转向、撞墙回待机、码头通行、跌落复位、地面接触。撞墙实测速度为 0；静止脚底距地约 2.5 cm，为当前碰撞控制器余量，未宣称零滑步或已完成坡地适配。
- 导入预览发现并修复了图集 UV 通道不一致和发顶面朝内的问题；增加回归检查，验证单 UV 通道、18 个色块以及发顶朝外。
- 最终测试报告、日景／黄昏和动作截图归档于 `Verification/Character/`。`character-gameplay.mp4` 为自动路线捕获的真实 Unity 独立应用画面，960 × 600、30 fps、195 帧，共 6.5 秒，并非 Blender 离线渲染。
- 此记录不是性能报告或完整人工游玩验收；尚未在 Windows、低配设备及其他分辨率上验证。

美术烘焙入口位于项目根目录的 `art/prototype/prepare_unity.py`，读取第二版源文件，输出到 `art/prototype/engine-ready/`。重新导出后需将 FBX、PNG 与 `materials.json` 同步到 `Assets/Art/Harbor/`。

人物导出与校验入口为项目根目录 `art/characters/returnee/export_unity.py` 和 `validate_export.py`，独立输出到同级 `engine-ready/`，不改动 `v1/returnee.blend`。将 FBX、两张 PNG 与 `clips.json` 同步到 `Assets/Characters/Returnee/` 后，可使用 `Harbor → Create Animated Character` 重建人物资源，或通过场景重建菜单一并更新。导出图集为纯色色块坐标，不是用于手绘细节的展开 UV。

## 当前限制

目前迁移了程序化底色。Blender 凹凸尚未烘焙为法线，海面静态，实时光照与离线渲染存在差异。尚未完成低配设备性能优化与发布适配。

人物尚无手指／面部动画、坡地脚部 IK、Humanoid 重定向和 LOD。当前动画验证不等于完整动画系统或经营玩法完成。Mac 包为本机开发版，未作分发公证，尚未构建 Windows 版。

本机开发版日志包含未启用的 Gaussian / Bokeh 景深、Panini 投影着色器被剥离或不受支持的警告；这些效果不在当前画面方案内，不能据此宣称整份日志零警告。当前使用的色调映射与实际画面已通过截图核对。
