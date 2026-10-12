# Unity 用美术资产

从 `../v2/coastal-harbor-v2.blend` 派生，原场景保留。

- `harbor.fbx`：879 个带材质的网格，保留对象命名用于角色拆分和碰撞配置。
- `*_BaseColor.png`：9 张 2048 × 2048 底色图，分别为 Coral、Deck、Grass、RoofLight、Sea、Soil、Stone、Wall、Wood。
- `materials.json`：30 个材质的基础色、粗糙度、发光强度和贴图名称。
- `harbor-baked.blend`：烘焙场景，用于进一步编辑。

原程序化底色已烘焙至 UV。细微凹凸暂未导出为法线图；Unity 中使用 URP Lit 重新设置材质和光照。程序入口为 `../prepare_unity.py`，再次运行会覆盖本目录的生成资产。

已将这些模型、贴图和材质信息接入项目根目录的 `unity/Assets/Art/Harbor/`。烘焙源场景中的图片使用本机路径，跨设备传递时应在 Blender 中打包资源或重新定位本目录贴图。
