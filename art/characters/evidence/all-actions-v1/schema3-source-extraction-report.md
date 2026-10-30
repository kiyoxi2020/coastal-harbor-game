# T02追加：完整源归一与显式多源选择

已在同一 `RegisteredAdaptations` 实现whole-source NEAREST正有理数归一及显式binary RGBA来源选择。仅修改 `tools/characters/build_contract.py` 与 `tools/characters/tests/test_registered_adaptations.py`；未登记正式mask/配方、修改其他资源、刷新manifest/baseline、提交或推送。

原 `binary-rgba-extract-v1` 的字段和行为保持：只接受 `{kind,density_normalization:null}`，不由文件大小猜比例，不接受新增selection字段。新能力使用独立显式extraction kind/version；view/mapping、单源source/bundle、annotation/anchor接口均未改。

## 最终字段

view仍保存真实raw GPT PNG的 `source`、canonical `source_bundle`；`view.canvas_px/root_anchor_px`表示注册母版的**归一后源空间**，必须与source_pose annotation一致。source ownership对象仍为 `{role:source-ownership,mask}`；它的空间由新extraction明确声明。

```json
{
  "kind": "normalized-source-selection-v1",
  "schema_version": 1,
  "normalization": {
    "kind": "whole-source-rational-v1",
    "filter": "nearest",
    "numerator": 1,
    "denominator": 2,
    "raw_canvas_px": [1024, 1536],
    "raw_root_anchor_px": [512, 1416],
    "normalized_canvas_px": [512, 768],
    "normalized_root_anchor_px": [256, 708]
  },
  "ownership_space": "normalized-source-full-frame",
  "selection_space": "normalized-source-full-frame",
  "selections": [
    {
      "selection_id": "collar",
      "source": {"file": "sources/<id>/originals/collar-repair.png", "sha256": "..."},
      "source_bundle": {"file": "sources/<id>/source.json", "sha256": "..."},
      "source_pose": {"document": {"file": "templates/.../annotations/<revision>/poses.json", "sha256": "..."}, "record": "walk-south-zero"},
      "normalization": {"kind": "whole-source-rational-v1", "filter": "nearest", "numerator": 1, "denominator": 2, "raw_canvas_px": [1024, 1536], "raw_root_anchor_px": [512, 1416], "normalized_canvas_px": [512, 768], "normalized_root_anchor_px": [256, 708]},
      "selection": {"role": "source-selection", "mask": {"file": "parts/.../collar-selection.png", "sha256": "..."}}
    }
  ]
}
```

`selections:[]`表示只对完整主源归一。selection_id必须唯一；列表顺序就是明确的来源覆盖顺序，重叠处后项逐RGBA取代前项。每张额外源都有独立source/bundle/normalization，并且source_pose selector必须与主view完全相同，禁止混入另一个pose、另一注册记录或独立偏移。

所有这些对象按精确字段校验；新旧kind互不当作别名。新schema_version当前仅支持整数1。未知field、filter、空间、角色及local_scale/source_box/offset等字段拒绝。

## 三种空间与实际处理顺序

1. **raw完整源空间**：原PNG尺寸必须等于raw_canvas_px；其canonical source.json的source_id、精确asset file/SHA和实际PNG bytes均核验。新归一流程若bundle明确声明source_view_pose，也须与source annotation pose_id一致，不能出现相互矛盾的身份。
2. **normalized完整源空间**：numerator/denominator须为最简正有理数；两个方向的 `raw_canvas*numerator == normalized_canvas*denominator` 均须成立，不能非均匀缩放。raw_root同样须按比例精确映射到annotation绑定的normalized root。只对**整张**原图作一次Pillow NEAREST resize，不裁片、不局部缩放、不凭图片大小自动推比例。额外完整源同样独立验证后归一到完全相同的canvas/root。
3. 在normalized完整源空间，selection mask必须是同画布binary L，role必须为source-selection。先按列表二值选择完整源RGBA，然后用独立的source_ownership二值提取。selection不是coverage、occlusion或alpha混合；原alpha73、51等软边数值逐字节保留。
4. **target pose空间**：沿现有source/target annotations同名锚之差作整源整数注册；只允许丢出透明padding，owned真实alpha>0支撑不可越界。target coverage和ordered foreground occlusion仍走现有不同角色与空间的检查，然后逐RGBA核对注册texture。

