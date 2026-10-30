# 原裤鞋：足点、支撑/腾空与滑步独立只读复核

结论：**当前不能通过设计77/88的严格脚接触/滑步门槛**。32个走跑姿态没有把实际足点、同一解剖脚身份、支撑期/腾空期及批准接触轨迹登记为可执行验收合同。原裤鞋像素保持与整帧注册成立，但这不足以证明支撑正确。此报告没有修改源、配置、速度、渲染、正式合同或现有验收工具。

当前可见的有条件反证也必须保留：同一姿态纹理停留期间，两个真实鞋底材料候选均随角色平移。若其中某个材料点被指定为固定支撑接触，它相对首样本世界点的偏离，走路为 **8.00–24.00 viewport像素**，跑步为 **16.00–36.00049像素**，远超1像素。接触期尚未定义，因此这些数值不是未经条件的真实物理接触误差；也不能用“接触未知”将严格门槛记为通过。

## 冻结输入与范围

- 最终84帧manifest：`art/characters/builds/adult-top03-full-hair-hat-r001/manifest.json`，SHA256 `9b209b9d4000a5e2c366705ff7e752efa875fd68100dacf3b1636826f53d6533`。artifact `61d071a98a25ee765be62fa4d4623cae074d4097327c8e781ca3a207b6af421a`。
- 实际base配方：`art/characters/recipes/adult-top03-full-hair-hat-body/r001.json`，SHA256 `c8ed7101e61fd21342b76e764533bba567cbdb708391b4a1d7b314a1b8427ef5`。只沿其8走跑clip的裤/鞋、source/target annotation、canonical pose/action与声明source JSON链读取：43个完整JSON加3个容器中的所选记录；不扫描无关资源。
- poses06原始报告：`/private/tmp/coastal-actual-all-actions-poses-06/report.json`，SHA256 `353a44de20080ddad921f4d06385297f53b39b98890ad89931db0c94e912905b`。world05原始报告：`/private/tmp/coastal-actual-all-actions-world-05/report.json`，SHA256 `bac3ef89d472ac1dbaee4fe9c5d8b729dd51eba7459a211de09ad9f332f50c7c`。
- 逐图查看实际walk/run原生1×总览，以及32个实际canonical/final裤鞋源下半身。world05测量覆盖全部1373个走跑draw PNG、2056个运动physics样本；41个held片段/clip（含首尾部分片段），其中39个完整片段/clip用于分布。全部328段保留在JSON，不删除异常或只选最小值。
- 1373个实际GPU纹理clip/pose/RGBA与最终manifest匹配；1373个原生PNG SHA和32个最终帧PNG SHA复核无差异。该检查仅证明身份/文件完整性，绝不证明接触。见 `actual-input-identity-crosscheck.json`。

## 已有元数据能证明什么

配方所选32个shoes mapping的注册锚是`frame_root`（canonical `[256,708]`），不是脚底点。裤鞋ownership/coverage描述有限可见材料支持；它们既不描述哪只脚支撑，也没有腾空时间窗、足底投影、批准接触轨迹或物理地面真值。所选链的key和非opaque字符串检索foot/feet/sole/stance/flight/support/contact/gait/ground/plantar/swing/airborne均无结果。完整文件与所选记录SHA见 `selected-metadata-audit.json`。不把作者代码快照中的制作操作当合同。

继续只沿上述引用链读取18个历史source JSON及26份prompt后，发现真实制作意图，不能声称所有来源都没有support/flight含义：South walk原prompt明确contact/passing/opposite contact/opposite passing；West walk原prompt指定near/far解剖腿在cell1/3的支撑、cell2的forward heel contact；North walk修改prompt明确第4格右腿支持、左腿抬起。South/North run原prompt明确0/2两侧交替接触、1/3腾空，后续修订要求保留腿鞋。这些文本还给出planted near y708或flight鞋高等一般目标，但没有被当前合同采纳的真实逐足点、批准轨迹/接触时窗与屏幕残差。runWest历史candidate只存`phase_map:[0,1,2,3]`，且`phase_map_status`明确`candidate observations, not frozen contact events`，不得当成已批准接触相位。具体26个prompt路径/SHA/命中行和18个JSON路径/SHA见`historical-source-intent-audit.json`。

