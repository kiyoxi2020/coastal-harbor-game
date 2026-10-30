# 成年固定配方全动作：衣裤鞋来源准备度

日期：2026-10-29。只读核查，目标为 top03 / original-pants / original-shoes，24格、84个实际pose；不包含发帽审计，不是新适配、构建、原生或用户认可。详细逐pose路径、坐标、层序、mask与SHA见同名JSON。

## 可执行结论

现有资源足够直接保留西锄4pose及其exact西idle；西walk4pose的条纹上衣像素也足够，但原裤原鞋的新动作身份、源提取和真实覆盖/层序尚待登记。其余72个运动pose没有找到同投影top03条纹源；另3个idle只有四向静态top03候选，尚不能证明与冻结idle母版可作整帧注册。**不能仅靠注册现有文件就声称全84pose资源齐备，也没有依据要求全身、裤鞋或84pose全部重新生图。**

固定原下身的实际像素可从每pose完整参考及locomotion真实共享body层取得。prompt链明确原橄榄裤、棕鞋及其位置保留，因此不是按颜色认同款。但original-*旧ID仍是有限配方标签，除西锄/西idle外79pose未登记目标裤鞋适配；当前结论是可推进有限身份准入及逐pose提取，**不是独立裤鞋通配/隐藏身体已完成**。未发现必须补画的具体可见下身表面；若新遮挡/覆盖露出不存在的表面，再报告该pose和表面。

## 24格矩阵

| 动作 | south | west | east | north |
|---|---|---|---|---|
| idle | 静态top候选待投影核；下身待登记 | 三件exact源、mask、层序齐全 | 静态top候选待投影核；下身待登记 | 静态top候选待投影核；下身待登记 |
| walk | 缺已证同pose条纹源×4；下身待登记 | top03可复用×4；下身桥接后待登记 | 缺已证同pose条纹源×4；下身待登记 | 缺已证同pose条纹源×4；下身待登记 |
| run | 缺已证同pose条纹源×4；A下身待登记 | 缺已证同pose条纹源×4；A下身待登记 | 缺已证同pose条纹源×4；A下身待登记 | 缺已证同pose条纹源×4；A下身待登记 |
| hoe | 缺已证同pose条纹源×4；下身待登记 | 三件exact源、mask、层序齐全×4 | 缺已证同pose条纹源×4；下身待登记 | 缺已证同pose条纹源×4；下身待登记 |
| water | 缺已证同pose条纹源×4；下身待登记 | 缺已证同pose条纹源×4；下身待登记 | 缺已证同pose条纹源×4；下身待登记 | 缺已证同pose条纹源×4；下身待登记 |
| harvest | 缺已证同pose条纹源×4；下身待登记 | 缺已证同pose条纹源×4；下身待登记 | 缺已证同pose条纹源×4；下身待登记 | 缺已证同pose条纹源×4；下身待登记（同名旧鞋属于另一父配方） |

5个exact pose＋4个西walk复用pose＋72个运动top投影缺口＋3个idle候选＝84。72个target pose不等于72次生图：西walk已有一个完整torso view被4pose复用，独立袖形及真正露出的隐藏布料才决定绘制视图数。

## 最小新增源包：先south walk

用 `art/characters/builds/locomotion-r001/frames/B_4.png`、`B_5.png`、`B_6.png`、`B_7.png` 对应 `walk_south_0..3` 作为完整真实pose参考。每帧512×768，root=[256,708]，scale=138/582，80ms；playback_rate=0.75另记。四个完整cell可合为2048×768条带请求一次生成，结果仍逐pose审核与注册，不能把一次调用等同于通过。

款式参考：`sources/static-top03-v1/source.png` 的south格；实际已采用的运动布料参考为 `sources/motion-wardrobe-sampling-v1-2381424d/originals/walk_west_0-outfit-v1-2d469955.png` 和 `sources/motion-wardrobe-sampling-v1-990cd16b/originals/ready-full-attempt1-30edae01.png`（均相对 `art/characters/`）。

