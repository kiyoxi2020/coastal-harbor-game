# V5默认主角接入

用户要求将当前游戏人物替换为V5，使用Progress记录。本次默认主角已接入已认可的adult-v5/r012像素风完整动画；NPC及制作母版选择仍保持现状。本地开发接入不授予完整统一发布、动态换装或严格接触资格。

## 运行数据与精确变更

现有godot_integration.py从`art/characters/builds/adult-v5-pixel-visible-r010`严格重建核验后复制108帧，输出`godot2d/assets/characters/integrations/adult-v5-pixel-visible-r010`与`godot2d/resources/player_body_v5_frames.tres`。默认`player.tscn`替换SpriteFrames和整帧offset=(-125,-201)，保持0.25缩放、nearest、10×6碰撞及玩法/存档。24动作方向全部切换，无旧帧回退。

最终美术仍在`art/characters/parts/body/adult-v5/r012/atlases`，archive-r010的440文件SHA全部匹配。9图集和164源姿态未重绘，运行108帧逐RGBA匹配严格构建；24组时序与旧默认包一致。源帧260×228，世界画布65×57；相机4倍下内部显示画布260×228。原生渲染2560×1440，窗口2418×1516；按等比适配宽度估算画布约246×215屏幕像素。已查看原生主场景与走跑/农事/门采样，未见旧人物帧、缺工具或注册错位。

基线精确新增110项（108PNG、manifest、SpriteFrames），只修改玩家场景1项哈希，其他119旧冻结项全部保留。增加新SpriteFrames保护/108纹理引用及local_integrations登记，玩家引用仅指向V5。旧V4文件保留现有跟踪，不额外删除或重采整份基线。对应校验器及生产发布门禁未放宽。

## 验证

- 先将现有玩家测试预期切换为V5，旧场景出现绑定、几何和manifest缺失失败；完成接入后469项通过，含实际导入RGBA、尺寸、时序、动作完成与无效农事提交保护。
- 严格`godot_integration.py verify`及独立`verify-runtime`均通过24组108帧。
- `check.py`通过4严格配方、4严格构建、0旧配方、2本地接入，正式发布关闭。
- 原生`test_body_game_native.gd`171项通过；走跑四向至少十循环、农事四向、暂停/恢复、树与柜台前后、双向门过渡。4584时间采样、521临时截图；原生前后1215项冻结输入SHA一致。

- 人物Python全套504项通过（237.921秒）；日志中的拒绝错误为预期反例，unittest最终OK。
- 实际四晚耕种、浇水、收获、重载原生150项通过，最终第5日场景已目视检查。
- `git diff --check`通过。无本轮未解决阻塞。

原生导入有沙箱无法保存用户级Godot编辑器设置的环境提示；实际GPU加载、RGBA检查及运行均通过，未修改用户编辑器设置。

## 范围与过程资料

测试存档全部位于`/private/tmp/coastal-v5-*`，未使用真实玩家存档。过程媒体仅临时用于验收，不纳入Git；制作包继续本地忽略，新运行PNG及必要导入配置是主游戏实际依赖。Progress四步骤对应核对、接入、验证和交付。未提交、推送或导出；不宣称独立导出应用和其他平台已验证。
