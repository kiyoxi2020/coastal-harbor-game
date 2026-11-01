# 当前身体材质点的原生像素量测

目标：复用既有contact_evidence/native_raster，为当前严格schema3 body-only包提供源点与实际GPU截图对应；不把像素对应改称脚底支撑、掌心接触或合法地面证明。

- 先写body-only静态/原生反例测试：接受真实body槽，拒绝未声明的衣鞋层、源/坐标/输出篡改、假原生输入；保留旧头部+衣装检查。
- contact_evidence最小扩展到schema3且只选body槽的包；无头部留边/遮挡，不伪造head配方。不自动增加鞋coverage，不跳过鞋检查；请求鞋检查必须明确拒绝无鞋包。
- 新增通用body_native.py准备和复核捕获前冻结输入。使用现有strict build.verify，绑定实际manifest/recipe/PNG/几何、材质点、观察器及场景资源闭包。拒绝目录覆盖和源码变化。
- 通用Godot静态观察器加载当前严格PNG，复用原walk_trial场景及只改变初始化的test fixture；不再实现角色或动画时钟。报告明确为source-pose静态材质点采样，不冒充实际移动或接触。像素图先暂存，采样后保存。
- 从真实源图定位可见下缘材质点，记录确切RGBA、atlas原坐标/整格裁取关系和41×41固定ROI；候选定位只辅助材质点，不作为解剖脚位、mask归属或支撑窗口。源不可观测部位明确未验证。
- 实际原生采集后沿同一native_raster量测，不移动源点/ROI/根点、不调容差；记录所有最优偏移是否≤1屏幕像素与RGB界。失败先调查证据，不能事后放宽。
- 人物单元测试/check及当前包build.verify通过后记录结果。身体归档仍须物理支撑/接触与完整时序等独立门禁，不开始衣物。