归一/来源选择的参数在adaption文件内，由其file/SHA绑定；每张raw、每个bundle、每张selection/ownership、annotation/pose/reference frame和texture均进入实际依赖闭包。改额外raw源或mask会使已有build verify失败；连同文件重新哈希也不能让旧texture通过source重建。

## 同一mapper的复用入口

公开主入口保持 `RegisteredAdaptations.component(layer,clip,frame)`；头部新合同仍可复用，不需要复制mapper。

新增内部可复用阶段：

- `source_png(source,source_bundle,canvas,pose_id=None)`：绑定实际完整PNG及canonical bundle/assets；可选pose一致性检查。
- `normalized_source(source,source_bundle,normalization,canvas,root,pose_id)`：核显式整数比例、原/归一canvas/root及全源NEAREST，返回归一后的完整RGBA。
- `source_pixels(view,annotation)`：沿已由构造器检查的新旧extraction生成完整的normalized/selected源RGBA，未做source ownership和target注册。

消费者应调用component，或只在view/extraction和annotation均已验证后复用这些分阶段方法；不能以裸dict调用分阶段方法来跳过顶层kind/space/role/identity检查。`reference(ref,namespace=None,image_size=None)` 与 `record(ref,namespace=None)` 回调及其SHA/safe_file/依赖登记要求不变。component自身验证额外源bundle，不依靠外部base层循环补校验。

## 真实r003+r004复算

新增真实资源测试 `test_real_collar_sources_reconstruct_only_reviewed_visible_surface`：

- 从 `sources/gpt-top03-walk-south-0-v1/` 读取保留的complete-shirt、collar-repair raw PNG及真实bundle；读取canonical walk-south B_4 pose/action/完整frame与geometry。
- 将这些真实文件复制到隔离 `/private/tmp/coastal-build-*` fixture；临时annotation绑定真实canonical pose/ref SHA，临时selection取持久化review JSON中的人工polygon。没有往仓库写mask、配方或新登记。
- 两完整源1024×1536统一1/2归一，按真实领口polygon二值选源，再经同一component重建已知有限表面texture；36测试中该测试实际执行，无mock verifier。
- 既有30655个高置信可见布料点均仍有alpha≥200的真实选入源材；source、额外source、bundle、selection、ownership、annotation、canonical poses及实际B_4 frame均被检查进入依赖。

该fixture中的visible-surface probe是已有实测范围的诊断，不是正式source ownership或完整B衣层登记。139个隐藏侧边缺口仍保留，本次没有补画/补色或假称归一/合同能恢复不存在的像素。整源光晕仍须人工语义ownership排除；NEAREST/哈希通过不证明布料归属、投影、动态或原生屏幕效果。

## RED / GREEN

新增小图测试先RED：初轮33测试（原24＋新9），因未知新extraction字段失败，记录 `/private/tmp/coastal-schema3-extraction-red.log`。之后补“额外bundle声称另一source pose却通过”的独立RED，记录 `/private/tmp/coastal-schema3-extraction-pose-red.log`，再实现一致性检查。

最终结果：

- registered适配36测试通过，含完整4×4→2×2全源归一、2×2/4×4真实construct/verify、软alpha原值、多额外源重叠顺序、source/bundle/mask/annotation闭包、错误比例/root/空间/filter/角色/unknown fields、变更raw/selection后重哈希仍不能伪造texture，以及真实r003+r004复算。
- 原build_contract 32测试通过。
- 原composition_contract 30测试通过（既有20张西锄RGBA回归仍通过）。
- 指定两文件 `git diff --check`通过。

