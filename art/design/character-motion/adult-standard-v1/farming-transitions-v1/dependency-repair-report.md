# 原生证据依赖归因补充

2026-10-26。仅补本目录证据；原生测试脚本、Godot运行代码、原report.json/checks.json、原始采集与录像均未更改，也未重跑Godot。执行模型gpt-6.1-sol/high；没有子代理。

## 修复内容

新增[依赖契约](evidence/native/dependency-contract.json)与[生成/验证工具](dependency_contract.py)，修复旧原生报告仅登记5个输入与3农事candidate、未覆盖走跑/站立及世界相机配置的P2。契约明确标为post_run_supplement_not_runtime_sampling；这是采集后补充来源关联，不把新字段伪装成原测试运行时采样，也不扩大原78项原生检查结论。

契约SHA-256：`317bda96da1cacfa0860222b287503f22211380f6c08376d5bf7a60fe419c5d9`。

原report SHA-256仍为`a359922a4abfcc7cd7546842d27373504c1c703c1085522af22d7bdb9536e223`，checks仍为`03416aad8850e446a2cb4aea6c522d303ba12c6093a79fcb8d1210a6d0275af8`。原报告登记的测试脚本和其他输入均重新核对实际哈希，未替换其绑定。

补充集合共1140文件，是**保守静态可达/manifest依赖超集**，不是运行实际加载列表：

- 显式校验locomotion-v1/baked/export-manifest.json的inputs/source_contract，以及A/B实际20帧纹理；run candidate的inputs和16帧纹理、walk_artifact_digest关联，以及run-garments.json的candidate哈希、inputs和所有声明配方纹理。
- 保留原生report/checks/原采集脚本绑定，重新校验既有农事catalog、3个candidate及其输入/实际纹理。
- 从实际trial.tscn、原生测试脚本和project.godot出发递归解析可达tscn/tres/gd/配置/JSON的完整res://静态字面路径，包含world、camera、外部场景、脚本、字体、素材与项目设置；不扫描仓库或读取.godot缓存。继承测试脚本和项目主场景的未执行分支也可能贡献资源，保留为保守超集，未为缩小集合重构。
- 9项目录/动态路径片段单独列明，不当作已解析文件。locomotion/run目录片段由明确清单补足；此工具不是运行时文件访问跟踪器。

本次native run没有启用diagnostics；原生测试设置run root并使用正常run-garments。用户启动器是另一次调用，可能启用diagnostics，不继承本契约的采集结论。

## 时间与历史依据

baseline和补充时HEAD均为`f6d9e20678d2280198e92801332df41f05b0d958`。主代理声明本任务初始git干净，遗漏依赖在初始到采集后均未改；契约明确将其标作会话来源陈述，没有伪造历史git status日志。

工具把当前文件Git blob与baseline tree ID逐一比较：1136文件与baseline相同；唯一baseline内容差异为本轮修改的character_walk_trial.gd，它已由原生report的原始运行时输入哈希绑定；原report/checks及新原生测试脚本这3个文件不在baseline中。没有未经解释的其他baseline差异。契约另保存补充时完整git status，用户既有修改未处理。

原report未记录UTC运行起止，不能事后准确恢复。保留归档报告文件mtime `2026-10-26T03:06:38.331234+00:00`，注明它是补充时观察到的文件元数据，不是运行时UTC；原samples已有单调wall_ms范围4146–34130。补充创建时间另行登记，不将二者混为一谈。

## 门禁与失效机制

[validation-summary.json](evidence/native/validation-summary.json)已升级：仅完整验证成功后设置input_hashes_current=true，并绑定契约确切SHA-256、验证UTC及“保守采集后超集”范围。验证失败会将原先可能残留的true改为false并写明错误，不再仅依赖旧5输入的布尔结论。

**归档或复用本原生证据前，必须执行：**

```sh
python3 art/design/character-motion/adult-standard-v1/farming-transitions-v1/dependency_contract.py validate
```

缺必需角色/文件、依赖图遗漏、新旧哈希不符、纹理/source_contract不匹配、工具变化均拒绝。原证据随相关依赖变更失效；不得悄悄重建契约以延续通过标签。`build`只用于明确审查后的采集后补充建立；它还拒绝未被原运行时输入绑定的baseline内容差异。行为/显示输入实际改变时，应按范围重新收集证据，而不是把当前文件归因回旧运行。

## 测试

先添加回归，缺生成/验证工具时明确FAIL（1失败/8跳过）。实现后再增加摘要门禁回归，缺record_validation时2项失败，补齐后通过。

```sh
python3 art/design/character-motion/adult-standard-v1/farming-transitions-v1/test_dependency_contract.py
python3 art/design/character-motion/adult-standard-v1/farming-transitions-v1/dependency_contract.py build
python3 art/design/character-motion/adult-standard-v1/farming-transitions-v1/dependency_contract.py validate
```

最终12项测试通过，包括6类必需角色遗漏、6类实际文件缺失、真实idle纹理/run纹理/相机内容篡改、世界文件缺失、原report篡改、可达terrain遗漏，以及旧true摘要在失败时清除、成功绑定确切契约SHA。资源改动全部通过in-memory reader注入，摘要失败夹具仅在/private/tmp/coastal-dependency-gate-*；从未改真实认可资源。

build与独立validate均通过：1140依赖、12必需角色、input_hashes_current=true，摘要绑定上述契约SHA。未重跑Godot原生、玩法或导出测试。

## 限制

这份补充能证明当前资源与既有清单/原运行时哈希、baseline匹配关系，不能逆向证明两次观察之间从未发生过临时编辑。没有补造引擎二进制、导入缓存、OS、显示服务或精确UTC运行时证据。契约不提升完整动作、精确脚点/握点、换装、玩法或用户视觉认可状态。
