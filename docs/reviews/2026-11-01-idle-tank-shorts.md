> 2026-11-02清理说明：所述历史制作媒体和原生过程文件已按用户授权删除，旧数据路径已退役，本文仅保留文字结论；当前数据与验证见[执行报告](2026-11-02-resource-cleanup-executed.md)。

# 四向idle背心短裤母版

用户将任务收窄为先更新idle，并以Q26=A认可r002男性体型：侧面胸腹平直、正背面腰腹加宽。四向idle源登记和严格构建已完成；这是同一统一人体体系内的后继母版候选，只有idle能力，尚未替换默认游戏或扩到其他动作。

## 交付入口

- 原图、prompt、父图SHA与认可：[源目录](../../art/characters/sources/adult-v2-idle-tank-shorts-r001/)。Q26不等于登记、动态换装或生产认可。
- 母版：[adult-standard-v3](../../art/characters/templates/adult-standard-v3/template.json)，前代adult-standard-v2保持冻结，不建立第二套构建/播放管线。
- [严格配方](../../art/characters/recipes/adult-v3-idle-tank-shorts/r001.json)与[构建清单](../../art/characters/builds/adult-v3-idle-tank-shorts-r001/manifest.json)。artifact_digest：`13fbe4833a935b5abfb94e052fb6f5dca16022221ba4b2c4ff7c9a7d8a240c35`。
- [明暗底实际尺寸对照](idle-tank-shorts-v1/four-idle-native-size-light-dark.png)、[原生世界截图与回执](idle-tank-shorts-v1/native-r001/)、[显示尺寸及验证边界](idle-tank-shorts-v1/verification.json)。

## 制作与验证

保留GPT完整1024×1536源表，按四个512×768格位切分；现有pack_sources.py用统一1/5整帧倍率与各姿态脚部占地根点登记到256×224。人物原生显示约139–140像素高。没有单独缩放、挪动身体部件或拼贴旧脸手，也没有修改源alpha。初始预览的棕色光晕主要是透明像素RGB；真实明暗底alpha合成及原生世界未显示该背景光晕。

pack与verify通过，统一build.py的schema3身体配方build/verify通过，四向各一独立idle帧。仅声明真实存在的idle能力，缺walk/run/农事不能作为完整角色加载或发布。四张canonical PNG逐RGBA来自同一登记图集。

macOS Apple M4、Godot4.7.1真实GPU采集4姿态，8个背心/腿部材质点像素对应通过，382个冻结依赖前后SHA一致。主代理目视四张世界截图和明暗实际尺寸对照，轮廓、裸露臂腿与衣物边界清楚。观察器为既有body_native/capture_body_raster，不另建播放器。

人物全套473项unittest通过（255.603秒）；git diff --check通过。仓库check通过：57严格配方、51严格构建、9冻结旧配方、1本地接入；生产发布仍关闭。

## 边界

未验证连续运动、换装、发帽16状态、衣裤鞋混搭、严格足部接触、遮挡交互或导出应用。旧108帧、红毛衣小样、现行玩家及runtime-baseline保持原状。production_release仍关闭，不将四向idle完成写为全动作母版完成；后续动作按用户下一明确任务处理。

复核命令：

```sh
python3 tools/characters/pack_sources.py verify art/characters/parts/body/adult-v3/idle-r001
python3 tools/characters/build.py verify art/characters/builds/adult-v3-idle-tank-shorts-r001
python3 -m unittest discover -s tools/characters/tests
python3 tools/characters/check.py
```

完整原生采集临时目录为`/private/tmp/coastal-idle-tank-native-r001`，持久副本见上述原生目录；无需重新采集可审阅4张截图。新采集必须通过body_native.py新建证据目录，不能覆盖旧回执。
