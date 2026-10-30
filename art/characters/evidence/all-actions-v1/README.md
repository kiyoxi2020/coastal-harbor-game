# 固定发帽组合：全动作实施证据

当前已构建固定top03／原裤鞋／栗短发＋草帽的统一包：24动作方向、84姿态，review-only。唯一[构建](../../builds/adult-top03-full-hair-hat-r001/manifest.json)绑定artifact `61d071a98a25ee765be62fa4d4623cae074d4097327c8e781ca3a207b6af421a`。来源与严格构建完成；用户Q2=B明确按当前四关键帧像素步态接收本轮完整统一评审包，交付已完成；严格足底支撑／滑步保留为后续未验证事项。

- 完整试玩：双击 [review-all-actions.command](../../../../tools/characters/review-all-actions.command)，或运行 `python3 tools/characters/review.py all-actions-construction`；六动作四方向、固定hair_hat，暂停/逐帧可用。
- [原生动作总览](native-r001/videos/all-actions-native-overview.mp4)：20组各十轮／实例的实际原生帧，分组章节，151.749秒；有损视频仅供观看，原始PNG和时钟为证据。
- [84姿态原生1×板图](native-r001/native-pose-boards/)、[102／8407栅格核对](native-r001/contact-raster/final-summary.md)、[足底支撑审查](native-r001/foot-support-review/review.md)。栅格最佳偏移均0不等于足不滑。
- [当前门槛状态](current-delivery-readiness.json)、[统一构建来源](unified-package-r001/)、[原生尺寸合同](native-r001/source-output-native-sizes.json)。原始报告/输入/所有PNG按无损gzip/tar保存，等SHA图片使用标准tar hardlink，全部成员重新读出校验。

用户已选Q2=B，范围决定见 [q2-b-decision.json](native-r001/q2-b-decision.json)。本轮24格84姿态按当前四关键帧步态完成评审交付，严格支撑后续处理，未冒称已通过。生产player-unified-v4、baseline、存档和导出均未切换，未提交／推送。

## 历史证据说明

下文为早期范围的历史恢复记录；新统一包与后续原生记录不继承其认可。

## 历史恢复

`history.json`记录Git提交2742c19的四个西锄strict build、实际输入/输出、构建工具与必要轻量原生证据，共223个Git文件（约67MB）。已按Git blob逐字节恢复至`/private/tmp/coastal-all-actions-history-2742c19`，四build均用恢复的旧工具执行verify通过；Python/Pillow身份及每文件SHA/Git blob保存在清单。

恢复目录是临时核验副本，不是永久归档。永久恢复依据是清单中的Git commit/blob，重建历史时必须使用该版本工具和记录的Pillow版本；不能用旧manifest认证新代码。三处外部过程/GPU资料的存在性另记于external_evidence，均未宣称永久归档。

实施过程中不覆盖旧manifest或刷新runtime-baseline。新engine使旧build过期时据实记录，新目录重建并重验后才迁移当前评审引用。
