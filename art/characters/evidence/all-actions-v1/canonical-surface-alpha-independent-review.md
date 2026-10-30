# canonical-surface-alpha-v1 独立定点复查

结论：PASS，限定为 source annotation canonical frame 的有限可见材料 alpha 继承；没有发现 Critical / Important。只读审查父代理新增约30行与5个相关测试，不改 core。

核查了严格 wrapper keys / schema / finite-canonical-material scope；仅 top/pants/shoes；material_extraction 经原严格 kind 分支验证，nested wrapper 会拒绝；alpha_reference 必须等于已校验 source annotation.reference_frame，且 SHA/实际 PNG 进入依赖；owner 内 raw alpha0、canonical alpha0 均拒绝；只改 owner 内 alpha，全部 RGB 保留，owner 外 alpha 保留。原各 extraction kind 未包装时的分支原义不变。

新增5 tests静态检查：实际construct/verify正例、无关alpha源、错误hidden scope、raw材料孔洞、nested wrapper。没有重复运行父代理已经通过的5 tests。

另用独立小图算术探针实测：raw (201,30,40,128)，canonical alpha73；owner内输出 (201,30,40,73)，owner外仍(201,30,40,128)；canonical alpha0以ValueError拒绝。探针只验证此新增运算的必要边界，不声称替代annotation/closure集成测试。

Minor：现正例canonical alpha全255，建议补非255 canonical正例以及canonical alpha0、hat slot反例，逻辑已明确拒绝，非阻塞。

能力边界：此wrapper继承的是source canonical alpha。若source_pose与target_pose不同，经过锚映射后不自动证明target canonical frame的alpha相等。南组全部同pose，实际5帧新构建已额外逐像素证明全画布alpha差0。source mask的布料语义与不是halo的视觉真实性仍属于真实来源/人工归属证据，rawalpha>0不构成自动视觉认可。
