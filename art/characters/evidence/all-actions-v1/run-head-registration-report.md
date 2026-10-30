# RUN A 四向固定 hair_hat 严格登记

范围：16 个真实 RUN A pose＋4 个冻结 B idle；全部 review-only。未宣称 RUN B、full24、原生动态或用户认可。未改引擎、消费者、生产/current/baseline。

| 方向 | 最终build | recipe SHA256 | artifact digest | inputs |
|---|---|---|---|---|
| south | `builds/headwear-newrun-south-hair-hat-r002` | `1b37bf82d8dc5231ec842af3e25561b6764f5af09393010896d6007a93d0bbe5` | `15d19639ee8140782703871df97d110da3f6cf4f010b53076e60e66cc1a2a30f` | 173 |
| north | `builds/headwear-newrun-north-hair-hat-r002` | `8218366a3fd2407baf29983c102e85299e8441e5f0c21c327918e1c4e594a4a1` | `baef354147bff740f6613d26041b58fe89da76fc4de1d3eb533e690059be143d` | 172 |
| east | `builds/headwear-newrun-east-hair-hat-r002` | `bc47dd84d7dd1b0fae4a00a89d7189cc618ef0896d9d5b974e04de6739e9c92e` | `b449bcbae3259979dedde791c3853f82a50148882ce8dced6334aa5c9fd5a057` | 226 |
| west | `builds/headwear-newrun-west-hair-hat-r003` | `c3089ef0f19e031d4c1fd6c300523241704bd4c69b68f8a3e848b5d443edbdd3` | `72865ce317352da556f1731880f0628bddbca21d8caf851c687efc5b4316b954` | 185 |

全部使用 `tools/characters/build.py build/verify`。4组各5帧 PASS；20帧全部实际输入及三个冻结engine文件复hash一致；每帧共享compose逐RGBA重建一致、所有头部实际材料支持区之外0差、y≥400整身0差。原眼/耳安全内部0差；4个idle与对应 walking冻结idle的完整PNG字节和RGBA均相同。

资源入口：每个方向 `parts/{hair-chestnut-short-v1,hat-straw-navy-band-v1}/{revisions,adaptations/...}/newrun-<dir>-r001/`；独立annotation为 `templates/adult-standard-v1/motions/review-motion-v1/annotations/head-newrun-<dir>-r001/poses.json`。每组实际输出、hash与不变性证据持久化在hair adaptation的 `evidence/strict-source-registration-and-invariance.json` 与PNG。

South：完整source-r001/r002、两次实际prompt/refs在 `sources/gpt-run-south-underhat-v1/`，最终raw SHA `243b0a78e94e71f8c81290de874b14c867fc61a2abea82c9471416ed6ea6f9d8`，全源1/2 NEAREST。actual source pose为A_S0，真实耳宽270 vs目标269–270；独立眼/耳残差≤1px。仅取真实发，15个确认的发梢/皮肤混色点保守留原人体，手工界面+原RGB证据在actual-source-anatomy-seam-review.json。连续真实α1外缘尾在每pose冠ROI帽面外仍保留1点，强前景0；不擦、无volume。

North：完整source/prompt/refs在 `sources/gpt-run-north-underhat-v1/`，raw SHA `816ac5e2884817a1b80020be3b5865414ba6aceb011318556d82bfeb461a3183`，全源1/2 NEAREST。source pose为A_N1，真实耳宽262 vs目标261–264，独立耳残差≤2px；55个确认耳后皮肤/发间暖色混边保守留原人体，真实相邻棕黑发束保留。4pose实际冠面帽外全α0。S/N实际原帽near-only，whole真实帽owner重建，不造fake far；原帽skin已在冻结来源中排除。

West：W0/W1保留原完整idleB1 source及真实visible-underhat材料，眼/上耳残差≤1px；隐藏颅顶y残差11/5px如实保留，真实上颅强前景均被实际完整帽alpha覆盖，不宣称精确颅形或隐藏发冠。W2/W3采用 `sources/gpt-run-west-wearing-v1/` 新完整真实wearing source，SHA `204e276e24c53d5a3add344defec650d413310af286ea8b165f8515e7a8e26c9`，1086×1448→576×768统一96/181，整帧原内容窗口返回64px，source_pose保持A_W2。眼＋下耳碗W2给完全同一delta；W3残差≤2px。手工真实帽/发分类，原眉、整耳、耳后skin和颈描边不入角色。帽真实near/far互斥并集重建全部帽ownership；不宣称隐藏冠。

West四RUN统一padding[24,0,0,0]，交付536×768/root[280,708]，annotations仍512×768/root[256,708]。所有实际帽α完整保留，late所需最小left15/16px；例真实gold raw[164,368]→atlas[87,195]→canonical[-4,186]→output[20,186]逐RGBA一致；人体和头部都整帧pad，世界位移不变。idle无pad且exact。

East：`sources/real-run-east-headwear-v1/` 从Git379a9bc精确保全三份完整GPT帽raw、真实prompt/生成references、旧manual contours；underhair完整四pose源仍为 `sources/motion-headwear-sampling-v1-0e05155b/originals/source-v1-6cb90493.png`（SHA fca1724d…）。4个raw source-full-frame逐RGBA精确重建旧真源，near/far互斥并集全部真实帽，不把旧cap-volume名当擦图。原face/ear/brow/skin/gray背景排除。R0/R1按实际耳眼眉质心分别half-up source/target后delta[12,8]/[7,6]；R2/3为0。独立feature形状残差仍留存（hair R1 brow≤4px、hat早帧多点≤3px），不伪称exact projection；有限可见fringe/side/nape，缺失隐藏冠被真实帽面遮住。

所有发/帽intrinsic身份＋独立typed compatibility均由最终mapper验证，source_pose没有改成target动作；完整生成body只作来源/测量见证，canonical A始终是脸耳手body父级。没有新合成器、播放器、局部缩放、镜像、height百分比、source重命名或cap-dependent erase。

未冻结中间构建及实际inputs/engine closure已在/private/tmp归档：coastal-newrun-{west-pre-interface-fix,east-pre-centroid-quantization,south-pre-anatomy-seam-review,north-pre-anatomy-seam-review,west-pre-unused-landmark-label-fix}。只保留新最终build目录；W最后仅删未使用错误测点别名，五PNG/RGBA与修正前完全相同。

验证：4build/verify＋20帧不变性/源RGBA已PASS，git diff --check PASS。最终源边界修订后的221工具测试PASS（306.140s），check PASS（strict_recipes26、strict_builds22、frozenlegacy9；production closed）。日志分别为 /private/tmp/coastal-newrun-head-tools-tests-final.log 与 /private/tmp/coastal-newrun-head-final-check-frozen.log。原生12cap连续循环、世界移动与接触由主代理集成，不以本报告代替。
