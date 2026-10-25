# 西向hoe v2返工：已拒绝

仅在本目录增量保留v2，两次GPT方案及所有旧稿均保留。结果与边界见[简短验收](acceptance.md)；入口为[可播放评审HTML](review.html)。**本轮未获得可用hoe动作；source密度、二维工具合同及跨格检查失败，未获用户批准，不接入生产。**

第1次改变为从4格原像素approved-idle参考重新绘制，不输入旧失败hoe；第2次再改为标准1024×1536的2×2格，避免超宽版面影响，仍保持每格512×768。同一GPT源内完成4姿态。工具明确请求300px直柄、两端可见、固定握点间距及仅在图像平面旋转。实际未满足，已达最多2次方案上限，不继续机械重试。

完整原图在[sources](sources)，提示词在[prompts](prompts)，来源与参考哈希见[source-manifest.json](sources/source-manifest.json)。参考板只是将已认可idle原RGBA原尺寸复制到各格，作为GPT输入，不是正式动作美术。新人物/工具像素全部由GPT built-in image_gen生成；精确生图模型标识未由工具返回。

登记只将attempt-2四格原样裁为512×768、再横排拼接；没有重采样、局部位移、重画或alpha修补，连失败的邻格碎片也原样保留。名义根点[256,708]仅为评审原点，实际脚点/根点未通过；显示比例138/582、nearest。源图1024×1536，输出每帧512×768、横排2048×768；单帧原生显示121.40×182.10px。头部/身体实测与投影口径见[measurement-method.json](measurement-method.json)和[poses.json](poses.json)。

```sh
python3 art/design/character-motion/adult-standard-v1/hoe-west-proof-v1/revisions/v2/register_sources.py
python3 art/design/character-motion/adult-standard-v1/hoe-west-proof-v1/revisions/v2/build_review.py
python3 art/design/character-motion/adult-standard-v1/hoe-west-proof-v1/revisions/v2/validate_artifacts.py
```

结构RGBA/尺寸/哈希检查通过，边界检查失败；HTML JavaScript语法已检查。未启动GUI，未借用旧版原生证据；本轮`native_checked=false`，原生由主代理统一处理。没有分层/隐藏身体/衣裤鞋换装/发帽/四向/生产或业务事务改动，未读写玩家存档、未导出、提交或推送。

实际模型为`gpt-6.1-sol high`，独立负责本目录来源、登记及测量；无嵌套代理。artifact与输入/脚本/配置哈希见[evidence/artifact-manifest.json](evidence/artifact-manifest.json)。