GREEN日志：`/private/tmp/coastal-schema3-extraction-green.log`、`coastal-schema3-extraction-build-regression.log`、`coastal-schema3-extraction-composition-regression.log`。未重建旧四manifest，未运行此中间态check.py；主代理待共同engine冻结后负责当前构建迁移、完整人物检查及新原生验收。

## 当前边界

只支持全部完整源先归一到同一source_pose记录及完整canvas/root后作binary选择；不支持来源间任意局部变换、不同source pose强拼、任意crop、其他resampling filter或隐含密度。列表二值来源选择不等于自由绘制/抹图工具。view/mapping的已绑定整数target注册及mask角色仍严格执行。没有新生产release、实际动作能力登记或用户认可。

## 冻结独立复查修复：I1 / M1 / M2

已读 `/private/tmp/coastal-all-actions-core-review-01/review.md`，据真实探针补RED，再修代码；没有忽略finding或改主代理mapped-head测试。此节是当前有效边界，替代早期报告对二值occlusion前景支撑的较宽表述。

### I1：二值occlusion只可落在alpha255前景

RED测试在同一真实fixture把canonical body参考及实际texture的(0,0)改为alpha1、128、254，同步全部frame/SHA/annotation。旧代码均错误接受该点的二值occlusion并清掉底层top。

修复把“alpha>0前景支撑”收紧为“实际alpha==255的不透明前景支撑”。occlusion mask若碰到任何只由半透明前景支撑的位置，明确ValueError拒绝；这类边缘须保留完整底层，并由真实layer_order做alpha-over。未改变源alpha，也不把254阈值抬成255来通过门禁。

新正例取消该点二值occlusion、恢复完整top、保持 `top → body` 顺序，实际construct/verify输出：

```text
top pixel  = (200,30,40,128)
body pixel = (10,20,30,128)
output     = (73,23,33,192)
```

alpha1及254同样与完整图层的Pillow alpha-composite参考逐点一致。原alpha255 occlusion正例仍通过；无真实foreground支撑的mask仍拒绝。

### M1：新mapper坏类型稳定ValueError

先观察 `assets=[null]` 的AttributeError及unhashable view/mapping/variant/foreground的TypeError，再在遍历、membership、set之前收紧新输入类型门禁：

- canonical source bundle必须是对象，assets必须是对象列表；公开component和schema3完整validate均稳定拒绝null资产。
- view_binding的view_id/mapping_id、mapping.view_id先验证identifier；不会以list作dict key。
- annotation.variant先验证字符串和实际variants字典；canonical action/direction也先验证字符串。
- foreground_layers须为字符串列表后才检查唯一性与层序，`[[]]`不会冒出set异常；未知component slot也明确合同拒绝。

未用笼统 `except Exception` 掩盖实现错误，也未放宽角色/identity约束；schema1/2旧分支的字段解释没有改成schema3。

### M2：当前source布局/asset格式的明确限制

目前支持并已验证的raw输入布局为 `sources/<source_id>/<subdir>/<file>`（当前实际新增源都在 `originals/`），bundle按源路径的 `parents[1]/source.json` 推导，source_id须匹配。assets仅认迁移形式的 `new_path:art/characters/...` 与 `new_sha256`。

**不宣称已支持** `sources/<id>/source.png` 直接放源图并配同层source.json，或native `assets:[{file,sha256}]` 形式；库里存在这样的静态源不代表本合同能直接切atlas/适配。本轮未为它们追加别名/格式兼容，也未为增加“源包数”制造来源。若后续确有用途，应沿真实原图/原prompt/原SHA做明确的版本化source准入；派生归一/预合成PNG仍不能冒称GPT原始源。

M3全包preflight正例由主代理负责，不在本责任两文件中修改。

### 修复验证

修复前：`coastal-schema3-review-fixes-red.log`，40测试出现3 failure/5 error（包含subtests），覆盖I1和M1真实错误。修复后：适配40测试全部通过，保留 `coastal-schema3-review-fixes-green.log`。

最终冻结代码合并覆测：

```text
PYTHONPATH=tools/characters/tests:tools/characters python3 -m unittest \
  test_registered_adaptations test_build_contract test_composition_contract
Ran 102 tests in 19.711s — OK
```

