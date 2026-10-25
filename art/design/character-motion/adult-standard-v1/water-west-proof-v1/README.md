当前修订见 [浇水 v2：比例修订及原生十循环，接触/握持与视觉待审](revisions/v2/README.md)。以下为此前 v1 记录。

# 西向浇水完整帧候选

目标是为同一 `adult-standard-v1` 母版制作可观察的提壶→倾倒出水→回收动作。本目录仅包含奶油短袖、橄榄裤、棕鞋的 GPT 完整帧候选，**未获用户批准，体高比例需返工**；不表示分层换装、四向完整动作、业务接入或生产发布通过。

入口：[自包含可播放评审](review.html)，支持暂停、逐帧、速度和重复开关；[原生十循环录像](evidence/native-ten-cycles.mp4)，左右分别为明暗背景，包含原生目标缩放与放大诊断。

## 来源与登记

使用 built-in GPT `image_gen`，提示词在 [prompts](prompts)，完整原图在 [sources](sources)，源图和参考文件哈希在 [来源清单](sources/source-manifest.json)。外观依据当前选中母版 `selection.json` 的眉毛 v3 和已认可的西向 walk A；没有拼贴旧脸或手。

两版六格源稿要求1536×1536，工具实际均返回1254×1254，无法满足每格512×768；保留为失败尺寸记录。随后采用已有成功证据的2048×768四格布局，得到当前 v3。四个完整姿态按180/160/260/200ms播放，单次合计800ms；重复仅供评审，不触发农事事务。

当前源图2048×768，每格512×768，头部约240源像素，未重采样。为将右移的倾倒姿态按脚部占地参考点对齐，同时保留完整水流，统一扩大到 **768×768、根点[384,708]**（相当于原512画布根点[256,708]增加128px左侧余量）。登记仅执行整帧整数平移，见 [registration-config.json](registration-config.json) 和 [register_candidate.py](register_candidate.py)；没有局部移手、移鞋、缩放衣物或程序绘制正式美术。

统一显示缩放仍为138/582、nearest；768源像素画布约显示182×182渲染像素。**候选人物实际高度约644源像素，显示约153像素，比已认可walk约138像素偏大；头密度接近但躯干/腿比例尚不合格。** 此问题不能用全帧缩小来假装同一源密度，需后续GPT重绘比例。原生明暗停帧已目视检查，工具、握持手、水流和落点可见。

## 验证与边界

四帧均通过精确源裁切、整帧整数平移、画布边界、正时长、文件哈希与四帧不同检查。Godot 4.7.1 原生诊断窗口完成10次连续播放，原生记录及截图见 [验证记录](evidence/validation.json)、[原始连续帧](evidence/native-originals.zip) 与 [采样记录](evidence/native-samples.json)。录像是实际 Godot 诊断渲染帧编码，非用静态源图合成的伪原生证据。

提壶和倾倒时肩、肘、腕与壶均变化；握点与玫瑰喷头可观察。回收帧接近准备帧，残余滴水结束后重复。手工观察坐标在 [poses.json](poses.json)，隐藏关节和解剖左右映射未冻结；约±4源像素观察不能冒充≤1屏幕像素的批准目标轨迹验收。

尚未通过：母版体高比例、用户动作认可、严格脚接触/刚性握持轨迹、真实港口遮挡和交互、工具事件时序合同、分层身体/衣物与动态混搭。没有读取或写入玩家存档，没有修改玩法事务、共享脚本、正式人物资源或发布清单。

复现登记与HTML：

```sh
python3 art/design/character-motion/adult-standard-v1/water-west-proof-v1/register_candidate.py
python3 art/design/character-motion/adult-standard-v1/water-west-proof-v1/build_review.py
godot --path godot2d --log-file /private/tmp/coastal-water-west-proof-native.log --script /Users/wyq/Documents/code/coastal-harbor-game/art/design/character-motion/adult-standard-v1/water-west-proof-v1/native_review.gd
```

本子任务负责独立西向浇水美术、登记与原生证据交付；实际模型由主代理派发记录注明。未创建下级代理，未提交或推送。
