# adult-v2-top04-west/r001：七帧严格配方独立复核

**结论：通过本轮西向idle＋六walk有限制作小样的数据与静态画面检查，未发现阻塞问题。** 原canonical body未修改；衣物来自已绑定prepared派生源，root与完整帧登记一致；body-raster-support只表示真实body alpha支撑，未冒充coverage/解剖表面。不是完整衣柜、隐藏衣身、动态/原生世界或生产通过。

审查：新recipe、top04修订design、views/mappings、v2 annotations/scope、prepared计划/source bundle与严格manifest及七张实际PNG；查看`/private/tmp/coastal-top-strict-seven.png`。未读取或审阅正在施工的registered adapter代码，未修改文件或跑全测。

## 身份、能力与范围

- recipe为`coastal-character-construction-v1` schema3，唯一model=`unified-composable-character-v1`，template=`adult-standard-v2`、motion=`body-motion-v1`。
- 仅body/top两槽。design ID保持top04，revision=`adult-v2-west-r001`；范围明确review-only、west idle+six walk，不继承其他动作/隐藏源/生产资格。
- 两clip均选真实`body-reference` variant：idle_west_0为1000ms，walk六pose顺序为0–5、53/54/53/53/54/53ms，共320ms。声明能力与实际clip一致。
- 所有frame均`registration:null`、`composition:alpha-over`、层序body→top；两层full_frame、offset(0,0)、local_scale(1,1)。没有新增脸手层、第二个body、coverage替换或occlusion擦除。
- prepared source bundle明确`prepared-derived-review-only`、accepted=false、runtime_eligible=false、complete_hidden_source=false；未把prepared派生PNG冒充新GPT原稿。

## 来源、登记与纹理逐RGBA复算

独立检查严格manifest **211项input文件SHA全部匹配**，当前三构建engine SHA匹配，artifact_digest按实际inputs+engine重算相等。manifest保持review-only/release_eligible=false，七输出文件SHA和RGBA SHA均匹配。

七帧逐一检查：

1. source_pose与target_pose绑定同一真实annotation document/record；record的poses/variant/pose_id/reference_frame均对应当前canonical。
2. source/target canvas256×224、root(123,201)、display_scale1.0；mapping锚`root`的source_px与target_px均(123,201)，delta=0。
3. **直接用真实raw source、raw ownership与绑定body packing计划独立复算**：walk先取对应418×627源格，density_ratio209/512；idle取1024×1536完整源格，density_ratio1/1；整帧inverse仿射由该pose真实body source_root、body比例23/194和target root推导。对原RGBA、二值ownership分别一次nearest登记到256×224，与实际prepared materials和ownership逐字节相等。未用逐帧额外偏移或单独衣袖缩放解释差异。
4. 对materials以其实际二值ownership复制原RGBA到透明画布，所得与mapping texture完全相等；mapping texture又与prepared textures逐RGBA相等。没有重复乘alpha或重画衣物。
5. 严格输出按真实层序从透明画布依次alpha-over原body、top，独立重算与七张实际输出逐RGBA完全相等。这里保持alpha-over的透明背景语义；没有把“输出透明RGB一定等于原body透明RGB”错误当作合成要求。

prepared source bundle列出的实际inputs全部在strict manifest中以同SHA绑定。recipe的173项authoring inputs包含原穿戴PNG、精修mask/边界JSON、实际prompt、准备计划/manifest、canonical姿态/body，以及既有body packing计划闭包。复用完整body归档准备计划使部分其他动作原稿/提示词也在该既有闭包中；这不代表新top支持那些动作，也不把这些authoring输入变成新的运行人物层。

本复核验证实际数据/像素，不审查source-preparation工具实现；其通用工具代码与拒绝反例由另一独立审查负责。

## body-raster-support语义检查

scope.json明确声明：二值mask为完整canonical body真实alpha>0支撑，包括低alpha边缘；不是torso、source ownership、target coverage、occlusion、物理轮廓或接触证据。

独立逐帧从实际canonical PNG的alpha>0生成L支撑，与七张surface mask逐字节相等。支撑255像素数依次：idle5293、walk0=6365、1=5581、2=6012、3=5933、4=5535、5=6228（画布总57344像素），没有all-white或bbox伪表面。

所有mapping与layer的coverage/occlusion均null；surface只绑定真实body层。该用法符合本轮普通alpha-over叠加的有界合同，不要求为了通过验证假造不存在的身体上衣分层。未来做删灰底、前景手分片、解剖覆盖时仍须补真实相应接口，不可沿用raster-support偷换语义。

## 原body与冻结引擎保持

七帧body layer纹理逐RGBA等于各自canonical，且相应文件SHA与身体archive-r001冻结值一致。另对归档内**108张canonical body PNG**的live SHA做只读比对，108/108保持原值。

pack_sources.py、build.py、build_contract.py、composition_contract.py四个冻结引擎的live SHA也与身体归档一致。未刷新旧archive、旧build manifest或runtime-baseline。

## 严格输出静态接口

已看主代理七帧明/暗面板：

- 衣领与原身体颈部贴合，没有新肤色片、双颈线或明显灰底领圈。
- 袖口与当前原手匹配，前摆/后摆造型分别对应各pose，未见大块灰袖外露、重复手或断腕。
- 腰摆红罗纹及黑边连续，灰裤与下肢沿原body保留；未见大块灰裤被带进top或明显腰部断口。
- idle与六walk体型/画布/根点一致，没有通过移动或缩放body来适应毛衣。

面板是静态PNG对照，不是GPU原生或连续动作证据。<1像素级袖腕/领口抖动、循环首尾/idle切换、实际位移与前后关系仍须由正在接入的统一消费者及原生连续验证决定。本报告不提前写motion_checked/native_checked/user_accepted或发布资格。

## 本次未执行

未重跑全量人物测试、check.py、Godot或严格构建CLI；主代理已有实际构建/verify，本次用独立SHA/登记/纹理/合成复算验证同一七帧，未重复其实现或审阅施工adapter。未进行任何项目写入。
