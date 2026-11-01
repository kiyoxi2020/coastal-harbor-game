# 当前身体的严格构建与实际世界观察

Q19认可的原始图集像素未改。候选后继`adult-standard-v2`仍属于`unified-composable-character-v1`，沿同一人物规范/构建器登记`body-motion-v1`，不修改旧template、catalog、生产、发布清单或runtime-baseline。

164完整源格精确提取为canonical参考，无重绘、重缩放、挪肢体或改alpha。不可变来源`sources/visible-atlas-packed-r001`含Q19准备图集的逐字节副本、原计划/工具身份和提取映射。`adult-standard-v2-visible`及`adult-standard-v2-body-reference`两配方通过既有schema3 build/verify，各108帧；前者农事保留工具，后者用于无工具身体参考，两者不宣称可像素分离/换装兼容。两份构建始终review-only。

实际原生观察读取这次严格构建的真实PNG，逐文件SHA和实际RGBA在创建GPU纹理前核对，沿用character_walk_trial的运动/位移时钟/物理及农事状态机。临时fixture只替换初始化和纹理供给，未实现第二个角色控制器；actor场景、地形/树/柜台/门和物理不改。旧相对密度农事API有显式单位转换记录，真实源像素/world比为.25、相机4倍，进入/退出动作后尺度与根点恢复核对。

| 项目 | 已观察结果 | 不外推的结论 |
|---|---|---|
| 四向走/跑 | 8段各超过10实际世界周期，6姿态全覆盖，当前严格纹理，松键回idle | 不等于已量测足底支撑/滑步 |
| 走跑/转向 | 5个真实控制切换及最终idle记录正确 | 未覆盖全部低FPS/暂停/重播事件原子性 |
| 三农事×四向 | 每段10次，共120次，各次全部姿态；动作中位置固定/方向锁定，结束回idle并恢复尺度/根点 | 无农事事务/真实存档或游戏目标入账修改；不能推断工具接触合法地面 |
| 真实港口 | 绕树/柜台8路点与门0/1阻挡、2通行通过；补充树/柜台前后含工具截图 | 路点1.3world到达容差不是接触1px标准；不代表全部空间/生产门shader已验收 |
| 资源/回归 | canonical164格RGBA相等；389测试，check55严格配方/49构建/9冻结legacy通过；原生无ERROR/WARNING | 不授予衣物混搭、生产或最终归档 |

旧首轮同步PNG保存造成70ms触地帧漏采；采用GPU截图先留内存、十实例结束再写盘后，当前严格输出的120实例及空间动作均观察到完整阶段。未把漏采当作源动画错误。输入始终按真实状态机锁定；结束后仍按住方向可正常恢复移动，统计动作中固定位置而不是把动作后的移动当成锁定失败。

当前观察路径在`/private/tmp/coastal-visible-atlas-body-r001/native-strict-body-world-r001`、`native-strict-body-farm-spatial-r001`、`native-strict-body-spatial-detail-r001`。录像是实际截图按physics-frame间隔回放，不是逐绘制帧的全量连续录像。移动报告为等待physics+draw后的真实快照，不冒充完整逐物理tick账本。观察结束审计760实际输入/资源闭包与代码哈希，当前严格PNG在加载时已核验；该审计不是现有all-actions-suite的捕获前冻结合同或正式原生回执。

现有contact_evidence目前只接受schema2头部＋schema3基础及鞋coverage。不能拿它给body-only/赤脚/未观测掌心或北向隐藏锄刃制造通过回执。下一步沿该工具最小扩展到body-only实际材质点，冻结源关节/支撑窗口和工具/地面目标的可观测范围，再量测；必要时在现有通用观察入口收敛临时fixture。相对批准姿态≤1屏幕像素目标保持，不事后放宽。暂未根据固定帧脚点随角色平移的现象断言已证明物理滑步，须先定义真实支撑阶段。

Progress Q20只询问当前真实世界的显示效果，严格接触、完整动态和最终身体归档仍未完成；不启动衣物A/B，不推送/导出/切生产。
