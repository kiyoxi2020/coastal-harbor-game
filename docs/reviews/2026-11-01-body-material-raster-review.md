# 无发帽身体材质点的原生像素量测

本轮没有改人物像素、姿态、时序或显示尺寸。沿现有contact_evidence/native_raster增加直接schema3且仅body槽的来源路径；不伪造头部配方/留边。只测显式源材质点，不把无鞋包自动当成已过鞋coverage；请求鞋检查明确拒绝。旧schema2头部＋schema3基础路径保留。新增反例还拒绝旧头部合同冒充body源观察器。

body_native.py在原生截图前调用严格build.verify，冻结实际构建/配方/输出PNG、源点、观察器/初始化fixture、既有场景与脚本资源闭包，共760文件。计划涵盖实际108pose。verify-inputs重建整个计划与闭包，拒绝删pose/依赖后重算摘要、脚本/源点变化和覆盖旧目录。通用capture_body_raster复用原walk_trial场景及初始化fixture，不另实现人物或动画时钟；实际GPU读取严格PNG核对RGBA后按已声明几何静态摆pose，截图先留内存、采样完再保存。它不是实际移动或接触观察。

108点从已认可canonical源图的显式下缘区域定位，保存真实RGBA、prepared atlas原坐标和整格裁取关系，固定41×41ROI。颜色只辅助定位实际皮肤像素；未作正式ownership、左右脚、支撑时段、握点或地面判定。没有用native截图移动点/ROI，没有伪造北向遮挡点或隐藏掌心。原生报告/截图生成后，先复核全部冻结输入，再沿原有native_raster量测。

当前r002回执：108/108通过，未验证/不匹配0；所有最优偏移的最大值0屏幕像素，RGB误差也在原界内；原≤1px界限未改变。相应physical_contact_acceptance、support_flight_slide_acceptance、soil_or_target_acceptance、user_approval和release_eligible均为false。raster_matrix_complete只指这108个已选材质点，不是全脚表面或物理接触证明。已目视实际走路及北向浇水的320×320原生采样图。

当前证据/private/tmp/coastal-body-material-raster-r002；源点在templates/adult-standard-v2/motions/body-motion-v1/material-points/r001.json，通用代码及source.json body_material_raster_revision保留可复核依赖/摘要。初轮r001之后补充合同类型反例并重采r002，当前证据绑定最终工具代码，未改变点、ROI、容差或人物。

另从Q20真实世界快照统计同一离散pose保持期间的固定材质点平移（走3.6–14.4、跑5.4–21.6nativepx），仅为运动形式观察，没有指定真实支撑阶段，因此不能写成滑步失败，也不能用源像素匹配结果抹去物理量测缺口。Q20视觉认可保留。

Q21给出具体归档方案：A将当前已认可/可重建身体 SOURCE归档并允许衣物方法A/B实验，严格物理接触留待集成独立验证；B保留原来严格接触先过的前置。A必须有用户明确决定，不自行把未验证项目移出门禁或写成通过。详情见同日body-archive-scope-proposal.md/JSON。在回答之前，完整归档和衣物A/B均保持关闭。
