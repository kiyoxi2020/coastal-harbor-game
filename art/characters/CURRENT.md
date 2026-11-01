## 2026-11-01 像素风试验关闭

用户选择保留当前原始人物方案：默认游戏继续使用 `adult-standard-v2-visible-r001` 原帧。单帧与六帧imagegen像素风结果均仅预览、未采用，未替换资源或变更发布状态。

# 当前人物与衣物入口

## 默认游戏主角（2026-11-01，Q22=A）

正常游戏入口现用最新归档的灰色连体底衣身体，`adult-standard-v2-visible-r001`共24动作方向108帧，农事带工具。运行包：[本地接入清单](../../godot2d/assets/characters/integrations/adult-standard-v2-visible-r001/manifest.json)；来源：[严格构建](builds/adult-standard-v2-visible-r001/manifest.json)与[身体源归档](parts/body/adult-v1/archive-r001.json)。

这是默认玩家的本地开发接入，旧餐馆NPC暂留；完整统一发布、精确接触及动态换装仍待完成。下文是独立的固定发帽评审入口，不是当前默认游戏主角。

## 当前可试玩人物

固定top03条纹上衣／原裤鞋／栗短发＋草帽，四向idle、walk、run、hoe、water、harvest，共24格84姿态。仍为review-only，正式游戏生产人物不变。

- 启动：`python3 tools/characters/review.py all-actions-construction`。
- [统一配方](recipes/adult-top03-full-hair-hat/r001.json)／[当前构建绑定](reviews/all-actions-construction/review.json)。
- [上衣](parts/top/top03/)／[裤](parts/pants/original-pants/)／[鞋](parts/shoes/original-shoes/)／[发](parts/hair/hair-chestnut-short-v1/)／[帽](parts/hat/hat-straw-navy-band-v1/)。

## 衣柜索引

下面的“静态候选”仅表示来源目录，不能当作四向完整动作兼容。运动能力以实际配方和[coverage](coverage.json)为准。

