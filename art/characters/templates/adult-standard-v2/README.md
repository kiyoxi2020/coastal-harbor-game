# 成年标准身体候选后继修订

这是Q19认可灰色不透明连体底衣完整母版的候选登记，仍属`unified-composable-character-v1`，不是第二套模型/构建管线。当前生产仍用冻结旧资源；本候选不改变旧template、catalog、发布清单或runtime-baseline。

`body-motion-v1`包含四向六动作、108姿态，两种明确variant：`visible`在农事保留完整工具动作，`body-reference`用于无工具姿态参考；非农事共享相同PNG。共164个源格作精确矩形提取，未重画/缩放/挪动身体部位或编辑alpha。来源在`sources/visible-atlas-packed-r001/`，不可变提取映射逐文件绑定Q19源图集与RGBA。

严格配方为`recipes/adult-standard-v2-visible/r001.json`与`adult-standard-v2-body-reference/r001.json`，均使用原有`coastal-character-construction-v1` schema3及`build.py build/verify`，仅body槽。它们不是旧迁移配方，均为review-only，未继承旧人物、旧身体或Q19以外的严格动态认可。

新登记只冻结当前实际像素、pose、布局和时序。尚无新增发帽16状态、衣裤鞋混搭、正式生产资格；支撑脚/工具接触及衣物接口不得从可加载或静态还原推断通过。`visible`与`body-reference`由生图分别生成，不宣称是像素完全一致的可分离层。
