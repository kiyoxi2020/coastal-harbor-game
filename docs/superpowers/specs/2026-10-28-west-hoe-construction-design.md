# 西锄四头部状态统一构建小样设计

授权：用户已确认覆盖审计及后续小样实施包，本轮继续执行该范围。候选成年母版、top03、original-pants/original-shoes；hoe-west四pose+idle-west一pose，bare/hair/hat/hair_hat四固定状态。只产review-only。

## 方案与边界

采用同一coastal-character-construction-v1的schema2配方，显式引用严格base_recipe并重建其输出，继承模板/姿态/几何，只在已注册目标画布组合头层。schema1原配方/输出保留原语义。四固定状态分别一份配方与build，不建设运行时自由衣柜。

替代方案：将所有source衣装与target头部展开为通用DAG，范围较大且增加校验面；将现有成品帧复制为新身体输入，无法证明源/坐标/组合依赖。选用有界的父配方结果组合，所有依赖递归校验并绑定当前工具；禁止循环、嵌套组合、未知字段、缺失或过期来源。

实际头部操作保留旧语义：hair-only二值alpha>0范围RGBA替换；hat/hair_hat按far/body/(tucked hair)/near做alpha-over，最后在真实部件二值支撑内回贴body。多来源key2帽下发必须记录两个真实注册视图、各自来源/ownership和二值选择，并重算验证最终图；不能任意挑一源。

## 消费者稳定接口

build manifest继续使用现有coastal-character-review-build-v1/schema1与严格既有字段。recipe指向schema2配方；base_recipe字段为{file,sha256}，指向schema1严格配方。base_recipe中clips提供action/direction、canvas_px/root_anchor_px/display_scale和有序frames的pose/duration。schema2必须与父clip完全同范围/时序。

新review suite配置：kind=coastal-character-construction-review-v1，schema_version=1，resource_root=art/characters，scope=review-only，sample_id=hoe-west，states为bare/hair/hat/hair_hat四键，每项{manifest,sha256}；manifest为仓库根相对路径art/characters/builds/<id>/manifest.json。suite不声明已认可或生产release。

Godot在现有character_headwear_samples.gd中按kind分派专门的strict manifest loader，返回原样例结构，复用现有trial/状态切换/时间轴。loader验证suite与四manifest、recipe/head_state、base_recipe完全一致、inputs与engine当前SHA、输出路径/PNG尺寸/RGBA/hash和时序/geometry，失败清空、不回退旧样例。仅显示实际样例按钮，默认西锄；旧四组评审继续原格式。

review.py新增headwear-construction suite并在启动前Python verify四manifest所在构建，Godot作为显示/消费者验证；不把Godot加载成功当完整source重建证明。

## 文件责任

Python实施负责build.py/build_contract.py及可提取的组合合同helper、其新测试，保持check.py冻结基线不变。Godot实施负责新strict loader、headwear loader/trial分派、对应拒绝及实际加载测试、专用原生fixture。主代理生成四份配方、构建、suite、launcher接入、原生证据校验与归档、文档和交接。多人不同时修改同一文件。

## 验收

先失败测试后最小实现；未知/错state、缺状态、错pose/时长、错几何、局部挪缩、源与目标画布混淆、过期base/engine/input、缺多源ownership和错选择、纹理/manifest篡改均拒绝。构建20/20逐RGBA、姿态/时序/原生显示比例保持；所有新build verify，人物测试和check.py通过。独立审查当前工具/来源/时序/PNG证据覆盖，不能只绑定已通过布尔值。

新GPU证据：四state明暗背景五pose停帧、每状态10次面板循环、世界锄地四姿态及live评审状态切换不重置动作时钟、结束匹配idle。记录并绑定完整输入、输出PNG、工具与时序样本。主代理目视代表图和世界板。fixture信号/逻辑输入不宣称OS键鼠或WM焦点，未测试跨平台/导出；不登记新用户认可。

现有旧原生合同随dev代码改动会有受影响项，保留原证据，不刷新原回执；新证据只认证当前小样范围。原图、prompt、mask、冻结sample/catalog/acceptance/baseline全部保留，不重编码美术。未获要求不提交/推送。达到小样交付即停止。

## schema2字段定版

Root精确键：kind schema_version resource_root character_model_id recipe_id revision base_recipe head_state slots clips authoring_inputs。Clip精确键action_id direction frames；frame精确键pose_id operation layers layer_order，不允许重复duration/geometry覆盖父配方。bare操作none；hair为binary-rgba-replace；hat与hair_hat为supported-alpha-stack。层字段id slot texture registration provenance；registered-source-view与binary-source-selection两种有界来源表达，后者逐源绑定view/selection/source/source_bundle/source_ownership/source_ownership_space/registration。头部slots只声明该state实际hair/hat，不重复衣装槽。

西锄key2两现存selection ownership均为目标画布binary L、互不重叠；透明底上选择两已注册源view即可逐RGBA复现合并图。因此本轮无需补图或恢复旧posterior-view-selection.png。每个view绑定相应sample记录及extraction；未知字段、错pose、非零runtime变换、错selection或合并图不一致拒绝。详细实现字段和拒绝测试由组合合同代码与真实四配方提供唯一可执行定义。
