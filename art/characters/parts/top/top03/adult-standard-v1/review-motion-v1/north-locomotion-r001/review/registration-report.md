# 东侧与北背：top03 walk4 + idle 的真实衣装登记

本内部子包完成两个方向、各完整4帧walk与唯一idle，共10pose、30个衣裤鞋组件。它不包含head、Godot、native/dynamic或用户认可，不宣称全动作完成；四向idle/walk以外的衣装仍由主任务继续。

| 方向 | 严格schema3配方 | 最终review build | artifact digest |
|---|---|---|---|
| East | recipes/top03-east-locomotion/r001.json | builds/top03-east-locomotion-r002 | 16cbe992920970d02c23ede8f9d192b15426f8cb32a5e1ad0db0d607eec66418 |
| North | recipes/top03-north-locomotion/r001.json | builds/top03-north-locomotion-r002 | 480d2c2e5ed3289e93420c4481310fbaf53263ce2570f751e82f0d7071344453 |

通过统一build.py build与verify，全部真实15+15组件先经公开RegisteredAdaptations.component准入。每个pose的pants/shoes均为非空真实有限材料identity；不是合成fixture、空层或截短clip。

## Canonical 与源

依据canonical poses核准：east idle=B_2，walk=B_12..15；north idle=B_3，walk=B_16..19。原r001 pose文档、B variant、完整frame文件/SHA、512×768/root[256,708]/display_scale0.23711340206185566均绑定新annotation。新revision分别`east-locomotion-r001`和`north-locomotion-r001`，没有修改south、共享r001、engine、消费者或现行发布清单。

同方向真实static top03 atlas=`sources/static-top03-v1/source.png`，2048×768，SHA 8d86bad3a308885ea42abe0b54ff4451bf4e44a8b8bf22b86f59b2f93c78e055。仅作为style参考：east cell[1024,0,1536,768]，north cell[1536,0,2048,768]，reference-only裁格后整格nearest2到1024×1536。不能把这些静态贴图当动作衣物源；没有使用正面图冒充背面。

每pose以实际完整canonical B frame的整帧nearest2为编辑目标，生成完整1024×1536 GPT源，保存原PNG、prompt、实际输入路径和内容SHA。10张首轮完整pose源，另定向生成4张完整shirt候选；最终eastwalk3整件使用完整shirt r002，其余9pose使用本pose r001完整pose材料源。eastwalk3的r001保留为r002真实style输入。其余3张shirt候选没有被强行接入，仅留临时测量目录。生成方式为内置GPT imagegen，精确模型标识不暴露。

所有被映射的新源均整源NEAREST1/2到512×768，注册差[0,0]；raw frame reference root[512,1416]→canonical[256,708]。这是绑定完整参考画布的注册坐标，不从人体总高估计或伪造孤立衣物的可见foot landmark。没有部件独立挪动、缩放、重着色或人工补画。

新GPT源包：`gpt-top03-east-locomotion-v1`、`gpt-top03-north-locomotion-v1`。新canonical-derived包：`canonical-b-east-locomotion-reference-v1`、`canonical-b-north-locomotion-reference-v1`。

## 真布料、原navy trim与有限覆盖

| pose | top材料点 | 真实原navy cuff点 | 原池剔除的非材料/轮廓点 |
|---|---:|---:|---:|
| walk_east_0 | 23025 | 1156 | 47 |
| walk_east_1 | 21585 | 1040 | 78 |
| walk_east_2 | 18862 | 1272 | 103 |
| walk_east_3 | 21609 | 1026 | 44 |
| idle_east_0 | 21671 | 925 | 185 |
| walk_north_0 | 31940 | 1536 | 115 |
| walk_north_1 | 31588 | 1705 | 54 |
| walk_north_2 | 32530 | 1591 | 1 |
| walk_north_3 | 32428 | 1647 | 184 |
| idle_north_0 | 36772 | 1631 | 246 |

原source garment分层只提出候选池，不能把其中皮肤、灰色/混色外轮廓、alpha fringe全部当cloth。Palette/alpha用于定位疑点；实际边界按原领口/肩袖/腕/腰与源图检查。每个被排除点均保存canonical RGBA和语义理由；只保留冻结原RGBA，没有用缩coverage遮盖eastwalk3的普通袖身缺材。该pose最初确有普通袖身缺材，r002完整shirt提供真实布料；整件用r002避免两套stripe phase逐点拼边出现碎白线。

