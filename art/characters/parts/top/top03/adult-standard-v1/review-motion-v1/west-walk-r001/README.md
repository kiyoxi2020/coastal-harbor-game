# top03西walk有限材料适配

views.json按真实source pose登记：四个outfit raw分别供各自袖子，完整torso源始终walk_west_0，零位移映射其他walk；exact idle单独使用原已交付raw。所有raw1024×1536完整nearest1/2归一到512×768，不缩单独衣片。

canonical-surface-alpha-v1有限材料合同保留真实源RGB，只在真实source ownership内继承该source pose的canonical B alpha；每个owned点的原材料与canonical alpha均必须>0。exact idle原owner中两者alpha0点均0，旧top RGB完全相同，2689处合法alpha继承后逐RGBA精确还原。不能用透明RGB填缺墨。

归属由原实际衣物表面许可＋完整源领口/两只手的人工负向语义边界决定；颜色只报警，不分类。source-body-exclusion-boundaries.json保留坐标与来源语义。actual source透明区不当衣料，原颈/腕/手和接触描边不从生成图导入。米白条纹肩缘[327,407]实为衣料阴影，目视确认后保留，未为凑颜色计数擦掉。

每target coverage只选当前有限实际衣料表面，依原完整层序排除真实canonical可见手前景（扣除后续衣身/袖子实际强paint覆盖，保守保留弱/混合接触边）；源部件保持完整raw，未逐帧擦body或用volume遮错。袖/torso属于finite-canonical-material，非完整隐藏衣物能力。新walk保留原身体/裤鞋并选择真实衣料，不要求复现旧诊断composite的混合RGB。具体权限/源SHA与例子见evidence/material-semantics.json；该证据被recipe authoring_inputs绑定。
