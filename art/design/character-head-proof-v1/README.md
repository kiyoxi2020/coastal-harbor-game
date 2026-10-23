# 成年母版头部16帧候选

2026-10-22。使用GPT内置imagegen编辑当前母版，完成1款栗色短发、1款草帽的四方向头部小样。当前为**已做主代理原生检查、待用户外观认可**，不是完整人物组件库验收。

## 直接查看

- [明背景16帧与头部局部](native/review-light.png)
- [暗背景16帧与头部局部](native/review-dark.png)
- [真实Godot评审场景截图](native/scene.png)
- [验证步骤、覆盖范围与哈希绑定](review.json)

每张图按行排列：裸头、仅头发、仅草帽、头发＋草帽；列为南、左侧/西、右侧/东、北。每格左边是游戏同尺度完整人物，右边是头部局部。完整人物身体显示138px，与现有主角230px有效图高×0.15场景尺度×4镜头的138px一致；全方向共用一个整帧尺度，没有单独缩放头或衣鞋。

独立场景：`godot2d/scenes/reviews/character_head_proof.tscn`。可在Godot直接打开，窗口较小时上下滚动。它只供评审，没有接入正式主角、餐馆顾客或玩法状态。

## 来源和构造

身体和所有裸露五官来自[当前母版](../character-bodies/adult-standard-v1/source.png)及其[四向注册](../character-bodies/adult-standard-v1/registration/registration.json)，RGB/alpha原样切分。原图在原生明暗背景下已可正常显示，因此没有采用会改变人物像素的背景重绘候选；不以alpha最高254直接判失败。

| GPT编辑 | 提示词 | 处理状态 |
|---|---|---|
| [发型第一稿](hair-worn-v1.png) | [提示词](hair-prompt.txt) | 否决：东向发生明显位移/变形，不参与构造 |
| [发型修订稿](hair-worn-v2.png) | [提示词](hair-v2-prompt.txt) | 只提取经核对的头发区域；生成图中的衣物/身体像素一律不用 |
| [草帽稿](hat-worn-v1.png) | [提示词](hat-prompt.txt) | 只提取帽子表面区域，生成图中的脸/身体不用 |

[语义遮罩](semantic-masks.json)逐方向登记发际线、耳部避让和帽檐内缘。颜色范围只在人工限定的头发区域内辅助排除皮肤/背景，不使用暗色连通块推导五官边界。帽内发区按对应方向的帽檐包覆体积遮挡；裸头/仅发型状态不受影响，不使用眼鼻矩形补丁。图层替换采用单一像素归属，不反复alpha叠加描黑边。

[构造脚本](build_head_proof.py)仅切分、应用遮罩与原位合成，不绘制人体，不移动脸、手或脚，也没有引用旧A/B的脸或手。proof目录保留发、帽、帽内头发、遮罩及16种结果；运行纹理在`godot2d/assets/characters/adult-standard-v1/head-proof/`。

## 验证与边界

构造时逐像素断言16种状态中所有非组件归属区域RGBA与母版一致；四向母版切分同样逐字节一致。主代理已查看明暗背景全图、完整脸轮廓和游戏尺度，未观察到鼻旁/眉部残线，修正了第一轮背向帽冠穿发。

[原生验证脚本](verify_native_scene.gd)实际加载独立场景16张512×768纹理，并让同一个预览Sprite2D逐一切换16种结果；Apple M4 Compatibility原生通过。[布局渲染脚本](render_review.gd)提供明暗背景对照。所有验证独立运行，不加载玩法或玩家存档。

manifest.json记录原图、部件、遮罩、构造脚本、注册、评审场景、原生脚本与输出纹理哈希；review.json把原生证据绑定到对应artifact_digest。任何输入改变均应复查，旧截图不能替代当前版。

尚未完成：用户外观认可、衣裤鞋可替换接口、隐藏身体补齐、其他体型适配、动画和正式场景人物接入。后续仍遵循[统一人体管线](../../../docs/design/character-art-pipeline.md)，不能据本小样直接扩量60款。

后续正面眼睑与眉毛反馈已制作[独立v2修订候选](../character-bodies/adult-standard-v1/revisions/front-eyelids-brows-v2/README.md)，本目录截图仍是原版基线，不替代v2验收。
