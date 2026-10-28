# run_east_2 / run_east_3 新真帽提取审计

入口为 `manifest.json`，两帧的可消费文件、SHA、检查与登记残差分别见子目录 `manifest.json` / `audit.json`。本目录只替换 `run_east_2`、`run_east_3` 的帽层；没有生图，没有修改原身体、短发、catalog、Godot、idle 或旧 `motion-extraction` 反例。

## 来源与登记

输入分别为 `motion-sources/pose-2-wearing-v2.png`、`pose-3-wearing-v2.png` 的完整 1254×1254 RGB 原图，以及它们的 512×512 whole-image nearest 归一图。每帧目录同时保留 `source-original.png`、`source-window.png` 和 512×768 `source-full-frame.png`；重新执行 whole-image nearest 后与归一图逐 RGBA 相同。

耳弓、眼顶、眉三个独立特征的源→原身体偏移为：

| 姿态 | 耳 | 眼 | 眉 | 采用登记 |
|---|---:|---:|---:|---:|
| run_east_2 | `(0,0)` | `(0.5,0)` | `(0,1.5)` | `(0,0)` |
| run_east_3 | `(0,0)` | `(0,0)` | `(-0.5,1)` | `(0,0)` |

因此整幅源保持零登记；帽像素没有单独平移或缩放，运行时 `full_frame` placement 也是 `(0,0)`，不会二次加偏移。生成图中的人物只用于登记测量，不进入正式合成。

## 真帽归属与空间层序

正式 ownership 读取 `contours.json` 的冻结坐标，不在重建时运行颜色分类。帽冠、帽带、近侧帽檐和真实黑色下沿归 near；左右实际可见的帽底归 far，合成顺序为 `hat-far → original-body → hat-near`。far 多边形和近沿相遇时，共享的真实黑边强制保留在 near；run3 初稿中曾有 2 个近沿点落入 far，现已按完整近沿线修正，不以“远面”名义吞掉侵入头前的黑边。

源图是不透明画面，不能把 alpha255 当物体归属。逐帧显式排除了生成皮肤、源脸竖轮廓、肩部与灰背景；run2 帽冠/前檐凹角的一行灰底过渡和 run3 帽冠顶部灰底过渡也已从冻结坐标中排除。正式帽像素保持源 RGBA，未补色、重染或提高 alpha。真帽 ownership 不触碰 512 源窗四边，说明帽外缘没有被源图边界裁断。

近远层互斥，二者并集逐像素重建完整 `hat-complete-plate.png`。run2 为 37455 个帽像素（near 34074 / far 3381），run3 为 39032（near 35951 / far 3081）。帽支持区外的合成图与原身体每个 RGBA 字节一致，原身体文件 SHA 与对应 bare 参考一致。

## 原头覆盖、接触与反例边界

`target-coverage.png` 不是旧 v4 的 232 列接触线，也不是少量缺口探针。它取实际 near 帽面下边界以上、原身体 alpha≥32 的全部可见支持像素：run2 检查 25404 点，run3 检查 26573 点；两帧 `coverage-missing` 都为 0。`authored-contact.png` 只记录真实帽面与原身体的相邻接触，分别 236 / 238 点，不用于造帽、擦身体或裁头发。

旧 `motion-extraction` 的 run2/run3 拒绝仍保留且未放宽：它们的旧源在多点登记后确实缺少覆盖原头上右弧的帽面。新 v2 之所以允许进入 runtime 候选，是因为新的逐姿态真帽源分别通过同一套完整上头支持检查，并非修改旧缺口阈值、扩大 ownership 或挪动原头。

## 结果与验证边界

每帧 12 项离线检查均通过：1254→512 nearest 精确、源帽 RGBA 精确、零登记不裁边、源边界不裁帽、近远并集完整且互斥、真实近沿保持前景、帽支持外原 RGBA 精确、生成解剖与灰底排除、完整可见原头覆盖、真实 contact 属于 near。

已目视 `hat-head-2x.png`、`hat-light-dark.png`、`composite-head-2x.png` 和 `composite-light-dark.png`：两帧未见源肤色条、竖脸线、灰底条、近沿断裂、露原头上弧或帽缘裁断。当前状态只表示可交主代理接入并做真实 Godot 连续播放/明暗原生检查；本目录没有执行 native 验证，也不声明新的用户动态视觉认可、短发草帽兼容或完整四帧 run 已通过。
