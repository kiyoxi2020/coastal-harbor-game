# idle r002可见上衣提取：独立复核

**结论：通过本轮可见idle毛衣抠图的有限检查，未发现需要追加定点修订的明确问题。** 无肌肤/灰裤大块残留，领口、袖口、下摆保持合理，保留像素RGBA与原source完全一致。此结论不是完整隐藏衣身、严格构建、动态换装或用户认可。

已查看`/private/tmp/coastal-top-idle-mask-r002/source-light-dark.png`的原source/明底/暗底对照，并只读核对实际文件。未改项目、未生成PNG、未跑全测。

## 精确数据验证

三项均1024×1536；ownership为L、像素值仅0/255，source与derived为RGBA。

| 文件（相对`art/characters/sources/top04-adult-v2-west-worn-r001/`） | SHA256 |
|---|---|
| `masks/manual-idle-boundaries-r002.json` | `5b48b29f93ba32266861ebd6eea2259ff8e230e086c7186a62ec7051b6288182` |
| `masks/manual-idle-ownership-r002.png` | `93f1919ab124df67793718f7ca483e9cbf55316d941f45fa7e763983c639eba4` |
| `derived/visible-idle-garment-r002.png` | `8cb854aa904be5a1e95c3ea9f71e337697faaec98517c27703d00b49b29e801a` |

独立由原source与二值mask重建`Image.composite(source, zero RGBA, ownership)`，结果与derived逐RGBA完全一致。因此保留的软alpha/透明RGB没有二次相乘或重画，排除像素为(0,0,0,0)。

65条`pixel_exclusions`逐条检查记录的原RGBA、mask=0、derived=零RGBA，全部相符。15个keep/exclude witness全部与实际mask及expected/actual相符。

补充的颜色诊断只用于寻找疑点，不定义ownership：在已保留像素中按之前同一肤色辅助条件（alpha≥220、R>150、G>110、B>65、R>G+20、G>B+15）未找到候选；在衣摆范围寻找亮中性灰过渡（通道差<12、min>70、alpha≥220）也未找到候选。不能反向把“无阈值候选”当成所有边缘语义已经由颜色证明。

derived alpha≥16的像素为一个8连通主体（77574点），未见六帧r002那种孤立棕/黑残点。仍保留15个alpha<16的原source边缘像素，位于外轮廓附近；它们是未改源RGBA的低alpha边，不构成明显肤色或灰裤块，本次不建议为追求干净bbox全局清理/提高alpha阈值。

## 视觉结果

- **领口**：皮肤已排除，弧形黑领边与罗纹保留，没有新肤色片或整段黑线缺口。上左角与后颈共享黑描边仍保留源造型，本次没有发现会带入脸或颈部的明显残片。
- **近侧袖口**：收至原手腕上沿，罗纹及黑线连续，未把手掌/手外周带入；下沿略有原source栅格起伏，符合本次原像素保留，没有理由另行挪缩或重画。
- **远侧小袖片**：仅保留原图实际可见的狭窄红色/黑边范围，未虚填被躯干挡住的袖子，也没有手掌残块。
- **腰摆**：红色罗纹与下弧黑线连续，灰裤和向下延续的裤侧描边已切开。没有明显腰摆大缺口或灰裤碎片。

扁平source本身仍有抗锯齿、软alpha与共享边混色，不能把有限可见提取评审说成已恢复完整衣层的精确干净alpha。保留原source和当前边界/排除记录，后续prepared与严格配方沿现有验证链继续；实际动态适配须另验。
