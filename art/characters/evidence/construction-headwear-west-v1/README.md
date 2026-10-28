# 西锄四固定头部状态：统一构建小样

2026-10-29交付。范围：成年母版、条纹上衣、原裤鞋，西锄四姿态＋匹配西向待机，bare/hair/hat/hair_hat四固定配方。均为review-only；生产发布仍关闭。

```sh
python3 tools/characters/review.py headwear-construction
```

入口逐一verify四构建后，进入现有发帽评审场景。仅西锄可选，右下切换四状态；左侧可暂停、逐帧，G启动世界锄地。评审状态切换保持时钟；这不授权生产动作中换装。

## 实际交付与验证

- 同一 `coastal-character-construction-v1` 的schema2，引用严格r002衣装配方并重建，统一整帧登记后在目标画布组合头层；没有新批次构建器。
- 四配方位于 `recipes/headwear-hoe-west-{bare,hair,hat,hair-hat}/r001.json`，四输出位于同名加 `-r001` 的 `builds/` 子目录。原图、prompt、旧sample、旧认可和runtime-baseline保留。
- [equivalence.json](equivalence.json)：20/20逐RGBA完全一致（包含透明RGB）、原姿态顺序/时长/画布不变。
- 114项Python人物测试、check.py通过；门禁计strict_recipes=5、strict_builds=4、冻结旧配方9。
- Godot synthetic 134、真实actual 48通过；旧loader34/actual98/trial90回归通过。
- Apple M4 / macOS / gl_compatibility原生120项检查通过；四state各十面板循环，3,307条原始binary64时序样本；世界每state四pose、live切换时钟和结束idle通过。
- 新原生合同绑定4,422项输入、215张PNG；[receipt.json](receipt.json)与[report-summary.json](report-summary.json)记录校验范围。

## 原生代表图

- [发帽浅底五视图](hair-hat-light.png)、[发帽暗底五视图](hair-hat-dark.png)、[仅头发暗底](hair-dark.png)。每张原生2240×480，未缩图存档。
- [发帽第三帧世界图](world-hair-hat-key2.png)、[仅头发第三帧世界图](world-hair-key2.png)，各300×320原生裁区。
- [主代理目视记录](visual-review.json)：未见新的明显帽头接缝或已报耳后缺口回归；只代表所列抽查，不是用户认可或全帧视觉验收。

动作源画布1536×1792、scale=138/1164；idle源512×768、scale=138/582，整帧显示尺度沿原配方。部件不单独挪缩。头部注册图是目标画布，衣装源框平移只执行一次。

## 证据留存与限制

完整原生采集及原始report：`/private/tmp/coastal-west-hoe-construction-native-01`。该目录不是Git永久归档；保留全部原PNG和报告，不把重新运行当原证据。库内保留确切input-contract、receipt、摘要与五张代表图。采集入口拒绝任何已有额外产物、链接或越界路径，不能对旧目录重复采集。

[旧证据影响](prior-evidence-impact.json)：旧layout-native合同的headwear_samples与headwear_trial两份脚本已改变，其原回执仍是历史证据；本轮只重新认证西锄构建suite，不扩大到其他旧样例。

未验证OS键鼠/WM焦点、严格足/握持/目标接触、跨平台或导出；连续动作保存为带时序的PNG采样，不宣称全帧率录像。未登记新的用户认可，未切换生产角色。其他动作/四向/体型与生产发布属于后续独立任务。

独立最终验收：[2026-10-29-west-hoe-construction-review.md](../../../../docs/reviews/2026-10-29-west-hoe-construction-review.md)，规格、质量与证据完整性PASS，无未解决问题。迁移校验2986映射/35 artifacts/257显示帧、静态校验60候选通过；59个现有文档链接检查通过（本条新增验收链接随后单独核对）。
