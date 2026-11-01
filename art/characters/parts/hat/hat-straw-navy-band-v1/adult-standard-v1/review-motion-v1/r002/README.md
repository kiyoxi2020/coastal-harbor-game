# 南向真实帽atlas组件候选

[views.json](views.json)只登记`water_south_B_ready`真实南正面帽。完整raw1774×887来源沿用既有`motion-headwear-sampling-v1-9f06fab9`包，未把派生registered PNG冒充GPT源。

[atlas登记证据](metadata/atlas-registration.json)保存既有local768²ownership及原注册元数据的路径/SHA。完整raw按1536/887、同轴NEAREST仿射到3072×1536；local ownership嵌入[0,768]，真实atlas耳锚[142,1304]到canonical[533,729]，整源整数平移[391,-575]。atlas使用image origin[0,0]，不伪造actor world root；canonical pose保留真实canvas/root。

本投影完整真实帽只需near，含前冠、前帽檐及两侧underside，所有真实ownership保留。无单独rear表面，因此不造空far；此结论不推广到其他投影。

最终`RegisteredAdaptations.component`从完整raw atlas重建并严格核RGBA，与旧真实帽逐RGBA相同。发帽组合及工具/依赖证据在hair `r002/evidence/reconstruction.json`。本目录是单pose review候选，无完整clip、Godot动态、用户认可或发布能力声明。
