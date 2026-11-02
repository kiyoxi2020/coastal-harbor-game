# 六帧参考表工具及上衣源独立复查

日期：2026-11-01。只读复查；未修改项目、美术或代码，未嵌套代理。读取`/private/tmp/coastal-reference-sheet-review-package.txt`、实际两新文件、Task2计划及随后到达的实现报告。审查的reference_sheet.py SHA256为`2fe9be2fa3869f19af2d96dc92ba6ed41897e42063e4f46b58b92adbbc566358`。

## 两项结论

- **规范符合：主要功能符合，路径/symlink门禁有两项Important缺口，修复前不能称全部要求通过。** 真实参考表六格RGBA逐字节等于原输入，含alpha0 RGB的直接复制实现正确；reference-only身份清晰，没有绕过人物构建或登记。旧冻结引擎未改变。
- **代码质量：请求修复两项Important；核心图像复制与完整重建正确。** 已有6测试和全量425测试通过不能覆盖下述实测反例。修复仅需围绕新工具与反例，不能修改旧pack/build/contract或刷新身体归档。

图像附查结论：**六帧r001不是合格同坐标上衣源**。下排三帧领肩位置明显上移，整体同比例无法对齐；不能把下排单独向下挪、独立缩放袖子或登记成严格部件补救。上排仅暂保候选，尚无某帧贴合/完整源通过结论。

## Important 1：verify接受输出文件及祖先symlink

位置：`tools/characters/reference_sheet.py:244`到`:281`，尤其`:250`与`:252`。

verify只拒绝`directory.is_symlink()`，目录内容只检查名称与`is_dir()`。它不会拒绝`sheet.png`/`manifest.json`为文件symlink，也不会拒绝directory某个父路径为symlink。后续`read_text/read_bytes/Image.open`均沿链接读取。即使图像和manifest当前匹配，verify仍错误地将链接制品当作完整可交付的独立目录；外部目标可变动/删除，且不符合此工具声明的拒绝symlink边界。

已在全新的`/private/tmp/coastal-ref-review-*`最小fixture真实复现，三项均**被verify接受**：

1. 先build正确小图，把sheet.png换为指向外部同字节PNG的symlink。
2. 还原PNG，把manifest.json换为指向外部同字节JSON的symlink。
3. 保留正确两文件，从一个带symlink父目录的别名路径调用verify。

修复建议：verify在读任何文件前检查目录的完整合法祖先路径与两个文件组件，拒绝链接而非resolve后隐去链接；要求两项都是普通文件。覆盖三项反例，不只是目录本身的symlink。

## Important 2：来源/正式输出的symlink检查未覆盖库根上方祖先

位置：`tools/characters/reference_sheet.py:92`到`:101`及`:141`到`:158`。

`_resolve_input()`从`characters_root`才开始检查；若`project_root/art`本身是symlink，而`art/characters`是链接目标中的真实子目录，`characters_root.is_symlink()`会返回false，后续components也都是普通目录，于是来源可逃出真实project_root。正式source-reference输出分支从`source_root=project_root/art/characters/sources`起查，同样漏掉art与characters祖先。

已用`/private/tmp/coastal-ref-ancestor-*`fixture真实复现：`repo/art`链接到`real/art`，六张PNG实际在`real/art/characters/sources/...`；`_validate_inputs(plan,repo/art/characters)`全部接受，真实源不在repo下。

临时输出分支恰好从`/private/tmp`开始检查，会拦截其下art链接，所以在tmp fixture直接build正式路径时先被临时分支拒绝；不能把该一次拒绝当成workspace正式分支已经安全。workspace不在/private/tmp时走`:158`的source-root起查逻辑，代码明确不覆盖这两个祖先。应从可信project_root检查输入/正式输出完整组件，且与真实允许根核对；保留临时分支对`/private/tmp/coastal-*`的约束。

修复建议：给输入`art`/`characters`祖先链接和正式输出的对应祖先链接补测试；不要只加最终文件链接测试。测试可在临时fixture构造真实外部目标，不能修改项目目录。

## 其余代码检查

### RGBA完整性与真实参考表

