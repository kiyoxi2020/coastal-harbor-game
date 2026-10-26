# 24组原生证据：采集前快照与采集后门禁

2026-10-26。完成evidence_contract.py、test_evidence_contract.py与本说明。执行模型gpt-6.1-sol/high；未创建子代理、未提交。没有改美术、Godot、旧farming-transitions-v1工具或历史报告，未运行Godot。

## 命令接口

所有24组、catalog和最终原生测试脚本就绪后，**先快照，再启动采集**：

```sh
python3 art/design/character-motion/adult-standard-v1/farming-four-directions-v1/evidence_contract.py snapshot \
  --catalog art/design/character-motion/adult-standard-v1/farming-four-directions-v1/catalog.json \
  --native-script godot2d/tests/test_character_farming_24_native.gd \
  --output /private/tmp/coastal-farming24-native/input-contract.json
```

catalog与native-script接受仓库相对路径，或仓库内的绝对路径；目录由工具所在位置确定。示例catalog路径以主代理最终实际文件为准。快照工具会两次核对引用闭包，使用真实UTC记录snapshot_started_utc、snapshot_utc，明确capture_phase=before_native_capture与run_diagnostics_enabled=true。保存前完整验证通过才创建快照；已有输出一律拒绝覆盖，避免采集后悄悄重绑输入。

原生脚本在运行开始时加载这份input-contract.json，记录其**完整文件字节SHA-256**，写入原report顶层字段`input_contract_sha256`。采集结束关闭report后执行：

```sh
python3 art/design/character-motion/adult-standard-v1/farming-four-directions-v1/evidence_contract.py validate \
  --contract /private/tmp/coastal-farming24-native/input-contract.json \
  --native-report /private/tmp/coastal-farming24-native/report.json \
  --receipt /private/tmp/coastal-farming24-native/input-validation.json
```

归档必须同时满足进程退出0、最新回执input_hashes_current=true、archive_allowed=true，不能复用旧回执。原report还须保留started_utc/finished_utc；工具校验snapshot≤开始≤结束≤验证。Godot的Time.get_datetime_string_from_system(true)输出无后缀UTC秒字符串，按已声明UTC解析，以1秒原生时钟精度比较并在回执记录capture_clock_precision_seconds=1。快照自身保留真实微秒UTC，不假称能判定同一秒内的严格先后。回执绑定原report SHA与input-contract SHA，要求report的input_contract_sha256吻合、checks是非空且全true的布尔字典，并要求started_utc/finished_utc满足采集前后时序；原report不被改写。

`validate --contract <file>`也可单独检查依赖；默认回执为快照同目录input-validation.json。未给原report时，依赖可通过，但archive_allowed=false，因为尚未建立报告绑定。失败返回非0并将最新回执设为input_hashes_current=false/archive_allowed=false，不留旧true。回执禁止覆盖快照或原报告。

同一输入复测可沿用原先已在采集前建立的快照；输入或原生脚本/证据工具改变时，旧快照会失效，须为新的采集建立新目录快照。不能改旧快照哈希来维持旧报告通过。

## 覆盖范围

快照声明的是**保守静态可达/manifest依赖超集**，不是实际运行加载文件列表。只沿引用，不枚举仓库、不读.godot缓存：

- schema2 catalog必须恰好包含water/hoe/harvest × 四向 × A/B的24个唯一键，不能仅靠数量或默认方向推断。每个候选的schema/身份/密度/画布/根点、全部inputs及实际SHA、所有frames/file/hash/source/source_sha绑定都核对；检查实际PNG画布、正时长、四阶段完整且顺序合法、至少4个不同纹理。帧数可超过4。
- locomotion导出清单的source_root/inputs/source_contract，以及各recipe实际烘焙纹理；源合同与inputs互相一致。
- run candidate全部inputs/frames及walk_artifact_digest关联；run-garments的inputs/recipe实际纹理及candidate关联；run-diagnostics的inputs/实际记录纹理、candidate与garments关联。按本轮真实配置启用diagnostics，并要求最终run能力覆盖四向A/B完整集合。
- 显式必需角色集合包含catalog、locomotion manifest、run candidate/garments/diagnostics、trial场景、world场景、camera、project.godot、调用者指定原生脚本与本工具自身，共11类。角色集合、依赖集合、24键和逐帧索引都在后验验证中重新推导，不能删掉world/相机再重算摘要来绕过。
- 从trial/world/camera/project/原生脚本递归读取完整res://静态字面引用，包括继承测试脚本带入的未执行分支。外部场景、脚本、素材/字体等按实际文件SHA绑定；目录及格式化路径片段另列，locomotion/run/catalog通过显式清单解析补足。

工具自身也在输入集合内；原生采集后改工具会使原快照失效。脚本不修改源/清单/图像，只写新快照和回执。快照含自身内容摘要用于检查结构篡改；原生report绑定的仍是**整个快照文件SHA**，两者用途不同。

## RED → GREEN验证

```sh
python3 art/design/character-motion/adult-standard-v1/farming-four-directions-v1/test_evidence_contract.py
```

先写测试：工具缺失时1项明确FAIL、17项跳过。初次实现暴露两个实际失败：缺candidate哈希未拒绝、缺frame哈希导致KeyError；原因是共用登记函数把None同时当作“静态引用没有声明要求”和“清单漏哈希”。改用独立哨兵区分后18项通过。再用畸形原报告复现旧通过回执残留风险，补对象类型检查与失败回执处理；增加真实CLI覆盖；收到原生UTC字段合同后，再先失败复现缺时间/倒序仍放行，补时序门禁，最终**21项全部通过**。

覆盖完整24键成功、缺键/重复键、缺阶段、缺candidate/纹理/source哈希、缺world/diagnostics、改变实际idle/run/camera/工具、遗漏角色/依赖/24键集合、错误report快照绑定、畸形report、缺原生时间/采集早于快照/结束早于开始、Godot无后缀UTC秒格式、失败清旧回执、成功双重绑定。CLI测试覆盖绝对catalog/相对native参数、拒绝覆盖快照、原report绑定、实际相机改动后的非0及false回执。

所有构造和变更仅在/private/tmp/coastal-farming24-contract-*夹具。夹具使用标准库生成极小有效PNG与完整24组合，检查结构/哈希/门禁逻辑，不把夹具当真实美术或原生采集。没有改真实认可素材。

## 当前状态与限制

本子任务交付API与工具，**未为尚在集成中的真实24组创建快照**；主代理待全部资源/原生脚本冻结后调用真实snapshot，并执行原生采集与post validate。21项fixture通过不等于真实目录门禁已过，更不等于原生动作/脚点/握点/用户认可。

这是预先关联与后验当前字节一致性检查，不是运行时文件访问跟踪；不能证明两次观察之间从未发生临时编辑。动态或仅UID的无路径资源并非完整运行追踪能力。引擎二进制、导入缓存、OS、显示服务不在快照内；这些限制不被隐去。源哈希只验证实际引用文件，没有把历史失败稿或完整穿衣图提升为好图/独立可组合。
