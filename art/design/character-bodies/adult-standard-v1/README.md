# 成年标准体型 adult-standard-v1

[原始母版](source.png)是用户明确选定的四向站立外观，原始文件名exec-85e8d851-94a4-4289-87cf-47757592d66d.png，2048×768。原图未缩放、未改像素；[提示词](prompt.txt)和[来源及状态](selection.json)一并保留。

SHA256：`a25ffb61c83135d6f1de87d2e7b18ad460ee8f6c659bc7c5bb695a6f984fabb7`。

[原尺寸登记脚本](registration/register_body.py)可从原图复现切分，不改变像素或局部几何。

原始外观选中状态保留；当前已完成四向整帧登记，见[注册元数据](registration/registration.json)和[原图明暗背景原生检查](registration/native-alpha-backgrounds.png)。保留原始RGBA，没有采用重绘提取候选；源图alpha最高254本身不是失败判据。

原始prompt.txt仅用于溯源，其中旧“还原其他来源五官”的描述不再执行。当前脸、手和身体只来自本source.png。

[头部16帧小样](../../character-head-proof-v1/README.md)已完成原生对照，待用户外观评审。图中的衬衣和短裤仍是完整母版外观，不是已拆分、补齐隐藏区域或兼容换装的身体。衣裤鞋、其他体型和动画继续按[统一管线](../../../../docs/design/character-art-pipeline.md)分别验证。

最新反馈修订见[正面眼睑＋三向眉毛v3](revisions/directional-brows-v3/README.md)：保留正面眼睑缩短及眉毛，并补齐两侧眉毛；原生明暗/发帽对照已检查，用户已认可本轮左右侧眉毛。后续面部源图以selection.json的active_revision为准。原始source.png仍保留为基线。
