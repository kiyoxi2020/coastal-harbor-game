# 成年灰色连体底衣：源图准备产物

## Q21=A后的身体源归档入口

`archive-r001.json`为已核验的身体 SOURCE归档清单：24动作方向/108身体姿态、56完整农事工具姿态，绑定586源/派生/严格构建/工具依赖及Q19/Q20视觉、Q21范围决定。后续衣物A/B必须读取此清单的同一身体源与shared_layout，不临时替换母版。用户明确允许本素材阶段先归档，将精确支撑/滑步/握点/地面目标接触移至后续集成独立验证；这些物理字段仍为false，不授予生产或完整动态混搭认可。

下方`r001/manifest.json`仍是不可变的review-only源图准备manifest，其complete_body_archive=false保持原义不改；上层archive清单记录本阶段source归档完成，二者类型/范围不同。正式游戏及runtime-baseline未切换。

`r001/`执行用户Q18=A授权的切分/整帧登记/打包，属于review-only源图准备；其manifest本身不发放身体归档认可，完整身体源归档范围由上层archive-r001.json记录。生产玩家、发布清单与冻结基线未切换。

- `atlases/body/`：idle/walk/run/hoe/water/harvest六图集，24动作方向、108姿态。
- `atlases/hoe-visible/hoe.png`、`water-visible/water.png`、`harvest-visible/harvest.png`：完整人物＋工具动作，另56姿态；不是独立工具图层。
- `layout.json`：唯一共享布局，256×224格、root(123,201)，north/west/south/east方向行及逐帧区域、时长、来源和整帧变换。
- `manifest.json`：不可继承的源图准备身份，绑定实际输入、工具/Pillow、输出PNG和RGBA；complete_body_archive固定false。

采用的高分辨率完整源、提示词和父图留在`sources/visible-atlas-body-r001/`；本目录只放派生PNG及其重建必需清单。计划为`sources/visible-atlas-body-r001/packing/r001.json`。未清理alpha、未重画、未贴其他人物脸手，未单独挪缩身体部位。

```sh
python3 tools/characters/pack_sources.py verify art/characters/parts/body/adult-v1/r001
```

verify重建全部输出并逐像素比较。新人物配方仍必须使用既有`coastal-character-construction-v1`和`build.py build/verify`；不能把这份源图准备manifest交给严格人物加载器。

临时原生核验图/录像在`/private/tmp/coastal-visible-atlas-body-r001/native-packed-r002/`，轻量摘要记录于source.json；它们只证明源图准备及原地播放。最终密度/连续切换、美术认可、实际移动支撑/滑步、工具接触、空间遮挡和换装兼容仍需对应验证，通过之前不启动衣物A/B。
