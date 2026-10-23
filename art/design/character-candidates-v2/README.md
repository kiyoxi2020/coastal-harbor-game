# 人物六类候选库

打开 [gallery.html](gallery.html) 浏览全部候选，切换穿戴图／透明组件、明暗背景，点击图片查看原尺寸。实际数量、输入版本、四向与兼容关系以 [catalog.json](catalog.json) 和 [验证报告](validation.json) 为准。每款保留GPT原图、提示词及生成来源；四方向不重复计数，拒绝稿不计数。

**当前验收状态（2026-10-23）：** 六类各10款结构检查通过，0错误、60项缺少评审记录提示；数量齐全不代表可组合交付完成。body09男童身高与年龄比例仍需修订，跨款接口、跨体型适配及动画未通过。

人体候选包含标准成年、三种女性体型、瘦型男性、敦实男性、男女老人、男女儿童。每个新体型是独立完整视觉母版，穿简单内搭便于看比例，**不是已完成的裸体换装骨架**。新体型保持候选状态，原已认可成年v3仍是唯一已登记换装基准。

头发、上衣、下装、鞋和帽的原位透明组件只声明适配body01的standing_0。没有通过缩放、位移或替换旧脸来拟合。上衣/下装/鞋的头手与非归属像素逐点保持v3；头部组件保护整张可见脸、耳朵与颈部。各组件在候选目录中单独展示；全部新发型与帽子的任意搭配仍需对应帽体积下的收发规则，不能将单件拟合直接当成100种发帽组合通过。

首两套衣裤鞋的8个交叉状态×4方向、两种旧发帽附加全套×4方向，见second-set-swap。原生切换32个衣裤鞋纹理的临时证据曾生成在/private/tmp/coastal-candidates-swap-delivery，尚未完成逐页视觉复核与入库。短鞋可能露踝，露出的皮肤由母版提供，不能随裤/鞋携带另一套皮肤。长裙、雨靴等的所有跨款接口组合尚未穷举，选中后做对应局部评审；尚未接正式角色、碰撞、行走或其他动画。

构造与复现：

```sh
python3 art/design/character-candidates-v2/build_head_body_candidates.py --all
python3 art/design/character-candidates-v2/build_wearable_candidates.py --all
python3 art/design/character-candidates-v2/assemble_catalog.py
python3 art/design/character-candidates-v2/restore_baseline_head_layers.py
python3 art/design/character-candidates-v2/build_gallery.py
python3 art/design/character-candidates-v2/verify_catalog.py
```

重构造会改变或清除对应评审，不能自动继承通过。输入和证据的绑定说明见[工具说明](TOOLS.md)。原生总览临时输出位于/private/tmp/coastal-candidates-delivery，尚未完成视觉交接；本目录没有已交付的native/native-swap证据集。后续单项review须以artifact_digest绑定实际源/组件/规则字节，并单独登记用户认可。

已纠正的本批问题：裤腰上移的源稿退回GPT重做；高挑稿拉长腿后改用女性母版直接设计健整体型；错误尺寸儿童稿重做；领口原图肤色和暗下巴按真实颈域排除；发帽提取不保留脸部/肩颈的黑线；旧proof/hair文件名曾同时指向完整穿戴图，现从原源与原语义遮罩重新提取真正透明层。无现行依赖的拒绝稿已归档，详见[清理记录](../../archive/README.md)。pants08/rejected/skirt-waist仍是当前候选声明的生成参考，保留原图、提示词和来源；jobs.json保留历史任务记录。

分工：主代理GPT设计、头部/人体构造、集成与原生验收；gpt-6.1-sol high独立完成目录校验/原生总览工具、衣裤鞋构造及领口归属复查。候选美术与评审工具随本次整理纳入本地提交，未推送或导出。
