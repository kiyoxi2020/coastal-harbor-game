# 四向idle背心短裤实施计划

**Goal:** 把Q26认可的男性四向idle源稿登记为可验证的母版候选。

**Architecture:** 沿统一character_model_id与现有pack_sources/build/body_native入口，创建有前代关联的adult-standard-v3候选，仅声明idle。既有v2冻结模板与108帧不改；不另建播放器或构建器。

**Tech Stack:** GPT imagegen、现有Python/Pillow源登记工具、Godot原生GPU。

## 约束

- 仅四向idle；头脸、完整身体来自认可r002，禁止旧脸手拼贴或部件挪缩。
- 保留1024×1536整表、512×768源格，四格统一整帧1/5登记到256×224；根点按实际脚部定位。
- Q26仅外观认可；新构建仍review-only，不继承全动作/换装/物理接触/发布证据。
- 旧运行基线、旧源与用户已有修改保持。测试资料仅/private/tmp/coastal-*。

## 步骤

- [x] 源与认可：sources/adult-v2-idle-tank-shorts-r001内记录Q26、SHA、四格与根点，检查真实alpha显示。
- [x] 登记：现有pack_sources.py打包到parts/body/adult-v3/idle-r001并verify；原图逐格登记、统一倍率，不重画或清理认可像素。
- [x] 严格构建：templates/adult-standard-v3下只登记idle四向；recipes/adult-v3-idle-tank-shorts/r001.json通过build.py build与verify。
- [x] 原生静态：以body_native.py与capture_body_raster.gd冻结并观察4个实际PNG，保存截图和材质像素对应回执；检查明暗背景原尺寸显示。不声称连续动作或换装通过。
- [x] 必要检查：python3 -m unittest discover -s tools/characters/tests；python3 tools/characters/check.py；记录结果及未验证范围，同步PROJECT_STATE/HANDOFF与Progress。

本任务由主代理执行，主要是已有工具的数据制作，无新增逻辑代码，不为数据重复编写实现镜像测试。