`_validate_inputs`要求输入已是RGBA且尺寸与cell一致，没有转换、缩放或mask。`_make_sheet`以`sheet.paste(frame,(x,y))`无mask直接复制，保留半透明和alpha0像素的RGB。实现没有alpha-over、部件裁切或坐标变换。

本复查实际调用真实reference目录的`verify()`通过，并另外对manifest列出的六格逐一裁取**只读比较**：每格`.tobytes()`都与其输入原图完全相等，六项全true。真实表为3072×3072、每格1024×1536。未生成或修改诊断图片。

已有测试的alpha127及alpha0非零RGB检查是有效验证；直接paste而不是带alpha mask paste是正确实现。

### SHA、路径、新输出与manifest

- 输入SHA校验、根命名空间、绝对路径/`..`/反斜杠拒绝、重复路径、固定六项/3×2、RGBA/同尺寸检查正确；但symlink边界如上不完整。
- build输出限制为新`/private/tmp/coastal-*`后代或`art/characters/sources/<id>/references/<revision>`，已有目录不覆盖。正式输出的上级链接漏洞需修复。
- manifest完整记录标准化plan及digest、每格源SHA/位置/尺寸、工具/Pillow身份、PNG SHA与RGBA SHA、reference-only状态。
- verify由当前源重建PNG及RGBA并比较整个expected manifest，因此修改输出像素同时只重算output哈希仍会失败；修改cells/tool/status等metadata也会失败，不能靠手改SHA修复来源差异。嵌入plan不是外部签名或用户认可，报告没有将其当成这些资格。
- 两套`_read_plan`与`_read_plan_from_object`的校验较重复，当前行为基本一致。可选的小质量建议是共用一份对象规范化器，降低未来build/verify漂移；这不是本轮必须扩展范围。

### reference-only边界与冻结工具

新工具仅依赖Python标准库及Pillow，不导入旧人物build/contract/pack引擎。它的`coastal-character-reference-sheet-v1`/`reference-only`不等于`coastal-character-construction-v1`配方或严格build manifest，不提供人物合成、源登记、正式发布或用户认可。

复查时再次将live SHA与archive-r001.json的586项files中对应值比较，以下4项均一致：

- pack_sources.py：`0a77bec9452f18faabe57b51fc0a6e493249dc311da4384d873eff5efb4d3d4e`
- build.py：`6ab31ab7d8e899c4ec00e689e04eb327e21e00309bd0632b5db49c958e5e516f`
- build_contract.py：`3b318591071691e12fbc5ab9cb2c10b6d4f0f605a1097697253b514122971fa5`
- composition_contract.py：`1ee62590d94da01b0a4c7c046a5de71052a6a25fd3cfc700807d181217826a0c`

因此新增reference工具本身没有改变这些现身体冻结引擎。此次只核对4项，未声称复核全部586文件或重新获得身体美术认可。

## 生成图像：按唯一全表比例附查

已分别用view_image查看：

- `art/characters/sources/top04-adult-v2-west-walk-r001/references/r001/sheet.png`
- `art/characters/sources/top04-adult-v2-west-walk-r001/originals/six-sheet-r001.png`

实际生成1254×1254、3×2、每格418×627。相对原3072×3072，唯一全表比例为209/512；把此比例用于全部格位，不能再独立移动某行/某帧/袖子。

肉眼对照可见：生成下排的领口/肩线与对应body颈肩不在同一高度，袖口/腰线也跟随上移；属于帧间格位漂移，不是只返回统一小尺寸。上排的整体领肩高度相对接近，但袖子的横向范围/腕口方向也不能据外观一致认定贴合，尤其第一格袖口明显扩出原手腕位置。

为辅助复核这个结论，本次只读取源像素做有界颜色定位，没有制造ownership/coverage/occlusion mask：body每格取y680–1099的低饱和灰色不透明像素（通道差<12、min>90、alpha>220），生成图取红色不透明像素（R>1.3G、R>50、alpha>220），记录其最上缘。颜色只用于定位明显肩领高度趋势，**不等同解剖锚或正式衣物归属/覆盖验收**。

