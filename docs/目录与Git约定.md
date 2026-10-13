# 目录与Git约定

Git根目录即项目根目录，分支main；只建本地仓库，不配置远程、不推送。

## 跟踪范围

跟踪当前Godot代码/场景/素材/测试、Unity Assets/Packages/ProjectSettings、当前美术源资产、设计简稿和维护说明。tree-set-v4、环境材质environment-v2、人物v1等名称是仍有效的素材标识，不意味着旧工程副本。旧树试制和旧场景不跟踪。

忽略archive、work、builds、Unity Library/Builds/Logs/UserSettings、Godot.godot、测试输出、旧交付、旧场景、旧树、Blender备份与草稿。交付只跟踪说明/清单/报告，不跟踪ZIP、应用、视频和预览图。忽略不等于备份，这些本地文件需另行保存。不要用git add -f把历史加回。

## 最新工程

始终修改godot2d，不从历史压缩包覆盖回来。当前为v0.5.1生活手账，E交互和tree-set-v4引用保留，B/Tab打开手账。原六组场景检查260项，加上目录、库存、操作、保存与手账检查，共386项；导出Mac应用52项和重新启动恢复8项另行验证。旧单树专项在archive。

## 验证与交付

Godot4.7.1导入godot2d/project.godot，F5运行。命令行可运行tests/test_interaction.gd、test_world.gd、test_tree_set.gd、test_environment.gd、test_foraging.gd。日志用--log-file明确写入/private/tmp或work，避免沙箱下user目录日志访问失败。先完成导入再运行测试。

交付与预览只保留2D和3D入口。更新交付时旧文件移到archive，再将最新版放回稳定目录，勿新增日期版本目录。Mac包和源码包必须对应同一当前运行版本，当前为v0.5.1。

Unity已接入的源资产保存在art/prototype/engine-ready和art/characters/returnee/engine-ready；最新Blender场景在art/prototype/v3，尚未接入Unity。历史生成脚本依赖旧场景，留本地不跟踪；Git克隆后可直接编辑当前.blend，不能假定可从旧v2重新生成。Unity/Blender本轮未重建测试。

旧资料路径映射见目录迁移记录.json；历史文档中的路径按其当时快照解释，不作为当前入口。
