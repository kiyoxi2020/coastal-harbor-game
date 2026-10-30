# 南underhat r004＋真实帽atlas持久组件候选

完成：只新增source、hair/hat适配r002及版本化设计、独立south-headwear-r001 annotation。未改旧r001、衣装annotation、canonical pose、共用engine、current manifests或baseline；未创建完整clip/全包配方，未提交。

持久入口（相对art/characters）：

- `sources/gpt-south-underhat-r004-v1/source.json`：完整r004 raw、prompt，r002/r003直接编辑链，raw ownership、人工语义正/负边界、293非hair排除见证、眼耳实测与残差。generator实际精确模型名未暴露；最初r002的确切调用输入路径没有独立恢复，已明确标注不确定性。
- `parts/hair-chestnut-short-v1/revisions/r002/design.json`与`parts/hat-straw-navy-band-v1/revisions/r002/design.json`：实际既有款式身份及此候选的真实表面/适配引用，非空接口占位，不宣称全动作能力。
- `parts/hair-chestnut-short-v1/adaptations/adult-standard-v1/review-motion-v1/r002/views.json`。
- `parts/hat-straw-navy-band-v1/adaptations/adult-standard-v1/review-motion-v1/r002/views.json`；同目录`metadata/atlas-registration.json`保留原raw/bundle/local owner/注册authority路径与SHA。
- `templates/adult-standard-v1/motions/review-motion-v1/annotations/south-headwear-r001/poses.json`，独立源/目标记录，真实canonical B/frame/SHA绑定。`head` surface绑定`base`层，便于统一registered-head接口；不与衣装共享annotation。
- `parts/hair-chestnut-short-v1/adaptations/adult-standard-v1/review-motion-v1/r002/compatibility/south-underhat-r004-real-south-hat.json`：独立typed claim分别绑定hair intrinsic身份及真实全帽身份，不写回raw bundle。
- 完整证据：`parts/hair-chestnut-short-v1/adaptations/adult-standard-v1/review-motion-v1/r002/evidence/reconstruction.json`与同目录canonical-body-hair-hat PNG、历史接口放大见证。

最终mapper真实复算：

- Hair raw1122×1402，全源ratio256/187，同轴逆仿射187/256、NEAREST、offset0，ceil1536×1920。raw frame root[561,1168.75]→[768,1600]只是冻结frame登记，非生成脚底。normalized实测耳中点[765,730]→canonical登记点[768,729]，一次整源整数[3,-1]；真实目标耳中点y728.5及眼耳残差保留。
- Hat原raw1774×887→统一1536/887到3072×1536 atlas，真实ownership位于原local768²在atlas[0,768]的嵌入。真实耳锚[142,1304]→[533,729]，整数[391,-575]；不伪造atlas的world root。最终mapper重建逐RGBA等于旧真实帽PNG。
- 两层均通过最终`RegisteredAdaptations.component`，来源、annotation、ownership、整数锚及纹理RGBA精确重建。再次完全从持久文件读入设计、views、annotation、bundle、claim及canonical父底图，无临时资源依赖；36项记录输入SHA一致，所有bundle assets校验通过。
- 同一`composition_contract.compose`以真实canonical`water_south_B_ready` B完整帧为父底图，顺序`base → under_hat_hair → near_hat`。没有从生成图导入脸耳手body，真实支撑外父RGBA不变。仅near真实全帽，无fake far、无volume或逐列擦hair、无coverage/occlusion erase。
- 冠ROI[350,200,1150,540]中alpha≥220发像素在真实帽支撑外0；43个alpha=1软发缘保留。眉/眼/耳/脸颊排除与实际发束见证已持久保全；耳下293raw轮廓不是hair。目视复查实际canonical父底图上的耳/刘海接口，无新生成脸耳导入。

验证：`python3 -m unittest discover -s tools/characters/tests`：195 tests OK（97.655s）；`python3 tools/characters/check.py`通过（5 strict recipes/4 builds/9 frozen legacy，生产关闭）。初次check发现临时登记脚本被误放source metadata，已移出库后通过；库内没有批次作者代码、第二构建器或播放器。

未验证：没有完整clip，因此未执行strict recipe construct/verify；未接新top03衣装父底图；未尝试推广其他pose。Godot物理屏幕、连续动作、时序/接触、用户认可和生产发布均未完成。1536×1920输出沿canonical display_scale0.11855670103092783只声明逻辑画布约182.103×227.629；不能冒充物理像素验收。