| 帧（0起） | body上衣灰区起点y×209/512（格内） | 生成红衫最上缘y（格内） | 生成相对body的差 |
|---|---:|---:|---:|
| 0 | 296.4 | 301 | +4.6px |
| 1 | 296.8 | 307 | +10.2px |
| 2 | 296.8 | 307 | +10.2px |
| 3 | 293.9 | 220 | −73.9px |
| 4 | 293.9 | 225 | −68.9px |
| 5 | 298.0 | 227 | −71.0px |

下排偏移约69–74生成像素，换回原格约169–181像素，远大于普通边缘/领口版型差异。不能以统一缩图解释，也不能通过各帧登记偏移把生成漂移合法化。图中绳纹/砖红款式成立不证明领肩、袖腕、腰线贴合；也未检查衣身隐藏完整面，不能称可组合部件。

处理建议：保留本次原始PNG、prompt/共同参考与真实尺寸记录，将r001记为六帧同坐标失败候选；按原计划改为同一body单姿态生成/修订验证。上排可继续作为候选逐帧核查，不先写“合格帧”或把任何帧推广到idle/六帧兼容。不要进入严格配方、原生动态或生产接入来掩盖源坐标问题。

## 验证与未验证

独立执行：真实reference verify、6格RGBA逐字节比较、输出/输入symlink最小反例、冻结4引擎SHA比对、两原图view_image及只读格内位置统计。

实现代理报告6单测通过、全量425/425（244.194s）；本复查未重复整套测试。实现报告生成时check.py仍在运行，最终结果由主代理/实现代理提供，本报告不假称check通过。未执行Godot、动态衣物播放、严格新衣物build/verify或用户视觉验收，源坐标失败使这些后续验收尚未具备条件。

## 追加：单帧回退single-pose0-r001原坐标核查

本节独立查看了以下三张图，没有重查已失败六帧表、没有处理或覆盖美术：

- `art/characters/sources/top04-adult-v2-west-walk-r001/originals/single-pose0-r001.png`，实际RGBA 1024×1536。
- 原body：`art/characters/sources/visible-atlas-body-r001/originals/suit-walk-west-0.png`。
- 主代理诊断：`/private/tmp/coastal-top-single-coordinate-diagnostic-r001/body-top-overlay.png`，三栏body/衣物/原body+衣物；按同一整帧23/194登记至256×224/root(123,201)，未单独挪缩部件。诊断只是原坐标观察，不是严格登记或原生动态证据。

### 单帧结论

**可保留为款式与进一步同姿态修订候选，但还不能认定“领肩/袖腕贴合通过”，也不宜把第0帧当已合格共同接口后直接宣称其余五帧适配。** 这一帧的大尺度格位已比整表稳定，衣身/袖子明确对应第0帧方向；问题集中在袖口盖入原手掌，以及领肩位置偏高。应先修订/确认当前真实腕口接口，再以同一源作为款式参考扩姿态。颜色、绳纹和毛衣外观本身不是贴合证据。

- **领肩：** 生成的后领/肩顶高于原灰衣肩线；厚罗纹领口可有版型高度差，但当前图在后颈肩处明显向上覆盖，不能直接当精确同肩锚贴合。需要沿实际颈根/肩线确认它是批准的领口版型，还是生成漂移；不能单独向下挪毛衣修正。
- **袖腕：** 两袖口进入原body手掌上部，三栏中的露手面积明显小于原body。左侧前摆手的盖掌尤为直观；右侧袖口也压到原手掌上沿。这不是原body灰袖尚未盖满的问题，后续不能擦除原手、重画手或把袖子独立缩短缩放来通过。
- **腰线：** 罗纹下摆在当前原body腰髋上缘附近，未见六帧下排那样整段错层，但灰底连体衣本身没有可直接等同外套腰线的分割接口；单帧看不到明显腰部断口，不等于裤装/其他上衣组合已兼容。
- **人体/灰底混入：** 原始上衣图肉眼未见新脸、手掌、裤腿或灰色连体衣碎片，主要为砖红毛衣及轮廓。这个判断不替代真实source ownership及完整隐藏衣身检查。

为了定位盖掌疑点，本次只读body中两个手部ROI的肤色像素（alpha>220、R>150、R>G+25、G>B+15），再检查同坐标上衣alpha支撑；这是颜色辅助定位，**不是正式手掌ownership或解剖mask**：

