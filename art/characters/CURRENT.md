# 当前人物与能力

当前主游戏主角为V5像素风；制作母版仍为V4男性背心短裤，catalog.selected_template唯一指向adult-standard-v4。最终PNG在parts/body/adult-v4/r001，源图集独立化后两套recipe/build为r002，archive-r003。默认运行包为adult-v5-pixel-visible-r010，SpriteFrames为player_body_v5_frames.tres；整帧根点125/201，缩放0.25。V4制作包保留；旧V4运行包已按用户批准退役，测试夹具与CI改用V5。

V5已认可的像素风最终包为parts/body/adult-v5/r012，template-v5-r009、两套recipe/build-r010、archive-r010，已按2026-11-03用户指令接入默认主角（本地开发接入）。两个包均9图集、164源姿态、24方向动作/108显示帧；农事有无工具数据分别完整，未授予衣柜/严格接触或生产发布。

评审：`python3 tools/characters/review.py body-actions`或`body-pixel-v5`。严格构建与目录职责见[README](README.md)。旧v1/v2/v3、静态候选、旧服饰/发帽评审数据均已退役；不得从旧报告路径恢复为第二套现行模型。

[执行清理与验证报告](../../docs/reviews/2026-11-02-resource-cleanup-executed.md)。
