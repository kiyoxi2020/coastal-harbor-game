> 历史制作文字记录：所述过程图片、源稿、旧版本与回执已按用户要求清理；现行资源及验证见[独立动画归档](2026-11-02-adult-v5-animation-only.md)。下文路径为历史路径，旧验收结论不作为新闭包回执。

# V5 walk/run 横漂修正

最新候选：[r008最终PNG](../../art/characters/parts/body/adult-v5/r008/atlases/)，[严格评审绑定](../../art/characters/reviews/body-pixel-v5-drift-r001/review.json)。未更换v4游戏和母版；待用户视觉验收。

源登记误把摆动脚位置用作列距，东向run首行610源像素导致人物大幅横跳。改为每行固定源根点和列距，头/颈稳定区结合v4同姿态合法倾斜作为登记参考，独立躯干复查。无逐帧运行时偏移、部件挪缩、程序改色或重绘。43/48运动源帧的水平登记变化，原图、整帧缩放、裁区、Y位置、duration全部保持。

|固定根点头部横向范围（px）|旧r007|新r008|
|---|---:|---:|
|西向walk|17.5|1.5|
|东向run|38|4.5|
|南向walk|14|0|
|南向run|9|1|

[固定根点逐帧对照](adult-v5-motion-drift-v1/fixed-root-before-after.png) · [测量](adult-v5-motion-drift-v1/geometry-before-after.json)。该皮肤连通域头部测量仅诊断图像稳定性，不是关节、ownership或物理接触证明。旧原生绑定/时钟检查未覆盖此几何缺陷；不能因其通过就视为运动美术通过。

最终图片仍为parts/body，源登记新增registration-r003与packing/r003，统一模型新模板adult-standard-v5-r005、visible/body-reference配方和构建r005。archive-r005冻结469文件；v4归档637项和旧候选494项SHA保持。idle及六农事图集PNG字节完全相同。

## 验证

两套严格build/verify通过，每套108帧；suite preflight通过。原生逐姿态/连续十循环2248项、1021张PNG通过；96切换595项通过，两份独立绑定/时钟回执均通过。实际原生面板头部横向范围35/76/28/17屏幕px降至3/9/0/2px（面板按2倍显示），第2→3帧接缝28/76/16/1降至1/4/0/0px。逐帧目视颈部、衣身、髋部连接连续，无旧整帧横推。490人物测试通过（491.421s），`python3 tools/characters/check.py`通过69严格配方/63严格构建/9旧配方/2既有接入。游戏v4场景、资源、运行基线SHA保持。未宣称严格世界接触、动态换装、农事画风已通过；未提交、推送或导出。

独立复查：复用 gpt-6.1-sol/high，只读检查源图和新输出的衣身稳定性，主代理负责登记和集成。四组衣身横向范围7/5.5/2/2 px，v4同指标5.5/6.5/2.5/1 px；衣物bbox受摆臂遮挡和投影影响，不作刚性锚。西walk衣身相对头部有合法姿态变化，未发现需重新生图的明确断裂。[独立报告](adult-v5-motion-drift-v1/independent-torso-review.json)。

[原生六帧面板](adult-v5-motion-drift-v1/native-six-frame-panels.png) · [原生几何测量](adult-v5-motion-drift-v1/native-geometry-before-after.json) · [原生摘要](adult-v5-motion-drift-v1/summary.json)。原始观察保留 `/private/tmp/coastal-v5-drift-{poses,transitions}-r001/`。评审窗口已打开新r008候选。
