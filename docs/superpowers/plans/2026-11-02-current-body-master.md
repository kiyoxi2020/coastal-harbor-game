# Current Body Master Archive Implementation Plan

**Goal:** 将Q27=A认可的背心短裤全动作设为唯一现行制作母版，保留旧来源可追溯。

**Architecture:** 沿现有catalog.selected_template切换到adult-standard-v4；在parts/body/adult-v4添加明确源归档，绑定两套严格构建、四个源pack、认可及原生证据的确切SHA。保持已验收模板/源/构建字节不变，以外部选择指针升级现行身份。旧archive不可覆盖或迁移以免破坏历史依赖。制作母版选择与默认游戏运行包各自明确，不切游戏或发布基线。

**Tech Stack:** JSON/Markdown、既有build/pack verify、人物unittest/check。

1. 核对Q27绑定、源pack及旧母版引用；保留用户工作。
2. 写新归档及README，切catalog选中母版/归档和body-actions索引；同步CURRENT、制作规范和交接。
3. 核归档全部SHA、计数、旧版不变；执行人物全测与check。无美术/时序变化，不重录原生证据。
4. 记录结果并完成Progress，不提交/推送或展开下一阶段。

完成：归档、选择与文档已切换；624项SHA、490测试与check均通过，旧归档及运行资源不变。

## 用户纠正后的图片落位

此前仅增加archive清单不足以满足最终模板图片位于body下的目录约定。已将四个既有pack的164帧原登记合并，用现有pack_sources输出到parts/body/adult-v4/r001，结构与adult-v1/r001一致；9张最终PNG与layout/manifest齐全。archive-r002和catalog/制作文档改指该最终图片包，逐帧RGBA/姿态/时长等价，旧冻结依赖原位保留。相关门禁结果见2026-11-02-body-final-storage报告。
