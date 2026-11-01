# 人物资产分类与精简实施计划

**Goal:** 实际按部位/款式组织人物资产，删除非必需历史展示材料，保持当前动作/衣服加载运行。

**Architecture:** 保留同一制作和Godot播放管线。显式路径映射迁移JSON及SHA，严格重建制品，以旧输出字节/像素和动作元数据为迁移判据。

**Tech Stack:** Python/Pillow、JSON、Godot GDScript。

## 约束

用户已批准整理和删除历史验收材料；不自动提交或推送，不改生产玩家与baseline生产部分，不改图像尺寸/像素/动作时序，不新增模型或播放器。按实际依赖保留来源和mask，不以扩展名盲删。

## 工作项

- [x] 路径合同：先新增带category路径的失败测试；更新build_contract/composition_contract/recipe_assembly及fixture，保留错误category/identity拒绝。
- [x] 迁移工具：测试路径替换、依赖SHA传播、碰撞/循环/缺失拒绝与干运行无变更；实现tools/characters/organize_library.py，保存每文件旧新SHA与删除清单。历史原始收据保持只读。
- [x] 执行迁移：以7ef64b6为恢复点，仅操作清单内文件；内部review文件按实际闭包判断，保留所有构建/加载输入。strict build使用build.construct生成临时新目录，逐帧比较后再更新现行入口。
- [x] 加载与门禁：Godot同步实际parts路径；legacy仅按明确迁移关系核验，生产冻结不变；旧导入verify与当前迁移验证衔接。
- [x] 验证：python3 -m unittest discover -s tools/characters/tests；python3 tools/characters/check.py；两历史verify；review.py all-actions-construction --dry-run；Godot实际资源及全动作原生运行检查，日志和夹具均/private/tmp/coastal-*。
- [x] 交付：更新README、PROJECT_STATE/HANDOFF，报告目录、删除数量/大小和验证边界；不保留重新生成的大型验收视频。

分工：主代理负责迁移工具、资源、Godot、门禁和最终验收。gpt-6.1-sol/high子代理先独立审查依赖风险，后负责Python路径合同及其测试；任务可独立且主代理同时处理迁移，双方不修改同一文件。

## 完成结果

47严格构建输出PNG与迁移前逐字节一致；53配方/47构建/9legacy门禁通过，runtime-baseline原字节未改。379项Python执行377首轮通过，Finder元数据阻断与历史报告测试依赖两项处理后定点复验通过；未机械重跑其余用例。原生24格84姿态245检查及实际加载197检查通过，画面已目视。删除514文件约341.92MiB，原始资料仍可从7ef64b6恢复。未提交/推送/生产切换。
