# 西walk独立实际pose annotation

只绑定canonical west walk4与idle_west_0的variant B、实际帧文件/SHA、512×768、root[256,708]、display_scale138/582与真实时序。没有修改canonical r001或其他南向annotation。

frame_root是冻结完整帧坐标，用于已有源的零位移整体注册；不是从生成脚底重新估计。head_ear的源idle为[292,282]，四walk为[293,281]、[293,281]、[292,281]、[294,281]。实际耳/眼/颅顶测量和投影残差来自冻结readiness证据，保存于sources/west-walk-r001/metadata/provenance.json。

pants/shoes surface只继承有限canonical可见衣面；top surface为有限真实衣料可作用范围，四walk明确排除原body_arm在实际B hide-mask外、且未被后续衣身/袖子实际强paint遮住的可见原手/前景。该区域只限制材料覆盖，不创建隐藏body或复制脸手。head surface供同一registered-head base接口，非erase/occlusion。两类layer_id分别body/base，以实际统一合同使用。
