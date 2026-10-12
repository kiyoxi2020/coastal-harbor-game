# 返乡青年 · Unity 导入资产

从已验收的 `../v1/returnee.blend` 生成独立副本，原 Blender 文件不改动。

- `returnee.fbx`：一个蒙皮网格、一套材质、22 根骨骼，含 Idle / Walk / Run 三组原地动作。
- `palette.png`：18 色底色图集，sRGB；`surface.png`：非颜色数据，Alpha 为光滑度，RGB 为零金属度。
- `clips.json`：动作帧范围、帧率与标称步幅速度，供 Unity 配置播放速率。
- `returnee-engine.blend`：导出中间副本，保留原生骨架与关键帧。图集图片在本目录；移动此副本时请一起携带。
- `export-validation.json`：FBX 重新导入后的独立检查结果。

合并前应用造型细分、倒角与衣物厚度，并在静止绑定姿态下统一图集 UV 名称。游戏副本修正了头发主体内向面朝向，使用常规单面渲染。所有 18 个颜色单元都必须保留，避免部件丢失 UV0 后错误取色。

这里使用色块图集 UV，不是为精细绘制皮肤／布料纹理准备的完整 UV 展开。一个蒙皮网格与一个材质减少了部件切换开销，但不代表已完成低配性能优化、LOD 或发布级拓扑整理。

当前 Unity 使用 Generic 原骨架播放，不是 Humanoid 重定向。Unity 正前方通过 `ForwardMarker` 校准；根运动关闭，角色位移由碰撞控制器负责。

重建顺序：运行上一级 `export_unity.py` → `validate_export.py` → 将 FBX、两张 PNG 和 `clips.json` 同步到 `unity/Assets/Characters/Returnee/` → Unity 菜单 `Harbor / Create Walkable Scene`。场景生成器保留首次接入前的 `Harbor-StaticArchive.unity`，后续手工精修场景仍应先自行另存。
