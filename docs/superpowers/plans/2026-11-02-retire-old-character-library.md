# 旧资源及人物历史链退役 Implementation Plan

> **For agentic workers:** Execute continuously with scoped independent test migration; user authorized deletion and exact legacy baseline retirement. Do not commit/push.

**Goal:** 执行清理提案A组和旧人物链退役，保留主游戏所需数据、V4制作母版和V5最终动画包。

**Architecture:** 以V4最终9图集建立独立1:1动画输入和新r002严格配方/build，复用template-v4；保持216构建帧和108运行帧字节、pose/root/time不变。精确重绑定V4integration元数据，清退旧v2接入、旧配方/构建/模板/部件及制作源和评审索引，仅删除已退役基线条目，不修改运行代码或放宽校验器。测试使用临时合成夹具或当前独立动画包。

**Tech Stack:** Python/Pillow、现有pack_sources/build/godot_integration及Godot。

## Global Constraints

用户已批准A组及刚才列出的旧人物资源。保留当前V4、V5、主游戏实际主角/NPC资源及通用工具。无二进制备份；过程总结为文字。已存在的用户代码修改保留，不提交Git。更改基线须逐项删除已获准退役范围，现行主角/NPC运行纹理与脚本/场景SHA保持。

### Task 1: V4独立动画

- [x] 记录当前V4/V5图集、两套build输出、运行PNG、运行帧资源、保护代码/场景SHA。
- [x] 建立sources/adult-v4-animation-r001和1:1计划；重封装V4布局/manifest，核对语义与图集字节相同。
- [x] 构建V4两套r002配方/build，逐输出比对；更新当前body-actions与integration源绑定，保持运行SpriteFrames和PNG不变。

### Task 2: 测试去除旧资料依赖

- [x] 精确定位读取旧人物库的真实样例测试，先验证其在无旧库环境下失败。
- [x] 使用当前独立V4动画作真实像素oracle；历史组合/注册测试迁为运行时生成的小型夹具，保留拒绝错误及像素断言。
- [x] 不skip测试、不mock真实构建校验器、不保留旧二进制/base64资产。定点测试通过，记录责任与结果。

### Task 3: 精确清退

- [x] A组CSV重新核SHA后删除，保护用户新改文件。
- [x] 仅保留V4/V5的parts/body、templates、sources、两套recipes/builds及body-actions/body-pixel-v5评审；移除旧catalog/coverage/候选入口与旧v2integration/帧资源。
- [x] 基线移除40旧build、528旧文件、9旧配方及旧v2integration，production文件仅删除旧v2包并更新必要V4manifest SHA，运行代码/主场景/tres/PNG SHA保持；给出确切差异。
- [x] 更新当前档案与认可等价绑定、README/CURRENT/STATE/HANDOFF；旧制作与退役只保留文字，不复制archive树。

### Task 4: 验证交付

- [x] 构建/pack/两套body suite预检、当前归档SHA核对、基线差异审查通过。
- [x] 人物完整unittest及check.py通过，农事/图标与Godot实际主游戏和动画加载检查通过；任何代码逻辑修改先有失败测试。
- [x] 独立复核删除范围、测试质量与运行数据等价；Progress完成，交接已完成/限制和剩余问题。

实际实现补充：为Git运行资源边界新增显式verify-runtime，保留严格verify不回退；重复导入配置节/非规范覆盖键先失败后修复。运行与制作门禁、CI职责已分开，最终504测试通过。
