# 西向采收试稿：已拒绝

本目录保留 `adult-standard-v1` 西向 `harvest` 的两次GPT完整帧尝试与失败证据。4帧2048×768，奶油短袖、橄榄长裤、棕鞋，同一选定眉毛v3身份。蹲身伸手→握叶拔起→双手收回→起身的语义可见；**两稿均因密度和脚部支撑失败而拒绝，未获用户批准，不是可用harvest动作，不接入生产。** 已达到本任务最多2次针对性生成的上限。

入口：[播放与逐帧评审](review.html)、[原生启动器](launch-native-review.command)、[原生明暗截图](evidence/native-scale-review.png)、[十次原生重播录像](evidence/native-ten-replays.mp4)。这些入口查看v2失败稿；不是通过验收的展示。

## 来源与实际尺寸

GPT built-in `image_gen`生成/定点编辑，没有CLI回退。精确生图模型标识未由工具返回；不从工具名称臆测具体模型。原图、哈希与参考见[source-manifest.json](sources/source-manifest.json)，提示词在[prompts](prompts)。参考为 `selection.json` 的 `directional-brows-v3`、当前西向walk单帧及四帧sheet。人物与萝卜全部由GPT绘制，没有程序画正式美术。

| 来源 | 整张源尺寸 | 每帧源尺寸 | 末帧人物不透明包围 | 结论 |
|---|---|---|---|---|
| v1 | 2048×768 | 512×768 | y74..718，高644px | 对照582px偏大10.7%，拒绝 |
| v2定点编辑 | 2048×768 | 512×768 | y77..721，高644px | 密度未修正；鞋位仍滑移，拒绝 |

v2完整源原样保留；登记仅逐格裁切并整帧向上13px，统一512×768、名义根点[256,708]、nearest和138/582显示比例。没有缩放人物或分件挪动衣鞋来掩盖错误。画布原生显示121.40×182.10px；当前末帧人物实际约152.70px高，对照目标138px。名义根点只是独立评审坐标原点，未建立可靠的实际世界支撑。

## 可观察语义与明确失败

首帧张开的手触向叶冠，次帧手握叶冠且萝卜离地，第三帧双手将其收至腹部，第四帧站起持物。没有锄头/浇水壶替代采收，也没有增加另一个人物。握取相位从180ms开始，只作视觉标记，不执行扣除、采收或存档事务。

失败项：

1. 末帧身体644px，对照582px偏大10.7%；头部约260px，对照236px亦偏大，不能把蹲姿缩短当作源像素密度正确。
2. 起身期间近鞋中心约从x300移到x205、远鞋约从x430移到x295，屏幕约23px/32px位移。两鞋支撑漂移，不能称为稳定根点动作；未用分件移动或逐帧锁鞋修补。
3. 缺少批准姿态/握点/脚点轨迹，不能声明≤1屏幕像素准确。萝卜物理尺寸一致性、隐藏关节及分层衣体接口尚未验收。

`poses.json`记录人工近似可见坐标和未知项；它不是批准的精确关节合同。完整部件源、覆盖mask、衣裤鞋替换、四向、发帽、动态混搭及正式动作衔接均未交付。

## 已执行验证

`validate_artifacts.py`检查四帧512×768、源RGBA逐字节一致、主体不透明像素未碰画布边、4个不同帧哈希与1000ms时间轴，均通过。这些结构检查不覆盖密度和支撑失败。

Godot 4.7.1 Compatibility独立1100×650项目、nearest、固定30fps，录得301帧/10.03秒、十次动作重播；原生明暗画面已目视检查。采收是一次性动作，录像从结束持物姿态直接回首帧，只供重复查看，不声称循环衔接成立。Movie Maker采用固定时间步，不能代替真实时间交互、世界移动、遮挡或碰撞验证。

下一步需要重新确定与母版同密度的蹲身/站起两姿态并锁定真实支撑轨迹，再扩完整动作。当前两次尝试已结束；没有继续生图，没有对外观配方或生产发布作扩大声明。

## 复现与分工

```sh
python3 art/design/character-motion/adult-standard-v1/harvest-west-proof-v1/register_sources.py
python3 art/design/character-motion/adult-standard-v1/harvest-west-proof-v1/build_review.py
python3 art/design/character-motion/adult-standard-v1/harvest-west-proof-v1/validate_artifacts.py
art/design/character-motion/adult-standard-v1/harvest-west-proof-v1/launch-native-review.command
```

结果见[validation.json](evidence/validation.json)，实际文件哈希见[artifact-manifest.json](evidence/artifact-manifest.json)。`native_checked`仅为被拒绝完整帧稿的显示/连续渲染证据；`motion_checked`、`user_accepted`均为false。

模型分工：实际 `gpt-6.1-sol high` 独立负责本目录美术生成、登记、姿态与原生证据，理由是中复杂动作源和验证可以独立交付；没有嵌套代理。仅写本目录和`/private/tmp`，未改共享规范/状态、玩法事务或玩家存档；未导出、提交或推送。
