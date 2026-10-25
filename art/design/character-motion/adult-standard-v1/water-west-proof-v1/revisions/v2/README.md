# 西向浇水 v2 比例返工候选

本修订保留旧稿，改以当前已批准的 `idle_west_0` 四格同画布图作为几何输入，旧水壶稿只提供局部壶设计参考。目标是纠正旧稿腿长、保留头部密度，再评审提壶→倾倒→出水→回收。当前仍是**未获用户批准的完整帧候选**，没有分层换装或玩法接入。

入口：[自包含播放页](review.html)。明暗背景、逐帧、变速及重复开关均使用真实登记纹理。主代理已完成原生明暗十循环，见[原生记录](evidence/native-validation.json)与[连续视频](evidence/ten-cycles.mp4)。

## 比例原因与两次方案

[旧稿分段量测](measurement-baseline.json)：头约239px、下巴至衣摆约171px，与批准idle约239/170接近；旧稿衣摆至根点约234px，批准约173px。旧稿多出的62px中约61px来自腿段，并非全身同比例变大。量测为可见界面观察，约±4px，隐藏关节没有被伪造为已知值。

第1次方案直接编辑批准idle四格，不向GPT输入旧water全身。腿长和站高恢复，但提壶/倾倒格的脚位整体右移约28–31px，峰值水流还越过原512格边界。第2次明确约束相同脚位后，脚位漂移下降，但站高又增至约601px，退为返工记录。**已达两次生成上限，没有继续生图或反复调mask。**

最终选择第1稿登记。按相同alpha头顶ROI测法，当前批准idle从根到头顶约584px，第1稿四帧约585px；工程名义显示尺度仍为138/582，保留这一差别而不改写基准。报告见 [proportions-report.json](proportions-report.json)。没有后期缩短腿、缩放衣鞋、拼接旧脸手或局部挪动身体。

## 源图、裁区与脚点

完整源图为2048×768。峰值水花跨入上一名义格右下；其前一人物与水流之间有真实空隙，因此将整个源图按x **0/512/950/1536/2048** 分成四个互不重叠、无缺口的完整矩形，保留全部源像素。随后只作整数整帧平移，统一登记到 **768×768、根点[384,708]**，详见 [registration-config.json](registration-config.json)。不存在擦除水花、移动局部物体或重采样。

脚部占地参考通过近侧鞋后缘与批准站姿的关系作**整帧平移登记**；这不是动态支撑脚锁定。另一鞋轮廓仍有数个源像素差别，完整接触轨迹和≤1屏幕像素目标尚未通过。上身相对脚位的自然前倾被保留，不能把登记当作四格身体完全相同。

## 水壶与握点

[壶与握点报告](tool-grip-report.json)记录手工可见壶角、玫瑰喷头与双手位置。四帧壶体宽、高、喷头到壶心距离的最大/最小观测变化约5.1%、3.7%、3.8%；约±4源像素的人工定位误差包含在内，**不能称为刚性工具验收通过**。双手可见接触，部分手指/把手几何被遮住，精确握持轨迹尚未冻结。

提壶、倾倒与回收的肩、肘、腕、壶姿均变化，峰值连续水流连接喷头与落点。四帧共800ms；默认重复只供首尾评审，没有提交农事事件或事务。姿态与源坐标见 [poses.json](poses.json)。

## 验证与复现

四项结构测试通过：全源无缺口/无重叠分区、精确裁切加整帧平移、实际依赖哈希、越格裁区下的握点坐标转换。静态比例/明暗诊断板为派生排版图，不冒充原生游戏证据。

```sh
python3 art/design/character-motion/adult-standard-v1/water-west-proof-v1/revisions/v2/register_candidate.py
python3 art/design/character-motion/adult-standard-v1/water-west-proof-v1/revisions/v2/build_review.py
python3 -m unittest discover -s art/design/character-motion/adult-standard-v1/water-west-proof-v1/revisions/v2 -p test_revision.py
```

主代理已执行的原生调用命令：

```sh
godot --path godot2d --log-file /private/tmp/coastal-water-v2-native.log --script /Users/wyq/Documents/code/coastal-harbor-game/art/design/character-motion/adult-standard-v1/water-west-proof-v1/revisions/v2/native_review.gd
```

该脚本读取同目录candidate，完成10次诊断循环，在同目录evidence写原生停帧、25fps连续帧与native-samples.json，然后退出；不启动存档服务。它是本目录旧诊断脚本的原样复用，不修改共享Godot文件。

未通过项：用户认可、精确脚接触、壶刚性与握持轨迹、世界交互、分层身体/衣物/动态混搭、四向与正式发布。gpt-6.1-sol high子代理负责本次独立美术返工与登记，未创建下级代理，未提交。

主代理补验：原生 1280×720 明暗板显示 1×/2× 的真实登记纹理，十循环共337采样、199捕获，连续图和四停帧已归档。静态拼版缩略图另为0.72×，不作为原生尺寸标准。已目视检查水流边界和足部；仅诊断播放通过，未证明接触或工具刚性。
