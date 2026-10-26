# 南向浇水 A：两关键姿态候选

[逐帧审阅：明暗1×/2×](review.html) · [实施报告](implementation-report.md) · [真实量测](measurements.json)

ready-v1 / pour-v2，完整壶与水流。共同1280×1728画布、根[640,1480]、scale0.1185567010，仅整数整帧注册。首轮pour-v1因跨帧投影漂移退回，源图/提示词/诊断保留。

4项结构检查通过；未运行原生世界，未验证完整动作、精确脚点/握点、工具刚性、隐藏身体、分层、换装或用户认可。不可据此扩量或进入发布清单。头部投影差异详见报告。主代理将独立原生审查。

重建：先运行measure_candidate.py，再build_candidate.py，最后test_candidate.py。所有来源、提示词、实际尺寸和配置工具哈希见candidate.json/source-manifest.json。

## 主代理补充的原生静态诊断（2026-10-26）

[Godot明暗1x/2x板](evidence/native-static/native-board.png)及[输入绑定报告](evidence/native-static/report.json)已完成，8项检查通过，参照由认可locomotion清单按同向同上衣自动解析。主代理已目视完整姿态、透明度和源密度；这是静态诊断，不是连续动作、精确接触、独立衣物组合或用户认可。candidate仍保留制作时native_checked=false，以此独立报告解释新增范围。