既有shoe owner有局部覆盖限制：run West2/East2抬起的远鞋没有完整owner分量，仍由完整base母版实际显示；run South1/3若仅取owner最底行，还会漏掉真实黑色外底。故不能把owner底边、32鞋面栅格0差或frame_root直接命名为实际足点。这是测量语义边界，不是本次擅改owner的理由。

本次64个候选是**可见真实鞋底外轮廓材料点**：从已有鞋材料定位局部窗口，人工对照完整真实源确认鞋轮廓，保留最低可见行的整个x区间，再以其中一个实际像素中心作标记。门槛alpha≥220只用于选可见见证像素，不生成/修改mask，不靠颜色阈值判断鞋的空间语义。所有64点的原母版与最终帧RGBA相同。每点的源图、鞋纹理/coverage路径SHA、窗口、坐标、RGBA、是否在旧owner内都在 `source-sole-candidates.json`。

最初run South1左候选窗口在边界仍有黑色外底，已将该候选判为未完整包住外底并按实际源扩大语义窗口，得到`[212,651]`、RGBA`[0,0,0,248]`；旧候选与原脚本保留为`pre-semantic-*`。这次修正发生在看到原生数据之后，故不伪称盲选；没有按漂移结果选点。固定纹理的刚性平移对任何固定材料点相同，本次两点漂移最大差仅约1.82e−12像素，修正不改变结论。

![32个源姿态中的16走路姿态，红点为可见材料候选](walk-32-source-foot-candidates.png)

![32个源姿态中的16跑步姿态，红点为可见材料候选](run-32-source-foot-candidates.png)

图片文件名中的32指本轮总姿态数；每张图实际16姿态。图中裁切仅用于诊断展示；测量使用完整帧，原始帧与全部透明外缘均未改动。

## 姿态可见意图与未知真值

下表的左右仅指图像左右，**不是已登记的同一解剖脚ID**。交叉后不能按图像侧自动追踪同一只脚。低平鞋可作支撑候选，屈腿/露底可作摆动或腾空意图；单张正投影无法证明真实地面接触、足底高度、受力或升空。因此下表为人工图像概观；历史文本另有制作意图（见下段），二者都不升级为实际support/flight通过合同。

| clip | pose0 | pose1 | pose2 | pose3 |
|---|---|---|---|---|
| walk-west | 两鞋展开，是否双支撑未能判定 | 左低平，右折起 | 两鞋展开，是否双支撑未能判定 | 左低平，右折起 |
| walk-south | 右低平，左抬 | 右低平，左抬/露底 | 左低平，右抬 | 左低平，右抬/露底 |
| walk-east | 两鞋展开，是否双支撑未能判定 | 右低平，左折起 | 两鞋展开，是否双支撑未能判定 | 右低平，左折起 |
| walk-north | 左鞋后跟较平，右鞋露底/摆动候选 | 左鞋后跟较平，右鞋露底/摆动候选 | 右鞋后跟较平，左鞋露底/摆动候选 | 右鞋后跟较平，左鞋露底/摆动候选 |
| run-south | 右低，左抬 | 双鞋收起，可能腾空 | 左低，右抬 | 双鞋收起，可能腾空 |
| run-west | 左前鞋低，右后鞋抬 | 双腿折起，可能腾空 | 左前鞋低，右后鞋抬 | 双腿折起，可能腾空 |
| run-east | 右前鞋低，左后鞋抬 | 双腿折起，可能腾空 | 右前鞋低，左后鞋抬 | 双腿折起，可能腾空 |
| run-north | 左低，右抬/露底 | 双鞋收起，可能腾空 | 右低，左抬/露底 | 双鞋收起，可能腾空 |

全部16走路姿态、8个run0/2的低鞋都有需要检验的支撑候选；8个run1/3有可能腾空的视觉意图，S/N也有明确历史prompt意图，但没有绑定实际足点与运行时相位的flight验收记录。不能将后8姿态的材料移动单独判为滑步，也不能将其直接判为腾空通过。