包含适配40＋原build32＋原composition30；日志 `/private/tmp/coastal-schema3-review-fixes-final.log`。指定两文件diff检查通过。未更新旧manifest或baseline；主代理后续复审/完整门禁/原生检查仍须按实际snapshot执行。

## 完整源有理数归一＋透明padding：新显式kind

新增normalization kind `whole-source-rational-pad-v1`，沿同一 `RegisteredAdaptations.normalized_source()` 使用；外层extraction及view/mapping接口不改。旧 `whole-source-rational-v1`仍要求两个方向画布按比例全整除，且不接受offset字段，未把旧kind悄悄改成ceil/填行。

新kind的精确字段是旧normalization字段加 `whole_frame_offset_px`：

```json
{
  "kind": "whole-source-rational-pad-v1",
  "filter": "nearest",
  "numerator": 256,
  "denominator": 187,
  "raw_canvas_px": [1122, 1402],
  "raw_root_anchor_px": [561, 1168.75],
  "normalized_canvas_px": [1536, 1920],
  "normalized_root_anchor_px": [768, 1600],
  "whole_frame_offset_px": [0, 0]
}
```

规则：

- numerator/denominator仍须是最简正有理数；显式原PNG尺寸/SHA/bundle及source_pose annotation绑定不变。
- 两轴使用**同一个**逆比例 `denominator/numerator` 作NEAREST affine采样，不再按输出宽/高各自resize。仿射系数为 `[d/n,0,-offset_x*d/n,0,d/n,-offset_y*d/n]`；采样超出原图域时填RGBA透明。
- scaled extent逐轴用精确整数ceil算 `ceil(raw*n/d)`；offset必须是非负整数，完整extent＋offset必须放得进normalized canvas。这里不只检查alpha bbox，连原图完整空间也不得被归一阶段裁掉。
- root用 `Fraction(str(JSON有限数值))` 做精确有理计算，强制 `raw_root*n/d+offset == annotation绑定的normalized_root`。不增加视觉epsilon，也不允许随意挪root补错位。已有1168.75恰为4675/4，映射精确为1600。
- offset作用于整张完整源，仅允许统一画布padding；不是hair/衣鞋的局部offset/scale。后续层的offset仍零、local_scale仍一；target registration仍由已绑定锚决定。

实际under-hat尺寸算例：1122×1402按256/187统一缩放，scaled extent为ceil=[1536,1920]。测试中的稀疏完整源尾点在输出[1535,1918]保留alpha7，末行1919为透明；没有用非均匀resize拉满最后一行。此探针使用真实需求的尺寸/root与**合成稀疏像素**，不冒称已注册或验证实际under-hat美术。人物body不会从该图或该测试输出取源。

### 此扩展RED / GREEN及最终冻结

先新增5项小图/入口测试：odd 3×5按8/7统一affine得4×6，独立有理像素中心采样参考逐RGBA一致、明确不同于直接resize4×6；alpha7尾部保留、额外采样区透明；整源整数offset连同root合法；错误root/比例/offset及容纳不足的canvas拒绝；新kind经真实construct/verify重建，旧kind带offset仍拒绝；1122×1402算例及1e-9 root改动拒绝。

RED日志 `/private/tmp/coastal-schema3-rational-pad-red.log`：45测试，因未支持新kind/offset而1 failure、4 error。另补normalization.kind=[]的M1同类RED，确认稳定ValueError类型门禁后修复，日志 `coastal-schema3-rational-pad-kind-red.log`。

适配45测试GREEN，日志 `/private/tmp/coastal-schema3-rational-pad-green.log`。最终合并覆测107测试全部通过（20.564s），含适配45＋原build32＋原composition30，日志 `/private/tmp/coastal-schema3-rational-pad-final.log`；指定两文件diff检查通过。未改其他文件、M2输入格式、正式mask/配方、旧manifest或baseline。本轮后这两文件冻结，交主代理统一引擎复审与旧四build迁移。

## 真实source atlas：四空间与测量锚注册

