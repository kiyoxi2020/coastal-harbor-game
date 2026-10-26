# 锄地八组固定A/B序列实施报告

已完成本次hoe × 四方向 × A/B共8组、32个真实不同完整姿态，供主代理统一24组隔离试玩集成；未以两姿态或首组停工。各组ready/lift/contact/recovery为180/220/140/260ms，共800ms。西A原认可v4的源RGBA、整帧位置及时间不变；西B无损复用此前ready/contact并以GPT补lift/recovery；东/南/北独立生成A完整动作，再逐姿态GPT编辑蓝色长袖B，没有镜像方向。

| 组 | candidate | SHA256 |
|---|---|---|
| west A | [west-A/candidate.json](west-A/candidate.json) | `f7b0c8638777c9bc042eb82d3b85b1f45e67054d20ce10256abd13519f624a48` |
| west B | [west-B/candidate.json](west-B/candidate.json) | `5c15bd950e3557beb08b8a612f7866daa2a1b7627a1e5971f97c5667abd746c9` |
| east A | [east-A/candidate.json](east-A/candidate.json) | `4ebe3fafadd609cb1577dd52f2ef25adf2635467ddc7ef076071efa61af5697b` |
| east B | [east-B/candidate.json](east-B/candidate.json) | `ca529f38594d211a01b93a130823c3d35c49977242c566963a240b9baeab9b26` |
| south A | [south-A/candidate.json](south-A/candidate.json) | `5362bbdf4293b5677d1332caabbd9584a63458b2998f3d62d8ef75a61c528f5c` |
| south B | [south-B/candidate.json](south-B/candidate.json) | `93566b64871cd1934329a33e14fcbeb1d4c60d634f90cc10a844366e52e2f537` |
| north A | [north-A/candidate.json](north-A/candidate.json) | `19733bc62e655feb1a27e8db901597d80eeff0372b1eb52935bc219cbf0c4b92` |
| north B | [north-B/candidate.json](north-B/candidate.json) | `a3e4f22b650cd93bbf87d4264e5d2e37cbc6a89bb5a654c6bd0dd22e74762149` |

统一完整源1024×1536；registered1536×1792、root[768,1544]、source_density_scale_vs_idle2、display_scale138/1164。1x画布182.10×212.45屏幕像素；2x364.21×424.91。没有预缩小源图或上采样；所有源RGBA仅整帧整数平移，未知隐藏髋/膝/踝及遮住的握端为null，长袖遮住的腕关节与可见袖口表面另记。根点来自可见脚底口径，是作者登记，不是已批准支撑轨迹。

6项整体测试通过，验证实际八candidate、32个不同RGBA、真实源分辨率/整帧保真、source及全部inputs哈希/digest、缺方向/衣服/源及重复像素拒绝、背景透明度。最初缺实现失败测试及east recovery alpha失败测试保留；最后完整运行6项、2.406秒、OK记录见validation.json。8组明暗四停帧板均已逐组目视，32姿态有独立动作投影与锄的准备/抬起/接触/收回意义；全板没有保留alpha矩形噪声。Pillow板仅制作观察，Godot原生、连续十次/世界衔接等由主代理外部证据绑定冻结candidate；所有native_checked保持false，避免回写改哈希。

保留全部GPT原图、prompt与失败稿。东A四格请求2048×3072实际返回1024×1536，不能当2倍密度，因此拒绝并改逐帧1024×1536；不继续同法四格重试。东A recovery原稿有背景alpha污染，先失败测试/明暗板定位，后只用GPT背景提取修复，原稿和失败板保留；最终alpha0四角与透明外部通过。一次南B contact在源未持久化前派发，无成功输出，记录后仅在源存在时重派；不把无输出当成功图。

新方向头框与投影、足迹仍是待原生评审数据：东A/B约416–435×399–431、南A/B约489–504×451–481、北A/B约420–459×359–408源像素；北向弯腰会投影缩短。西A头框约464–474×476–487，西B contact透明修复稿约482×495。没有通过局部缩头/拉腿/挪鞋强求数值一致，未把这些量测冒称用户认可、工具刚性或严格≤1屏幕像素接触通过。每帧观察与不确定度见各measurements/poses/config。

本次是完整穿衣固定A/B外观候选，modular=false；没有独立衣身/袖子/隐藏人体、裤鞋发帽8配方动态组合或生产迁移结论。新目录之外的认可素材、共享Godot/catalog/docs未改，未提交/推送/导出，未用玩家档。无当前美术源交付阻塞；后续集成/原生/用户验收由主代理继续。

实际子代理调用：model=gpt-6.1-sol、reasoning_effort=high、fork_turns=none；职责是可独立交付的hoe八组源/登记/测量/结构检查，未嵌套。图像使用imagegen技能内置GPT工具，精确生图模型标识工具未返回，不从代理模型推断。