| ROI，原源像素 | 定位到的body肤色像素 | 同坐标上衣alpha≥220覆盖 | 比例 |
|---|---:|---:|---:|
| 左手 x230–374/y900–1064 | 7510 | 3543 | 47.2% |
| 右手 x630–789/y940–1109 | 9319 | 4466 | 47.9% |

该较大重叠与原生大小诊断中手露出变小相符，不能把它简单归为抗锯齿或1像素袖口边缘。最终腕口位置应回到实际body边界/手腕标注，不按本统计自动抠图，也不以此统计生成mask。

### 真实alpha检查

- PNG为RGBA，四角alpha均0，有真实透明背景；alpha0像素1,450,230个、alpha1–254像素122,634个。
- alpha最大值254，alpha255像素为0。毛衣主体视觉接近不透明，但**不能将254声称255**，也不能把其支撑用于现合同要求“alpha恰好255”的二值前景擦除。
- 非零alpha完整bbox为(81,499)–(1010,1272)，包含低alpha光晕/边缘；alpha≥16 bbox为(247,675)–(782,1042)，alpha≥220 bbox为(248,676)–(781,1041)。低alpha外扩应保留真实源并在明暗背景原生尺寸下审视，不能为获得干净bbox擅自阈值清理。
- 对alpha>220像素的只读粗筛未发现亮中性灰色块（通道差<12且min>90的计数0）；肤色相近色阈值有25点，可能来自毛衣高光颜色，不能由颜色阈值独断为皮肤或反过来声称正式归属已完成。

### 本节边界

这一帧未获得用户美术认可，未完成独立完整衣身/前后袖分层、真实ownership/coverage/occlusion、idle、另外五姿态、严格新配方构建或原生walk≥10循环。此静态对照不能解除先前记录的源登记、前景手分片与v2评审入口缺口。

## 最终追加：reference_sheet路径修复复查

复查依据：`/private/tmp/coastal-reference-sheet-review-package-fixed.txt`、对应live两文件及更新实现报告。最终live工具SHA256为`6b4b1d9836628744c510c6a2b2c0dda2bc0da3940495e6ee75cb7ed7b0dff299`，与实现报告、真实新r002 manifest记录一致。

**规范符合结论：通过Task2参考表工具限定范围。代码质量结论：通过，两项Important已关闭，未发现新的阻塞问题。** 此结论只针对reference-only工具修复，不覆盖上衣贴合/完整源/动态或人物发布；前文生成图像失败及单帧袖腕疑点结论保持。

修复以不resolve掉链接的完整绝对组件检查覆盖project、plan、characters根、source、output和verify两个文件；旧版从库根起查漏上级，以及verify只查目录本身的问题均已覆盖。

本次在**全新**`/private/tmp/coastal-ref-final-review-*`fixture独立重现原问题及相关边界，以下7项全部抛ReferenceSheetError明确拒绝：

1. sheet.png指向有效、同字节外部PNG的symlink。
2. manifest.json指向有效、同字节外部JSON的symlink。
3. 输出目录路径含父级symlink。
4. 来源路径的art祖先为symlink，使真实源位于project外。
5. build使用带art祖先symlink的project。
6. `_output_path`正式source-reference位置含art祖先symlink。
7. plan文件symlink。

随后同一正常小图fixture仍能build/verify，直接复制的alpha0非零RGB保持(10,20,30,0)。不是只拒绝所有路径来“修复”测试。

真实`art/characters/sources/top04-adult-v2-west-walk-r001/references/r002`已用最终live工具独立verify通过；再按其manifest逐格读取六原图并与sheet格内RGBA `.tobytes()`比较，6/6完全相等。没有修改r001或其旧工具identity来继承本次结果；r001继续保留原始证据身份。

再次只读核对archive-r001的对应冻结项：pack_sources.py、build.py、build_contract.py、composition_contract.py四项live SHA均与归档一致。没有为此次修复更新旧冻结引擎/身体归档/生产基线。

实现代理报告新增反例先失败、修复后13项单测通过；本复查没有重复完整测试或check.py，最终全量与仓库门禁由主代理运行。本次仅执行上述独立最小反例和真实r002精确RGBA验证，未修改项目、美术或运行资源。