新增显式 `extraction.kind=registered-source-atlas-v1/schema_version=1`。旧binary、normalized-selection、整除/透明padding normalizer的已有字段及运算解释保持，不把atlas画布强装成canonical完整人物画布。

```json
{
  "kind": "registered-source-atlas-v1",
  "schema_version": 1,
  "atlas_canvas_px": [3072, 1536],
  "normalization": {
    "kind": "whole-source-rational-pad-v1",
    "filter": "nearest",
    "numerator": 1536,
    "denominator": 887,
    "raw_canvas_px": [1774, 887],
    "raw_origin_px": [0, 0],
    "normalized_canvas_px": [3072, 1536],
    "normalized_origin_px": [0, 0],
    "whole_frame_offset_px": [0, 0]
  },
  "atlas_ownership": {
    "role": "source-atlas-ownership",
    "coordinate_space": "normalized-source-atlas",
    "mask": {"file": "parts/.../complete-atlas-ownership.png", "sha256": "..."}
  },
  "registration": {
    "kind": "atlas-to-source-pose-anchor-v1",
    "atlas_anchor_px": [142, 1304],
    "pose_anchor_name": "left-ear-edge",
    "pose_anchor_px": [533, 729]
  }
}
```

`normalization`只接受对应整除或pad kind的精确字段；atlas使用 `raw_origin_px/normalized_origin_px`，两者均须为整数[0,0]，**不是actor foot root**。调用同一个normalizer时仅在内存中适配其0→0参考点，没有保存假的world root，未复制另一份缩放器。pad的offset也必须满足这个0→0条件；未知actor-root字段或任意origin偏移拒绝。

四空间的顺序：

1. **raw原图**：view.source仍是真实完整1774×887 GPT atlas及canonical bundle，不能换成已烘焙registered帽PNG。完整源按显式全图有理数归一，原图和参数都留在依赖中。
2. **normalized atlas**：3072×1536独立atlas坐标；atlas ownership必须为同画布binary L。例中768²真实局部mask嵌入[0,768]，从完整atlas只选该帽源像素，不在运行合同里使用局部crop PNG冒充原图。
3. **canonical source pose**：registration的pose_anchor_name/px必须等于source_pose annotation真实landmark。atlas_anchor是绑定raw/mask/normalization的版本化人工测量声明；按差值[391,-575]整体放入canonical1536×1920。此时检查**所有atlas-owned alpha>0支撑**完整留在canonical画布，不能依赖后面的near/far mask把越界丢失掩盖掉。view.canvas/root仍为真实canonical frame的[1536,1920]/[768,1600]，与atlas几何不混写。
4. **target pose**：view.source_ownership在上述canonical-source空间选择whole/near/far，再沿原mapping的source/target annotation锚做一次正常注册。没有部件local_scale/任意offset，软alpha未重复相乘。

新实现阶段 `RegisteredAdaptations.atlas_source(view,annotation)`供source_pixels调度，source_pixels/component公开接线不变。source atlas可含多个pose；若raw bundle另外明确声明单一source_view_pose，不得与所选source annotation矛盾。多view atlas不应填一个假的单pose全局声明。

### 实际南帽复算

与headwear来源代理确认真实原图、bundle、768²mask、旧测量记录及canonical reference。新增真实回归读取：

- raw：`sources/motion-headwear-sampling-v1-9f06fab9/originals/headwear-sheet-attempt1-b71b3574.png`，1774×887，真实SHA与原bundle绑定。
- owner：原 `water_south_B_ready` 768² hat source ownership；测试内嵌入完整3072×1536 atlas，不修改正式mask。
- 原cell pivot[142,536]＋cell origin[0,768]得到真实atlas anchor[142,1304]；canonical left-ear anchor[533,729]，delta=[391,-575]。
- source_pose始终 `water_south_B_ready`、variant B；真实canonical frame及SHA、canvas/root/scale进入临时annotation。

