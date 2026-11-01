# RUN16 衣装源登记与冻结报告

完成四向 run 各4帧 canonical A 的 top03/原橄榄裤/棕鞋有限衣装接口，共16个真实跑姿；各组精确复用已有唯一 canonical B idle。全部为 review-only，不继承用户、原生或动态认可；24格总交付尚未完成。

## 冻结入口

|方向|配方（art/characters/）|recipe SHA256|最终严格 build|artifact digest|
|---|---|---|---|---|
|south|recipes/top03-newrun-south/r001.json|fdb3dea56260aee1acc338bca84a654ed149687c8a1674c600971b5f26ac078c|builds/top03-newrun-south-r002|ae75d386730f176139c04860041d6cde647acf91f7c1ae0fdde71397db269799|
|west|recipes/top03-newrun-west/r001.json|693e04330904bc4e286b80189e6f39d886f5fe092165d04dc99c55381741bba6|builds/top03-newrun-west-r002|bb49d51fa471e1e43a918bd2b38eaaba82a0e6dbe2a469d46362eea3f2a85784|
|east|recipes/top03-newrun-east/r001.json|a18740395cbe048acfcaabd5a98ff3b56a3d463d8d9ec63affb30a6ed151fa29|builds/top03-newrun-east-r002|07f8266346e4518d4dc25960b2c8cec3e3dd6faf1db88fd420bc6e6914fe1b1d|
|north|recipes/top03-newrun-north/r001.json|eafcdd588107775a6cb5200e06938bc4a853784e0c77baf64223e9c97715e787|builds/top03-newrun-north-r002|3cf4ee3fac19292da9238689a511a8ba898e111d411dbea0c4c59e932a7f0ad5|

新增命名域：`sources/newrun-top03-{dir}-v1`、`sources/newrun-canonical-a-{dir}-reference-v1`；top03/original-pants/original-shoes 的 `newrun-{dir}-r001` definition 与 adaptation；独立 pose annotation/body-view 同 revision。原 walking、旧 run r001、engine、consumer、baseline/current manifest 均未修改。首轮未交付构建完整归档为本临时目录 `pre-admission-{dir}-r001-build`，最终只使用上述 r002 build。

## 来源与边界

- RUN统一选择原有完整canonical A，不把r001 B stub、rejected south/north B转正。A是同adult-standard-v1现有完整母版，具体poses/frame SHA与原始GPT/旧parts/prompt lineage在 `canonical-run-inputs.json` 及8个正式source bundle metadata内。E/W accepted B只作longsleeve几何参考：8帧实际protected_hands RGBA0差、B_editable外RGBA0差，证据 `west-east-A-B-protected-comparison.json`。不凭标签B另建模型。
- 42张完整GPT原图及对应提示词均保留。所有操作源为完整1024×1536画布，明确NEAREST1/2→512×768、零位移；source RGB逐点保留，binary多源选择不重复软alpha，显式canonical-surface-alpha wrapper只继承原同pose完整frame alpha。未按部件缩放、移动、补色或以halo填缺材。shirt-only的root是从实际authoring整帧注册框继承的坐标，非声称图中可见脚根；不按图片大小猜比例。
- 材料范围包括原A shirt及真实forearm物理轮廓上的fitted sleeve，保留原手、脸、下身和中性/混合外轮廓。ownership、coverage、手前景参考分别保存。颜色/alpha仅产生检查候选；最终记录逐点/解剖区域的语义决定。原cream/skin候选与旧body_arm池中的neck、hand、boot、上髋pants残留均未重命名为cloth。
- 下身source是已注册A完整frame的字节同一alias，并完整追溯原GPT/原parts和canonical登记，明确derived、非新GPT raw/非第二body/非隐藏身体。原pants与shoes均有真实非空有限material层，不作空层或替代脸手。
- West3/North3首轮shirt板的偏移/缩放不能由同一真实多点Δ解释，拒绝以atlas单锚凑覆盖；相应完整原图/提示词作为未选择attempt保留。West3通过移除错误pose参考的完整A编辑恢复；S0通过实测真实far腕颈y468–472、移除完整body参考并在source board中明确腕界恢复navy knit cuff，不挪动衣袖。
- 南r002四份几何参考临时alias在后续腕界复测时被覆盖：按原执行polygon表和同一Pillow流程忠实重建，正式source stage明确标为reconstructed-input，不声称独立保留原输入字节。原始GPT输出从未替换或裁剪；后续reference独立文件保留。

## 明确保留的旧衣残留

North run2在 `[345,459]` RGBA `[248,233,213,252]`、`[345,460]` RGBA `[113,106,95,252]` 是原cream袖角。全部新源这里只有halo，未当新材质、未补色、未擦底。经主代理原生尺寸及8x静态source审查，允许作为明确已知旧衣边缘留在top coverage外；它与新ivory不连续，不能宣称16pose整top旧材0。原生显示小于1屏幕像素，最终Godot应特别观察，若可辨再处理。证据 `north2-explicit-original-ivory-two-points-native.png` 与 `north2-original-ivory-two-points-8x-comparison.png`，正式North source metadata逐坐标绑定原RGBA。

## 实际验证

- 4个最终 build/verify 全PASS，每组run4＋冻结idle1，共20帧。
- `actual-build-invariance.json`：16run整体alpha差0、top coverage外RGBA差0、实测真实手前景/脸/下身/上髋修正点差0；pants/shoes有限material identity原RGBA差0；4idle与冻结旧build完整RGBA差0。
- `source-asset-closure.json`：8个bundle、175个assets全部存在且SHA匹配。最终完整画面 `run16-actual-build-versus-canonical-and-idle.png`。
- `python3 tools/characters/check.py` 最终PASS：strict_recipes21、strict_builds18、frozen_legacy9，production closed，现player-unified-v4保持。日志 `final-check.log`。
- 本批执行全unittest：212项/120.646s，210通过、2项当时在主代理并行新recipe_assembly.py的string manifest.recipe处理报错。主代理随后修复，新增2项27s GREEN；按主代理协调不在其后续metadata建revision期间重复全suite，最终全批freeze后由主代理跑一次全局门禁。未将该前时段suite写成全绿。
- engine保持build_contract `7bdb41fddaca2930c614280063a2add07879edbc4961a0e42313f17d9a7d4475`、composition_contract `c514c82108427811291aac1d04336863b87f9adb4b782c1a3cc75f158e6c117f`。

run速度：基础108、默认因子0.75→实际81 world units/s；原4帧均80ms；phase按actual_distance/108推进，运行时不得重复乘0.75。当前衣装构建不创建另一播放器。

尚未验证：本批新衣装原生连续循环、条纹相位/袖接缝动态观感、最终固定hair_hat混搭及用户认可；由主代理和head任务继续集成。报告中的数量、重建和静态不变性不替代这些验收。
