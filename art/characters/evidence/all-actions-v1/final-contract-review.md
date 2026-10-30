# 最终核心与registered-head组合定点复查

**PASS（本次合同范围）。未发现新增Critical/Important。** 之前N1/N2均已修到根因，atlas/body门禁与同一mapper组合接线成立。此结论不是全动作美术、Godot消费者、原生连续播放或生产发布通过。

## 复核版本

- `tools/characters/build_contract.py`：`b85cc7806f013a536742ca2367cb0e85259270137e357802996f4a1ff47bc747`，与主代理冻结值一致；检查结束仍一致。
- `tools/characters/composition_contract.py`：`c514c82108427811291aac1d04336863b87f9adb4b782c1a3cc75f158e6c117f`，检查结束仍一致。
- `test_registered_adaptations.py`：`2c8965f2b790ba8d71216c4f92009af9f8945a9e6e805c2e31662b26ac25e822`。
- `test_registered_headwear.py`：`8267dc040ddfc1ab6edc291c6c6e427aa8e730da9cc5cde88190725709ba59c1`。

只读检查，未改共享代码、正式资源、配方或baseline；测试使用隔离/private/tmp fixture并清理。

## 旧finding闭环

### N1：显式source pose冲突

`source_pixels():307–310`的binary分支已传入实际source annotation.pose_id；atlas通过同一个normalized_source/source_png也带该pose_id。source bundle若明确声明单一source_view_pose，与所选源pose冲突将稳定ValueError。未声明单pose的真实多view atlas仍可按显式view/ownership记录使用，没有把source_pose改名成target motion。

独立执行binary冲突拒绝和atlas冲突拒绝两个定点测试，均通过；并非只改normalized路径。

### N2：共享source bundle的SHA环

`component_source_identity()`只含under-hat实际source/bundle/source_pose/geometry/ownership/extraction，排除兼容声明自身。独立typed `coastal-head-compatibility-v1`记录放在hair adaptation namespace，以真实file/SHA加入依赖，同时绑定hair和hat两侧intrinsic identity。raw source.json无需写回配对claim。

这解除了“共享bundle SHA包含claim、claim又包含该bundle SHA”的结构循环，没有靠忽略bundle、删额外源、复制原图或伪造第二source身份绕过。新增同一PNG atlas＋同一bundle同时供hair/hat的正例通过；本次额外将该正例推进到真实construct/verify，4个输出通过，typed claim与共享bundle均在实际inputs闭包。再改claim文件而不改旧build，verify因其SHA变化拒绝。

额外探针修改实际under-hat原PNG，更新raw/bundle/texture/adaptation全部SHA但保留旧typed claim，validate明确拒绝 `Under-hat source identity differs`。因此新record不仅绑定帽，也没有让旧hair兼容声明套到另一实际选入源。

## Atlas风险核对

- raw完整GPT PNG、canonical bundle、normalization、full-atlas binary ownership、人工版本化atlas anchor及canonical source annotation都进入真实依赖；registered PNG仍是待重建输出，不是冒称raw源。
- raw/normalized atlas使用零image origin；没有假造actor foot root。view仍保留真实canonical pose canvas/root，与atlas几何区分。
- 沿同一normalizer做统一NEAREST有理数采样；atlas-to-canonical是一次整数整源注册。其后才应用canonical-source的whole/near/far ownership与普通source→target锚注册。
- atlas-owned全部alpha>0支撑先受完整留存检查，不能让后面的view mask隐藏被裁掉的真实源像素。定点“即使末级mask会遮住也不可crop”反例通过。
- **真实南帽**原1774×887 atlas、既有768²ownership嵌入3072×1536、[142,1304]→[533,729]注册通过同一component实际重建；与旧真实帽逐RGBA一致，原图/bundle/mask/canonical pose/frame均入依赖。该真实定点测试本次独立通过。
- 人工atlas锚/ownership的解剖语义并未自动认证，仍需对应源图与视觉证据；合同没有把此限制隐藏成发布批准。

## Body风险核对

schema3恰好一个完整canonical body。实际body texture与所选canonical variant/frame解码后逐RGBA相同；canonical file/SHA本身也是input。不同PNG编码但RGBA相同的body namespace alias可通过，换成同尺寸另一身体后重哈希、或重复叠一遍完整body都拒绝。

本次分别执行“换身体拒绝”“重复身体拒绝”“RGBA alias真实construct/verify且canonical进入依赖”三个定点测试，均通过。此门禁固定的是完整同pose参考；它不声称提供隐藏身体或partial foreground。后续若需要这类接口必须显式扩合同，不能借same-pose-reference名称混入新脸手。

## 组合与兼容依赖

- registered-head继续直接调用同一RegisteredAdaptations.component；base真实validate为schema3，geometry/时序/pose来自已验证base，不接独立任意base PNG。
- near/far真实存在时保持严格far/base/under/near，同一完整帽源及target注册；near-only则base/under/near，near ownership必须重建整帽whole ownership，不制造空far。
- 旧I1仍以实际foreground alpha==255限定binary occlusion；mapped-head本身禁止coverage/occlusion擦图，交原compose的真实alpha与层序执行。
- hat identity保留实际帽source/bundle/source_pose/geometry、全部extraction（含额外source/norm/selection）及whole/near/far ownership指纹。hair intrinsic identity同样覆盖实际选入源与ownership。两者均排除target motion anchors，允许同一真实兼容视图映射多target。
- 独立compatibility ref既受hair namespace/SHA约束，也受typed kind/schema及双方identity校验；不是不解析的布尔批准。core只登记optional ref，组合消费者解析其语义，职责清楚。
- 原“增加额外cap源仍沿用旧兼容claim”反例本次定点仍拒绝；旧schema1/2路径未被此新协议冒名替换。

## 本次验证

选择性执行11项，不重跑完整121或全部已GREEN套件：

```text
binary/atlas显式source pose冲突拒绝
atlas-owned像素不得靠末级mask掩盖crop
真实南帽raw atlas逐RGBA重建
schema3另一身体拒绝、重复body拒绝、canonical RGBA alias construct/verify
hair compatibility ref真实依赖登记/变更失效
共享atlas hair/hat正例
registered hair_hat真实build/verify
新增cap源使旧compat失效
Ran 11 tests in 2.486s — OK
```

另有两组新增探针（不写测试代码）：

1. 改under-hat原图并同步所有像素/SHA，旧typed claim拒绝。
2. 共享atlas正例额外真实construct/verify通过；typed claim与shared bundle在闭包；改claim后旧build verify拒绝。

没有执行Godot/native/全包实际美术采集，也未把这些代码与小图结果扩成24格资源完成或用户认可。