通过同一个component从raw完整atlas重建，与旧1536×1920registered hat PNG逐RGBA一致；旧PNG仅作为待复核texture，未用作raw源。将atlas anchor改1px、保持旧registered texture时实际拒绝reconstruction mismatch。raw/bundle/完整atlas mask/canonical mask/pose/frame/annotation均真实加入依赖。

该回归在隔离 `/private/tmp/coastal-*` fixture完成，没有登记新正式资源或配方。RGBA重算只证明输入和规则能复现该有限结果，**不自动证明测量锚语义正确，不继承旧native/user认可，也不代表全动作帽源齐备**。语义/动态仍按实际measurement和visual证据验收。

## schema3 body：固定完整同pose参考

新增明确约束：schema3 `body.texture`须与所选canonical variant frame.file/SHA解码后的完整frame逐RGBA相同；canonical frame也成为真实input。允许body namespace内不同路径/不同PNG编码但RGBA相同的alias，拒绝换成同尺寸另一身体后仅重哈希。每frame恰好一个完整canonical body层，防止重复叠脸软边。

此版same-pose-reference不支持partial foreground、隐藏身体或任意body生成。现行西锄r002的shared_same_pose_foreground_and_contour是schema1，原解释不变；未来schema3需要分身体表面时必须另建显式接口，不能沿此名称自动放行。under-hat/atlas生成图不会作为body像素输入。

RED先观察“另一body PNG＋正确新SHA仍被接受”以及body-only alias使canonical frame未入依赖；实现后不同像素拒绝，同RGBA但不同PNG bytes的alias真实construct/verify通过。另观察同一canonical body复制两层被接受，再加恰一层约束；未改schema1/2。

## 声明source pose与独立hair compatibility引用

修复独立复审指出的single-source分支遗漏：`binary-rgba-extract-v1`同样把annotation.pose_id交给source_png，不能在所有SHA同步更新后接受bundle.source_view_pose与source annotation冲突。atlas也不会用另一extraction kind绕过一个明确相反的bundle单pose声明。

hair view新增**可选** `compatibility:{file,sha256}`：仅slot=hair允许，其他slot同字段仍严格拒绝。选用该view时component按该hair design的adaptation namespace执行真实reference/SHA/依赖登记；不解析record内容或复制composition parser。旧不含字段的基础schema3 view继续可用。

新head消费者由主代理要求并核独立record：`kind=coastal-head-compatibility-v1/schema1/hair_identity_sha256/hat_identity_sha256`，两个intrinsic source identity排除claim本身，避免同PNG atlas/单bundle出现hash环。raw source.json不再被核心擅自当当前head兼容claim权威。核心的optional-reference测试只验证真实闭包/namespace/坏引用拒绝，不把未解析内容当已通过head兼容。

### 此最终子包验证

- `/private/tmp/coastal-schema3-atlas-body-red.log`：四格atlas未支持、不同body错误通过、alias丢canonical依赖等真实RED；52测试时13 failure/1 error（含subtests）。
- `/private/tmp/coastal-schema3-pose-compat-red.log`：binary pose声明错误通过及hair字段尚不支持的RED。
- `/private/tmp/coastal-schema3-atlas-pose-red.log`：atlas不应绕过明确相反的bundle pose声明的RED。
- `/private/tmp/coastal-schema3-body-duplicate-red.log`：重复完整body未拒绝的RED。
- 最终适配59测试GREEN：四格atlas仅选真实owned单元、signed锚注册、softalpha不重复、错空间/role/锚/裁owned/假root拒绝；真实南帽raw复算；canonical完整body和alias；hair compatibility独立ref闭包/namespace；所有原归一、选择、I1/M1检查仍通过。日志 `coastal-schema3-atlas-final-green.log`。

最终合并覆测121测试全部通过（38.456s），含适配59＋原build32＋原composition30，日志 `/private/tmp/coastal-schema3-atlas-final-regression.log`。主代理维护的mapped-head/全包preflight/Godot测试未在此子包修改；M2源包格式保持原边界。未刷新旧manifest、baseline或提交。本包完成后两责任文件冻结，交原独立核心reviewer和主代理集成。