现有西锄prompt明确只换蓝衫布料为宽海军蓝/暖奶油横条，**保留原衣身轮廓、袖长、袖口和姿态褶皱**。这叫same-cut-surface-adaptation，静态top03原有短袖轮廓不能自动变成当前长袖接口。首包应沿同一规则编辑B已存在完整布料：画完整torso及各真实手臂状态袖片；手掌遮住的torso区域按固定组合真正需要补齐。不重画固定脸手、裤鞋或工具，不接纳GPT改变的非top像素。

交付原始完整GPT源、prompt、注册、source ownership、作用于实际身体/袖表面的coverage及每pose真实层序。若完整torso投影可复用，仅新增必要袖视图；不能把现有visible mask当完整源，也不把ownership直接当coverage。首包通过后按JSON的18个动作方向源包继续，每包给出4个真实frame路径；农事原画布更大，逐完整pose生成通常比超大四格条带稳妥。三向idle先量同投影；不能证明时仅补相应完整条纹衣装源。

## 固定B下身怎样推广

1. exact西idle的裤/鞋coverage内与locomotion B_1逐RGBA差异均为0；原source_references含B_1。该已复核桥接保留在JSON。西walk旧父配方是pants02＋original-brown-shoes-v1，只取它的top源；不能取整套样例冒充目标下身。
2. idle/walk均已有真实注册祖先和逐pose共享body/手臂/torso/袖层。原完整A源的下身保留在B组装结果，A→B prompt要求裤鞋位置及像素不变。最小操作是在同pose源中提取有限裤鞋ownership，保留源RGBA软边；给目标裤/鞋表面独立coverage含义，并按原腿/衣摆/手臂前后关系登记。西walk现有裤鞋诊断mask只是目标区域线索，不能直接换名成正式original-* mask。
3. run用四向真实A完整参考为下身/脸手来源。south B第三帧摆臂改变、north B领口/腰/腋下有孔且是diagnostic，不必为保留下身而依赖这些B稿。west A原atlas及其[0,11]整帧登记已定位；east A来源是历史已登记全帧反射+1x，报告记录该来源，不授予新动作任意镜像权限。四向新top应围绕已冻结A pose画，不把A衫当top03。
4. 三农事的完整B源及整帧source_box/translation均存在，prompt显式保持原橄榄长裤/棕鞋和动作。它们是穿衣参考，裤鞋、衣身、手、工具需按实际pose拆归属与前后关系；当前多数没有独立裤鞋ownership/coverage/真实有序子层。只登记有限目标配方，不由完整穿衣源推断裸身体齐全。
5. 腰、踝、鞋口和手掌前后关系必须实际查看；正常腿脚姿态沿母版，不能单独挪缩裤鞋修接口。原north harvest的original-shoes属于蓝长袖＋pants02，不能扩大到目标原裤。

## 统一构建字段与边界

推荐新design revision显式file/SHA选择和有限适配；旧design/r001不改。每view绑定 design_id、view_id、真实source_view_pose、完整source及bundle SHA、源canvas/root；每target pose独立绑定目标canvas/root、整帧registration记录、ownership、coverage的target_surface_id、实际层序/occlusion和composition_mode。无必要mask显式声明，不能为填字段造mask。source/target pose不混写；无部件局部缩放，不能把一张其他整衣装当body层。

西锄/西idle直接复用r002层与原RGBA规则；西walk正式准入已有完整torso源和各袖源，再为保留的B原下身登记新pose适配。其余top缺图不得用站姿硬贴、程序画横条或把其他上衣重命名解决。新来源必须仍走同一build.py合同。

## 核查证据与限制

已读AGENTS、人物README、唯一制作规范相关段落、24格审计JSON/MD、walk-west准备及其evidence、各pose文档、三款design/view、来源迁移记录、实际prompt，并定向查Git379a9bc。当前prompt及历史prompt检索中的条纹来源只落在静态四向、西walk、西hoe；这是仓库/Git范围检索，不宣称外部目录绝无源。

JSON枚举24格84pose，590条实际文件引用均现场读字节计算SHA，另5个Git源对象读字节计算SHA（并记录blob）；west-walk历史原atlas/prompt/registration可精确恢复。图像目视核静态top03与idle B、run A、water B：确认静态体型/裤鞋及衣装不同，不据此推定同投影。没有改正式资源/代码，没有生成新图，没有执行原生或测试；资料审计不能替代动态兼容与用户视觉认可。
