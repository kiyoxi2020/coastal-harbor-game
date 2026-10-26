# 浇水西向v3：两关键姿态候选，未通过动作验收

2026-10-25，农事子任务，gpt-6.1-sol/high负责复杂工具/姿态与来源检查，未嵌套代理。使用 imagegen 技能的 built-in image_gen，精确模型ID工具未返回。原图和完整prompt已保留，没有CLI回退、局部缩放、移手鞋、贴旧脸或像素修补。只写本v3新目录，未改旧稿、共享工具、玩法或玩家存档。

## 制作方法与实际量测

旧v2四格idle编辑两次分别留下脚位滑移、站高漂移。本次先做两个宽间距关键姿态。实际输出1774×887而请求1536×768：画布倍率1.155，头宽/高倍率1.251/1.227，人物总高约1.261，躯干/腿段也不符画布倍率，拒绝该探针，未用整体缩放掩盖比例。见 measurements.json 的 rejected_two_panel_probe。

新证据表明多格布局密度不可靠，转为单张2:3完整姿态校准：先ready，再从其完整源产生pour，均1024×1536。该画布是批准idle 512×768的整画布2×，统一显示scale为138/1164（约0.118557），从画布合同确定，不按当前人物总高拟合。原图保留，整数整帧登记到1536×1664，未重采样。脚根从可见近鞋后缘和母版固定偏移[144,4]推定，属诊断登记，未冻结为运动接触轨迹。

| 同口径观察（源px，点位约±8px） | 2×idle基线 | ready | pour |
|---|---:|---:|---:|
| 头框宽×高（含描边，不含颈） | 478×484 | 473×488 | 472×481 |
| 下巴→衣摆投影y | 338 | 353 | 340 |
| 衣摆→观察根点投影y | 346 | 328 | 338 |
| 头冠→观察根点投影y | 1168 | 1169 | 1159 |
| 壶体宽边平均 | — | 187.50 | 178.12 |
| 壶体高边平均 | — | 169.08 | 166.60 |
| 喷头→壶心 | — | 224.99 | 219.36 |

头身接近2×基线，但不据此称比例或动作通过。近鞋后缘对齐是登记定义，不是接触证据；另一鞋的真实点保留：近脚趾差10px≈1.19屏幕px、远脚趾差11.70px≈1.39屏幕px，人工不确定度亦未达到≤1屏幕px证明精度。壶宽边最大/最小约5.27%，喷头距约2.57%；握把与手指局部遮挡，精确附着及刚性未验证。工具角点、手/握点、腕/肘可见表面和脚点逐图登记；髋/膝/踝等衣物隐藏关节为null，未按总高推算。

因此不补中间提起/回收、不扩四帧、不分层、不接入加载器。只交ready/pour两关键姿态待审。循环只是诊断交替显示，不等同完整浇水或自然衔接。

## 交付与验证

sources保存三张完整原图（含拒绝探针）；prompts保存完整提示词；provenance.json记录输入角色、生成原文件及关联。references是实际看过的idle、active母版、壶设计。source-manifest.json和candidate.json记录实际来源、配置、姿态、纹理、规则哈希。registration-config.json、poses.json、measurements.json保留实际点位及隐藏未知。review.html提供真实登记纹理明暗1×/2×、停帧和诊断交替。evidence/static-review.png仅派生排版。

四项结构测试通过：完整RGBA含全部低alpha像素保留、实际输入/digest、姿态坐标转换与隐藏unknown、不完整动作不声明可用。见 evidence/validation.json。复现：

    python3 art/design/character-motion/adult-standard-v1/water-west-proof-v1/revisions/v3/build_candidate.py
    python3 -m unittest discover -s art/design/character-motion/adult-standard-v1/water-west-proof-v1/revisions/v3 -p test_candidate.py

主代理已串行完成原生诊断：585采样、249捕获、10次两姿态重复，目视明暗1×/2×。独立证据为 evidence/native-validation.json、keyposes-native.mp4、native-originals.zip。这是诊断显示通过，不是完整动作、接触/刚性或用户认可；candidate的native_checked仍为false，保留原artifact hash，原生证据独立绑定。调用：

    godot --path godot2d --log-file /private/tmp/coastal-water-v3-native.log --script /Users/wyq/Documents/code/coastal-harbor-game/art/design/character-motion/adult-standard-v1/water-west-proof-v1/revisions/v3/native_review.gd

脚本只读本目录candidate，nearest显示，不加载存档服务、不发玩法事件。精确接触/刚性/握点、隐藏身体、A/B衣物、四向、完整动作及用户认可均未通过。artifact_digest：fb55127f93a0ad29018320e0caa1c50a42f68296dd56038557d7d682eccfe465。
