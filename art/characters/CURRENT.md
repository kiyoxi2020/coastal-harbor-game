# 当前人物与能力

当前制作母版及主游戏主角为V4男性背心短裤，catalog.selected_template唯一指向adult-standard-v4。最终PNG在parts/body/adult-v4/r001，源图集独立化后两套recipe/build为r002，archive-r003。运行package路径仍adult-v4-tank-visible-r001，玩家SpriteFrames/姿态/像素/时序未改。

V5已认可的像素风最终包为parts/body/adult-v5/r012，template-v5-r009、两套recipe/build-r010、archive-r010，仅作本地当前候选。两个包均9图集、164源姿态、24方向动作/108显示帧；农事有无工具数据分别完整，未授予衣柜/严格接触或生产发布。

评审：`python3 tools/characters/review.py body-actions`或`body-pixel-v5`。严格构建与目录职责见[README](README.md)。旧v1/v2/v3、静态候选、旧服饰/发帽评审数据均已退役；不得从旧报告路径恢复为第二套现行模型。

[执行清理与验证报告](../../docs/reviews/2026-11-02-resource-cleanup-executed.md)。
