# Whole-frame output envelope 独立只读复核

结论：当前修复后 PASS；Critical 0、未解决 Important 0、Minor 0。只读复核，没有修改共同engine/GDS/tests。此结论限本接口和下述探针，不等于新美术、24clip原生或脚步支撑/滑步验收。

## Important I1：非对象 clip 在可选字段检查前崩溃（已修）

原 `composition_contract.py:449` 在 `keys` 前执行 `'output_padding_px' in clip`；真实fixture置 `head.clips[0]=null`，实际抛 TypeError，证据 `/private/tmp/coastal-head-envelope-null-clip-probe.json`。GDS 原对应分支在 `exact` 前求 `head.has(...)`，null/String 可产生运行错误；这一项为静态确认，没有冒称已跑原生恶意fixture。

root 先补RED，后增加 Python dict require 与 GDS Dictionary 短路 guard。独立复测 null/String/int/list/bool 五类，全部 ValueError 拒绝；代码复读确认 GDS 在 `.has` 前短路。修复后无遗留 finding。

## 定点实际探针

脚本 `/private/tmp/coastal-head-envelope-independent-probes.py`；完整结果 `/private/tmp/coastal-head-envelope-independent-probes.json`。复用真实 shared mapper 的小PNG fixture，新增右下边界场景，没有重跑 root 已跑的5项 envelope test 或全suite。

- 实际 source near-hat 软alpha RGBA `[20,30,240,200]` 映射到原4×4画布的 `[4,4]`：无 envelope 拒绝；仅加right/bottom各1后，5×5输出该点逐RGBA保留，construct＋verify PASS；root不变。
- 把输出PNG也裁到匹配不足留边的尺寸并更新真实SHA，仍以 `crop owned component alpha support` 拒绝；不是仅靠旧PNG尺寸不符挡住。
- 同一合法 padded head 插入非空 coverage，明确以“actual alpha/layer order, not erase masks”拒绝，不能借envelope擦body。
- 原schema2 bare分支逐帧RGBA仍等于原schema1 base；原schema2 clip偷偷加入padding字段，以 unexpected/missing fields拒绝。

## 静态依赖与坐标检查

- `whole_frame_padding` 只加非负整数 `[L,T,R,B]`（每项≤512），canvas加总、root只加 `[L,T]`，display_scale不变。只在显式mapped-head clip进入；base schema3/schema1字段合同不放宽。
- `RegisteredAdaptations.component(output_padding)` 仍绑定 canonical source/target annotation、实际poses/variant/frame/SHA、source/bundle/owner和真实source重建。mapping的解剖anchor保持canonical，统一的 `[L,T]` 只在最终输出注册增加；每层实际owned非零alpha bbox必须完整落在新canvas，不能裁袖/帽/工具的可见支撑。
- 该分支仅hair/hat，且alpha-over、coverage/occlusion均null；composition仍使用已严格验证的base内存输出，整幅RGBA直接paste进透明envelope，不从head配方收第二份body，不重复软alpha。
- `review._scoped_action_clips` 只派生输出几何，base clip/source/target指针保持canonical；GDS先用原base geometry核真实template，再用派生geometry核每个PNG尺寸/哈希/RGBA和运行时root。
- 实际试玩和对照面板Sprite均 `centered=false`（`character_walk_trial.tscn`、`character_motion_review.tscn`）；显示路径使用 `-root_anchor_px`。像素 `p→p+[L,T]` 与根 `r→r+[L,T]` 后，`(p-r)*display_scale` 不变；左右/上下不对称留边不改变actor world位置。新头部层按同一pad输出，未见双重平移或只平移某一件的入口。
- 旧schema2严格clip keys拒绝新字段，未显式opt-in的render路径padding为None，原行为保持。

GDS原生24clip padded fixture06由root执行，本复核未重复运行或宣称其结果。GDS loader仍按既定职责核实际依赖闭包/当前engine/纹理字节与geometry；source reconstruction由Python verify/preflight负责，本报告不将仅加载PNG当source语义重建。

## 本次实际复核 SHA256

- build_contract.py `72737c246b6981708564b9a8aa511bace64bc0d269fd32857011ea8475b1d6d6`
- composition_contract.py `de39cef81da85c02421d0857297cb4e4e1960782927a122d449ca138a7e36848`
- review.py `f70ec75133a19215b8de709428c26bb5415895e8add626ef505cad1185128541`
- character_construction_samples.gd `1a762124204770b7aca17e8cd2578ceeeeaff1e0df65c22738f9ac86f8b9b42f`

独立探针JSON已持久保存为output-envelope-independent-probes.json；独立probe脚本仍在文中明确tmp路径，不称其永久归档。