| 部位 | 稳定ID | 名称 | 静态状态 |
|---|---|---|---|
| hair | [hair-chestnut-short-v1](parts/hair/hair-chestnut-short-v1/) | hair-chestnut-short-v1 | not-listed |
| hair | [hair01](parts/hair/hair01/) | 栗色短碎发 | candidate |
| hair | [hair02](parts/hair/hair02/) | 深棕侧分短发 | candidate |
| hair | [hair03](parts/hair/hair03/) | 炭黑平头 | candidate |
| hair | [hair04](parts/hair/hair04/) | 深棕卷发短帽形 | candidate |
| hair | [hair05](parts/hair/hair05/) | 银灰后梳短发 | candidate |
| hair | [hair06](parts/hair/hair06/) | 黑色短莫西干 | candidate |
| hair | [hair07](parts/hair/hair07/) | 栗棕齐刘海短发 | candidate |
| hair | [hair08](parts/hair/hair08/) | 深蓝黑波浪短发 | candidate |
| hair | [hair09](parts/hair/hair09/) | 银白稀疏短发 | candidate |
| hair | [hair10](parts/hair/hair10/) | 深棕低小发髻 | candidate |
| hat | [hat-straw-navy-band-v1](parts/hat/hat-straw-navy-band-v1/) | hat-straw-navy-band-v1 | not-listed |
| hat | [hat01](parts/hat/hat01/) | 海蓝帽带草帽 | candidate |
| hat | [hat02](parts/hat/hat02/) | 海军短檐工作帽 | candidate |
| hat | [hat03](parts/hat/hat03/) | 橄榄绿渔夫帽 | candidate |
| hat | [hat04](parts/hat/hat04/) | 深蓝船长帽 | candidate |
| hat | [hat05](parts/hat/hat05/) | 米白水手帽 | candidate |
| hat | [hat06](parts/hat/hat06/) | 砖红针织便帽 | candidate |
| hat | [hat07](parts/hat/hat07/) | 炭灰羊毛贝雷帽 | candidate |
| hat | [hat08](parts/hat/hat08/) | 深蓝扎头巾 | candidate |
| hat | [hat09](parts/hat/hat09/) | 棕色短檐呢帽 | candidate |
| hat | [hat10](parts/hat/hat10/) | 米灰软呢报童帽 | candidate |
| pants | [original-olive-pants-v1](parts/pants/original-olive-pants-v1/) | original-olive-pants-v1 | not-listed |
| pants | [original-pants](parts/pants/original-pants/) | original-pants | not-listed |
| pants | [pants01](parts/pants/pants01/) | 橄榄棕直筒长裤 | candidate |
| pants | [pants02](parts/pants/pants02/) | 深蓝直筒牛仔裤 | candidate |
| pants | [pants03](parts/pants/pants03/) | 炭灰翻边长裤 | candidate |
| pants | [pants04](parts/pants/pants04/) | 森林绿工装长裤 | candidate |
| pants | [pants05](parts/pants/pants05/) | 蓝灰百褶短裤 | candidate |
| pants | [pants06](parts/pants/pants06/) | 酒红七分裤 | candidate |
| pants | [pants07](parts/pants/pants07/) | 深蓝及膝百褶裙 | candidate |
| pants | [pants08](parts/pants/pants08/) | 青灰小腿裹裙 | candidate |
| pants | [pants09](parts/pants/pants09/) | 深紫收脚长裤 | candidate |
| pants | [pants10](parts/pants/pants10/) | 黑灰细格纹长裤 | candidate |
| shoes | [original-brown-shoes-v1](parts/shoes/original-brown-shoes-v1/) | original-brown-shoes-v1 | not-listed |
| shoes | [original-shoes](parts/shoes/original-shoes/) | original-shoes | not-listed |
| shoes | [shoes01](parts/shoes/shoes01/) | 棕色系带低帮皮鞋 | candidate |
| shoes | [shoes02](parts/shoes/shoes02/) | 靛蓝帆布系带鞋 | candidate |
| shoes | [shoes03](parts/shoes/shoes03/) | 炭灰便士乐福鞋 | candidate |
| shoes | [shoes04](parts/shoes/shoes04/) | 棕色搭扣鞋 | candidate |
| shoes | [shoes05](parts/shoes/shoes05/) | 青绿短雨靴 | candidate |
| shoes | [shoes06](parts/shoes/shoes06/) | 米白低帮运动鞋 | candidate |
| shoes | [shoes07](parts/shoes/shoes07/) | 酒红玛丽珍鞋 | candidate |
| shoes | [shoes08](parts/shoes/shoes08/) | 灰色毛毡便鞋 | candidate |
| shoes | [shoes09](parts/shoes/shoes09/) | 深棕短工靴 | candidate |
| shoes | [shoes10](parts/shoes/shoes10/) | 黑色系带布鞋 | candidate |
| top | [original-blue-long-sleeve](parts/top/original-blue-long-sleeve/) | original-blue-long-sleeve | not-listed |
| top | [top01](parts/top/top01/) | 蓝色卷袖工作衫 | candidate |
| top | [top02](parts/top/top02/) | 苔绿针织开衫 | candidate |
| top | [top03](parts/top/top03/) | 海军条纹套头衫 | candidate |
| top | [top04](parts/top/top04/) | 砖红绳纹毛衣 | candidate |
| top | [top05](parts/top/top05/) | 浅灰双袋工装衫 | candidate |
| top | [top06](parts/top/top06/) | 深蓝小翻领衬衫 | candidate |
| top | [top07](parts/top/top07/) | 紫灰女式圆领衫 | candidate |
| top | [top08](parts/top/top08/) | 棕色马甲内搭套装 | candidate |
| top | [top09](parts/top/top09/) | 蓝绿半拉链运动衫 | candidate |
| top | [top10](parts/top/top10/) | 炭灰渔夫套头衫 | candidate |

## 维护边界

`sources`与`templates`是源与身体接口，`recipes`定义实际组合，`builds`是加载所需输出；部分局部构建同时也是完整配方的来源，不能按“不是当前主人公”删除。历史展示材料按用户要求精简；原始回执只解释历史范围。