Eastwalk2特别检查了(310,487)/(310,488)：虽有原blue garment泄出的蓝色RGB，它们几何上是手背孤立旧蓝点，而非袖子表面。放大证据`east2-actual-cuff-two-points.png`，这2点保留原手RGBA，不刷成新衣服。原语义池里也含暖米色cloth阴影，已目视区分，不用肤色阈值独自判归属。

每pose把原B真实navy cuff作为明确同姿态有限cloth材料输入：由真实手腕接触与cuff区提出候选，再检查其原布料/投影与新条纹衫深蓝trim相容。只选navy腕口，不用普通蓝袖身补源；不调色/挪缩。该选择仍计cloth，绝不重叫outline来隐瞒缺口。完整canonical参考保留，1/1整源注册，经独立source-selection二值选择；source ownership、coverage和selection各自有文件与角色，软alpha不重复相乘。

主代理已目视十姿态总览：侧/背投影正确，navy cuff与striped knit静态相容，领/腰/袖边无明显异色补丁。此为主代理静态source核查，不记录成用户/native/dynamic认可。跨帧连续stripe phase仍需原生循环观察。

## 原裤鞋与alpha

原裤鞋源是完整已注册canonical B帧的字节相同derived copy，明确不是GPT raw、新body或隐藏身体。metadata绑定每个真实canonical pose/frame/SHA和原parts/hide-mask/source-bundle，并追溯379a9bc原始idle、east/north GPT atlas、prompt与旧完整帧注册记录。body.texture为canonical完整帧的等RGBA别名，并经schema3 body强校验。

原裤source ownership取实际冻结lower层贡献的可见裤材料；原鞋为人工review靴区内有限深棕皮革材料，不覆盖中性/白色高光、裤管阴影或完整靴alpha。初次鞋候选ROI过宽，静态归属复核发现少量裤管阴影，因此在冻结前收紧真实深棕皮革界面。初稿两份r001 build完整保留在临时目录`pre-admission-east-r001-build`/`pre-admission-north-r001-build`；正式最终输出为新r002目录，没有删除旧交付或改baseline来过门禁。像素外观始终不受此identity层修正影响。

每pose原裤材料10271–17064点，原鞋皮革4865–6797点，均真实非空，经mapper从完整derived reference重算。它们是这10个canonical B姿态的有限identity接口，不能据此推断任意下身混搭、完整独立裤鞋层或隐藏腿脚能力。

Top显式使用已支持的canonical-surface-alpha-v1 wrapper，scope=finite-canonical-material：RGB来自本pose完整GPT材料源及真实原navy cuff；owner内alpha取source annotation绑定canonical frame。source/target同pose，实际10个统一构建输出证明：全画布alpha差0、top coverage外RGBA差0、原裤鞋材料内RGBA差0。原脸/后脑、颈肤、手、裤鞋与foot contacts原样保留。没有把生成的新face/hands/lower当body。

## 证据与未验

- `east/north-component-admission-receipt.json`：实际30组件准入、依赖SHA与非空计数。
- `actual-output-invariance.json`：最终统一build输出差异测量。
- `source-assets-verification.json`：4个新源包全部声明文件存在且SHA匹配。
- `ten-pose-final-previews.png`、`east/north-five-pose-original-and-build.png`、各pose final-boundary-review与lower-material-ownership-review、两组original-navy-cuff-comparison：静态显示与归属复核。

源1024×1536→构建512×768→逻辑约121×182；源、接缝放大与实际逻辑尺寸已目视。原pose4帧80ms与idle200ms保留，runtime播放率0.75是独立消费者设置。本任务不新增播放器/批次合成器，最终仅调用统一build.py。

未执行Godot/native/world/连续进入退出/混搭动态验收，不包含head、run或农事。发布仍关闭，status=review-only；南冻结字节、共用engine、current manifest/catalog/baseline均不改，没有提交或推送。


最终工具门禁：`python3 -m unittest discover -s tools/characters/tests`：208 tests，161.054s，OK；`python3 tools/characters/check.py`：passed=true，strict_recipes=10，strict_builds=9，frozen_legacy_recipes=9，production_release仍closed。最终east/north r002 build逐一verify通过；`git diff --check`通过。日志`character-tests.log`、`character-check.log`。源包声明assets逐文件/SHA核验全部通过；完整GPT缓存输出位置/SHA另保存在`generation-cache-locations.json`，正式review证据有副本，不把它当新runtime源准入格式。没有提交或推送。