## 实测尺度、行程与条件滑移

所有clip每pose80ms、周期320ms。world05实际speed_factor=0.75；运动physics采样约60Hz。真实纹理到世界比例是`0.0592783503234386` world/source px，camera基向量为4×，实际纹理到viewport比例约`0.2371134` px/source px。跑西额外左pad24仅整帧平移且sprite offset/root同步；足点仍记录canonical坐标，映射时加pad后抵消，不改变世界位置。

actor实际每秒位移约54.001465 world（walk）/80.998535 world（run），与配置名义54/81的微差来自实际浮点物理步进。单pose名义世界持续106.6667ms；actor单pose行程5.76/8.64 world、半周期11.52/17.28、整周期23.04/34.56。**这些是根点按相位移动的行程，不是已证明的足部步幅/同脚stride**；缺同脚ID与接触时刻时不能把它们当真实步幅。

对每个held段保留原phase/position/delta与draw，不重采样、不调速度。用实际`render_source_to_screen`（包含像素snap）投影固定源材料像素中心及sprite offset；从同row未snap的`source_to_screen`、pose_scale与binary64 actor位置解出camera变换。第一实际draw材料点的世界位置仅作为**假设固定地面点**，后续把此世界点投回当前camera，与实际鞋材料位置比较。这样camera跟随不能把脚相对地面的运动藏掉；也没有强钉双鞋、改两鞋y或反拟合新接触点。

以下每格为该pose所有完整held段的**条件漂移中位数 [最小,最大]，viewport px**；未经取整值/两个材料点/所有328段见测量JSON。

| clip | pose0 | pose1 | pose2 | pose3 |
|---|---:|---:|---:|---:|
| walk-west | 16.00 [8.00,24.00] | 18.00 [12.00,24.00] | 16.00 [12.00,20.00] | 16.00 [12.00,20.00] |
| walk-south | 16.00 [8.00,20.00] | 16.00 [12.00,24.00] | 20.00 [12.00,20.00] | 16.00 [12.00,24.00] |
| walk-east | 16.00 [16.00,20.00] | 18.00 [12.00,24.00] | 16.00 [12.00,20.00] | 16.00 [12.00,24.00] |
| walk-north | 16.00 [12.00,24.00] | 16.00 [12.00,24.00] | 16.00 [12.00,20.00] | 20.00 [12.00,24.00] |
| run-south | 28.00 [24.00,32.00] | 24.00 [20.00,32.00] | 24.00 [16.00,32.00] | 24.00 [20.00,36.00] |
| run-west | 28.00 [20.00,32.00] | 22.00 [16.00,32.00] | 22.00 [20.00,32.00] | 28.00 [20.00,36.00] |
| run-east | 24.00 [16.00,32.00] | 28.00 [20.00,32.00] | 28.00 [20.00,32.00] | 24.00 [16.00,36.00] |
| run-north | 28.00 [20.00,32.00] | 28.00 [20.00,32.00] | 26.00 [20.00,32.00] | 24.00 [20.00,36.00] |

每个固定鞋底材料点在同一纹理内都随整帧平移；两脚条件漂移一致。因此在相同held段中，挑另一个固定鞋底点不能把8–36px变成≤1px。物理rolling/toe-off、姿态间同脚轨迹和批准接触窗口仍未提供；本报告不补造这些真值，也不将飞行中的鞋移动当支撑错误。

这些数值是实际原生render变换下的viewport坐标位移，不是OS桌面物理屏幕像素。源像素缩到约0.237px后，特定源像素可能被NEAREST跳采样；红圈标的是该可见源材料候选的投影中心，不声称每圈对应同一被GPU采到的texel，也未把截图栅格足底边认证到≤1px。若对首尾离散栅格轮廓各留约1px定位余量，最小8px的同纹理投影漂移仍明显大于1px；此余量仅作稳健性说明，不能冒充已批准物理接触误差界。窗口管理器/HiDPI/外部屏幕映射未测。物理足底接触不确定性也不能由“红点投影位置精确”缩成0。

