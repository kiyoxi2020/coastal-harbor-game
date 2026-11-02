> 2026-11-02清理说明：所述历史制作媒体和原生过程文件已按用户授权删除，旧数据路径已退役，本文仅保留文字结论；当前数据与验证见[执行报告](2026-11-02-resource-cleanup-executed.md)。

# 最终母版图片归入body

用户指出最终模板图片应像adult-v1一样位于body下。此前adult-v4只放归档清单是遗漏，本次补齐实际图片。

最终目录：[art/characters/parts/body/adult-v4/r001/atlases](../../art/characters/parts/body/adult-v4/r001/atlases/)。包含body下idle/walk/run/hoe/water/harvest六图集，以及hoe-visible、water-visible、harvest-visible三图集。r001同级layout.json和manifest.json由现有pack_sources生成，源计划为sources/adult-v3-actions-packed-r001/packing/r001.json。

所有164帧从原四个pack的登记计划汇总，没有改原box/root/scale/pose/duration。pack与verify通过；新旧每帧RGBA和布局字段全部一致。[等价记录](tank-actions-v1/body-storage-equivalence.json)。归档升级archive-r002，catalog及制作入口同步；archive-r001与Q27原源、模板、recipe、build保留原字节，不重写既有证据。

没有修改美术、动画或默认游戏，不新增播放器/合成器。原图和必要旧派生仍保留冻结依赖；后续制作的最终图片入口明确为body/adult-v4/r001。

490项人物测试通过（323.749s）；仓库门禁通过59严格配方、53构建、9冻结旧配方、1既有游戏接入。归档637项SHA复核通过，git diff格式检查通过。

末次pack复核发现浏览目录后新增2个Finder .DS_Store，已移至/private/tmp/coastal-body-final-storage-finder-metadata备份，复核随后通过，artifact仍为60c77c0e84469a1990d3d9c528d4c46371bacc5ba31a721dc9abf6382ba31a62。未改PNG或放宽验证。
