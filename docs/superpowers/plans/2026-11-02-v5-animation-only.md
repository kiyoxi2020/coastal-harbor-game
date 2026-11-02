# V5 独立动画归档 Implementation Plan

> **For agentic workers:** Execute inline; user has authorized implementation and deletion. No delegation required.

**Goal:** 保留r012动画必需数据，删除V5制作过程资产，过程仅文字总结。

**Architecture:** 现有pack_sources读取已认可完整图集的独立源快照，以1:1整帧重封装r012；沿现有construction-v1构建r010配方，保持template-v5-r009和全部输出RGBA、pose/root/time一致。无需修改工具或放宽校验。

**Tech Stack:** Python、Pillow、现有人物构建/评审/Godot。

## Global Constraints

最终PNG仍在parts/body/adult-v5/r012；默认v4与runtime-baseline不变。用户明确只保留动画数据，覆盖旧规范保留制作过程的要求；更新唯一规范说明成品独立与文字总结。

### Task 1: 独立动画输入与等价构建

- [x] 记录旧9图集SHA、164姿态/时序/锚点和两套108帧输出SHA。
- [x] sources/adult-v5-animation-r012/prepared保存9完整图集快照，source.json绑定。packing/r001.json仅按最终格子1:1注册，不引用旧版本。
- [x] 使用pack_sources.py pack/verify；比对PNG和语义布局完全一致后替换r012的manifest/layout。
- [x] r010两套配方使用独立输入，build.py build/verify；比较108帧输出完全相同，更新当前suite绑定。

### Task 2: 过程资源清理与文字归档

- [x] 计算全部保留严格构建闭包及v4生产依赖，确认删除清单无交集。
- [x] 删除V5旧source目录、r010/r011残留、r009旧配方/build与旧归档、过程截图和结构化制作记录；不复制到其他备份目录。
- [x] parts保留最终动画包及新SHA清单/认可等价记录，文字总结制作决策与原生证据范围。更新导航/唯一规范，历史证据不冒充新合同。

### Task 3: 验证交付

- [x] 当前suite preflight和两套build.verify通过，实际图集和帧输出SHA与认可版本相同，任何当前输入不再引用被删目录。
- [x] 运行490人物测试与check.py强制门禁；若仅元数据/输入闭包改变，原生像素外观以精确等价证据关联原认可，新增原生启动检查确认加载。
- [x] Progress结束并汇报保留范围、释放体积、测试及边界。
