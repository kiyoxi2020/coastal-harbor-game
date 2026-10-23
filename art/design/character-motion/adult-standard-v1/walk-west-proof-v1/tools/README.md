# 西向四帧合成工具（未完成原生评审）

`compose.py`读取motion.json，用整数平移、目标层mask和alpha合成烘焙四帧A/B；不生成、缩放或修补人体。`timeline.gd`提供共享时钟帧索引。当前没有review.gd/review.tscn或原生录像工具，project.godot没有启动场景；不得将工具测试当成动态美术验收。

在项目根目录运行：

```sh
python3 -m unittest discover -s art/design/character-motion/adult-standard-v1/walk-west-proof-v1/tools -p 'test_*.py' -v
python3 art/design/character-motion/adult-standard-v1/walk-west-proof-v1/tools/compose.py --motion /absolute/path/to/motion.json
```

输入样例见test_compose.py：schema_version=1，canvas_px=[512,768]、root_anchor=[256,708]、display_scale=0.2371134；frames为walk_w_0到walk_w_3及各自duration_ms；recipes为A/B，逐帧layers按后到前排列。每层id/source/offset_px，hide_mask可选；相对PNG路径，mask为整画布L模式，白色仅隐藏目标层。输出默认baked及输入/脚本/输出散列清单。尚无可交付的实际美术motion.json。

Godot时间轴检查使用本机Godot可执行文件，参数`--headless --path <本tools绝对目录> --log-file /private/tmp/coastal-motion-timeline.log --script res://test_timeline.gd`。工具不访问user://，fixture由Python测试写入临时目录。原生评审待实现，测试项目不设伪装成/private/tmp的相对user目录。

2026-10-23：15项合成测试及时间轴边界检查通过。此合同仅限当前四帧小样，生产扩展遵循统一人物管线。

运行边界：Godot启动自身会尝试创建默认工具user数据目录，在当前沙箱中被拒绝并报错；上述时间轴脚本仍执行通过，脚本不读取或写入存档。当前不将该结果称为原生启动验收。
