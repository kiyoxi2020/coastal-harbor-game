# 身体评审适配器独立复查

结论：先前报告的两处校验缺口均已修复，本次只读复查未发现这两项仍可绕过的路径。未修改代码，未重新执行已由主代理完成的测试，也未改变正在采集的原生快照。

- `character_body_samples.gd:50` 在建立任何姿态索引前拒绝不合法的representation。仅允许`body`，或hoe/water/harvest各自对应的`<action>-visible`；例如hoe配water-visible、idle配idle-visible都会失败。拒绝路径返回空索引，加载器随后清空状态并拒绝安装，不会回退旧资源。定点测试保留了重绑实际layout/pack SHA后的hair、idle-visible反例。
- `character_body_samples.gd:85、98` 先要求motion.actions为字典，再逐clip严格比较`motion.actions[action_id] == clip.action.file`。因此同内容复制到未登记action路径也会被拒绝。新增反例确实复制了action文件、重绑recipe/manifest实际SHA与artifact后再检查加载失败，覆盖原先缺口。

保留的约束亦已核对：canonical纹理绑定实际pose引用，packed atlas与输出PNG逐RGBA匹配；headwear分派只有明确body kind进入BodyLibrary，其余Construction/Candidate仍走原分支，旧抽样逻辑保留。observer binding仍核实际suite SHA、manifest/artifact、runtime与实际sample路径；body合同只接受body绑定，原头包保持hair_hat绑定。

主代理报告的验证结果为两suite各156 checks通过，headwear 34、construction 48 checks回归通过。本复查确认代码和反例结构，不把该报告改写为本人独立执行，也不授予接触、美术、用户或生产认可。

复查时文件SHA256：

| 文件 | SHA256 |
| --- | --- |
| `godot2d/dev/characters/character_body_samples.gd` | `9c67ae0e830511b81266ae393b3925c49258bbea7d9eb7d3326d0f1e7b2b82ab` |
| `godot2d/tests/characters/test_body_samples.gd` | `db12a90c02afa886c2899dd4d268d103fcdfdb39d87c58b74cc1507c679da7d6` |
| `godot2d/dev/characters/character_headwear_samples.gd` | `64565bef3795234b76d4b281a97163b97aee7511d02b7ae650afd79d38271bb2` |
| `godot2d/tests/characters/registered_observation_binding.gd` | `99e5b039c3c2f981269e9c9a9d180406d7960d179dbe5bd03a969237dad655f9` |