## 代表性原生时序证据

每clip确定性取首个完整pose0段，并取该段首尾真实draw。红圈是真实源鞋底材料候选按实际render变换的投影位置（不是逐像素接触认证）；青框是第一draw同材料的世界位置投到当前camera的假设固定地面点。原PNG仍保留，标记只画在诊断副本。全部源截图路径/SHA、binary64 phase/actor位置、physics/process/ticks_usec在测量JSON逐对保存。

| clip / pose0 | physics帧 | process帧 | source phase ms | 实际draw时差 ms | 条件漂移 px |
|---|---|---|---|---:|---:|
| walk-west | 43→47 | 29→32 | 17.5092→67.5105 | 76.233 | 16.0000 |
| walk-south | 308→313 | 199→202 | 5.0088→67.5105 | 77.971 | 20.0000 |
| walk-east | 576→580 | 372→375 | 17.5092→67.5105 | 72.763 | 16.0000 |
| walk-north | 843→848 | 544→547 | 5.0088→67.5105 | 76.098 | 19.9995 |
| run-south | 1109→1115 | 715→719 | 4.9941→79.9928 | 98.824 | 32.0000 |
| run-west | 1378→1384 | 890→894 | 4.9941→79.9928 | 101.821 | 32.0000 |
| run-east | 1645→1651 | 1062→1066 | 4.9941→79.9928 | 104.301 | 32.0000 |
| run-north | 1915→1920 | 1234→1238 | 17.4939→79.9928 | 98.534 | 28.0000 |

![8组同姿态原生首尾draw，保持原生像素尺寸](eight-native-held-pose-examples.png)

代表对不能替代全段分布；完整328段已经枚举。没有从source phase ms推造OS真实elapsed；表格时差取实际ticks_usec。

## 门槛判定与明确缺口

- **Important：全部32姿态的足点/支撑/腾空合同与批准轨迹缺失。** 当前严格支撑验收为`rework_required`/未完成；0px鞋面还原、10循环与纹理身份通过不覆盖此缺口。设计77/88及唯一规范117/153要求不能据此记GREEN。
- **Important：真实速度下存在有条件的明显材料滑移。** 16走路姿态及8个run0/2的视觉支撑候选，应先确定真实接触意图再逐相位处理；在当前固定材料作为支撑的条件下均无法满足≤1px。不能只补一份声称support的元数据而忽略实测漂移。若选择另一套经批准的四帧风格门槛，应另行取得明确标准；本次只读审查不实施任何选项。
- **未验证而非通过：** 8个run1/3的实际腾空、同一解剖脚跨pose/跨周期的接触轨迹、真正步幅/stride、足底三维地面关系与支撑力、walk↔run真实接触相位映射、其它播放速率下脚接触、用户视觉认可。农事工具几何侧车、source material栅格与本结论独立。
- **没有修改：** 原始canonical/源/ownership/帧顺序/时长/世界速度/脚鞋尺寸/渲染/正式合同/构建器。没有新增正式foot合同或把鞋底强钉到同一y。只生成/tmp诊断报告与带标记副本。

可证明范围止于：实际32姿态鞋材料保持、实际GPU身份/PNG一致、真实actor移动和camera/纹理投影、固定材料的条件世界相对漂移。接触真值缺失与条件反证均保留，不冒充完整美术/物理/用户验收。

## 复算文件

- `foot-support-slide-measurements.json`：8clip/32pose/全部328段及8原生代表对。
- `source-sole-candidates.json`：64可见材料候选、真实源/纹理/coverage/坐标/RGBA/SHA。
- `selected-metadata-audit.json`：限定引用链的实际文件/记录范围与SHA。
- `historical-source-intent-audit.json`：沿typed source祖先引用读取的18个JSON/26个prompt与support/flight制作意图；不作物理证明。
- `actual-input-identity-crosscheck.json`：实际GPU/PNG身份复核。
- `analyze.py`、`write_report.py`：仅/tmp离线复算/报告代码，不是播放器/构建器。
- `pre-semantic-*`：最初局部窗口边界触及的真实审查历史。
