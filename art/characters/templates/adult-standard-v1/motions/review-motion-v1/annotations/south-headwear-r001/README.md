# 南向头部独立annotation候选

本sidecar只绑定canonical `water/r001/south/poses.json`的真实variant B、`water_south_B_ready`完整帧及其SHA、1536×1920画布、root[768,1600]与既有显示尺度；不修改canonical pose或衣装annotation。

`r004-hair-source`保存生成完整源归一后的实测耳中点[765,730]，`canonical-head-target`保存父底图取整登记点[768,729]与真实左耳[533,729]。source/target pose身份均保持真实water_south_B_ready，没有把静态源改名成别的动作。

`head`是人工限定头区内的真实canonical alpha支撑，layer_id=`base`用于统一registered-head接口；不是target erase或occlusion。实际原脸耳由父底图提供，生成source的reference_frame绑定表示同pose的canonical参考，不表示生成身体RGBA等于canonical身体。原始测量与取整残差见新hair source包metadata。
