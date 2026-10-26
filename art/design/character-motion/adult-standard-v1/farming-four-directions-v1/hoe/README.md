# 锄地四向短长袖固定外观候选

范围：hoe × west/east/south/north × A奶油短袖/B蓝色长袖，ready/lift/contact/recovery四姿态，各180/220/140/260ms，共800ms。每组位于direction-garment/candidate.json；只有实际产出的完整组可加载，不能借旧模型或镜像填缺资源。

每源1024×1536；统一registered1536×1792，root[768,1544]、display_scale138/1164、source_density_scale_vs_idle2。源全RGBA仅整帧整数平移；所有源、prompt、失败稿与配置保留。西A直接无损复用已认可v4完整四帧；西B继承先前两真实关键姿态并补两个GPT完整姿态。其余三方向独立GPT生成，B按同姿态上衣编辑；没有脚本绘制、局部缩放、挪鞋、脸手拆贴或镜像造方向。

每组evidence/four-poses-2x.png为1个动作四姿态的明暗nearest参考板。此Pillow派生板仅供制作目视；原生播放与控制证据由主代理外部绑定最终candidate哈希。各组candidate.native_checked保持false，避免外部证据写回候选造成哈希循环。

本次只声明完整穿衣固定A/B外观序列，不声明独立衣身/袖子、隐藏人体、裤鞋发帽混搭或阶段4/5/6完成。姿态、脚/握点按可见表面人工观察；遮住的解剖关节明确null；未冻结精确轨迹与工具刚性验收。

复现单组：`python3 register_clip.py west-A`（从本目录运行），校验所有八组：`python3 test_candidates.py`。最终范围/哈希/测试与局限见implementation-report.md与clip-index.json。
