> 历史制作文字记录：所述过程图片、源稿、旧版本与回执已按用户要求清理；现行资源及验证见[独立动画归档](2026-11-02-adult-v5-animation-only.md)。下文路径为历史路径，旧验收结论不作为新闭包回执。

# V5 四向农作与idle画风统一

最新：[实际最终PNG r011](../../art/characters/parts/body/adult-v5/r011/atlases/) · [严格评审suite](../../art/characters/reviews/body-pixel-v5-farming-style-r001/review.json) · [576文件冻结归档](../../art/characters/parts/body/adult-v5/archive-r008.json)。用户统一验收待定，默认游戏/现行母版仍v4。

本轮回到原任务：锄地、浇水、采收应与已认可idle的清晰像素边缘、肤色和眼部匹配。上一轮r010仅修异常整体漂移，不能当作完成画风统一。用户又指出新线条偏淡，因此明确以idle的黑色描边为准，修线宽和颗粒时不降低墨色/不透明度，不改浅棕或灰线。

内置Imagegen选用24张四向body/visible源表，更新112农作源姿态。112中采收前两帧没有道具，身体版本复用对应新visible完整姿态，未拼接局部脸手；其他身体版由新带工具姿态经Imagegen移除道具、补齐原遮挡区域。保留自然弯腰和握持、完整工具/作物/水流、原pose顺序和时长。idle/walk/run三张PNG逐字节保持，共52源姿态不变。整包仍9图集、164源姿态、24方向动作/108显示帧。

## 同倍率自验

[锄地：idle/旧/新](adult-v5-farming-style-v1/hoe-idle-before-after-1x.png) · [浇水：idle/旧/新](adult-v5-farming-style-v1/water-idle-before-after-1x.png) · [采收：idle/旧/新](adult-v5-farming-style-v1/harvest-idle-before-after-1x.png)。每格260×228，以原生贴图1倍对照，不单独缩放脸手或衣鞋。完整帧：[无工具身体](adult-v5-farming-style-v1/all-farming-body-1x.png)、[带工具显示](adult-v5-farming-style-v1/all-farming-visible-1x.png)。

旧粗黑外沿和大眼黑块已明显减轻，新稿保持清晰黑/近黑边线，皮肤回到接近idle的中性桃色。不是要求所有姿态外框总高相等，屈膝和前倾合法。西锄r001粗线、r002背景雾/棋盘、r003过淡及r004过粗均未选用，r005黑色细线作为扩量参考；被用户打断的三张早期方向尝试有两张可恢复输出，均未选入。完整记录28次可确认完成调用，另有3次被打断批次尝试，不猜第三张完成情况。提示词、全部已恢复原图、引用SHA和选择/失败范围保存在sources/adult-v5-farming-style-r001。

自动head skin CC在水北混入耳/颈，误把132–143px当颅壳宽，初稿缩小。独立人工量取源图实际颅壳横截面（约121–122px）与idle同部位49px，整张visible表统一49/122、body统一98/243重登记；不是按总高百分比或局部拉伸。其余北向没有同类证据，不强行改高度。注册记录registration-r005、packing-r005；未选登记草稿保留coastal临时诊断。

[独立静态报告](adult-v5-farming-style-v1/independent-style-review.json)确认修正后的颅壳密度、黑线、眼部和桃色肤色，当前静态范围未发现其他必须重绘项；不授动态或用户认可。复用farm_body_art做独立只读视觉审查，主代理同时准备严格构建。子代理仅能确认Codex，精确模型ID未暴露，未猜填。

## 构建与验证

最终图片实际归parts/body/adult-v5/r011，canonical模板与两套严格构建另保留技术用途，沿同一统一模型；未建立第二条合成/播放管线。pack、两套108帧build及suite preflight通过。初次配方迁移残留旧prepared引用被preflight拦下，已改为结构化绑定当前source bundle后重新构建；错误构建未作通过证据。未改变冻结引擎脚本、运行基线或v4资源。

原生复验与全库验证已完成：490人物测试通过（534.549s），门禁75严格配方/69严格构建/9旧配方/2既有接入通过。原生逐姿态/十循环1854项、824图，96切换595项通过；两份独立回执通过，绑定772/778输入。108实际GPU姿态619987高alpha像素在同一2倍显示和[-26,-2]原点下全部匹配（色差仅取理论alpha合成/取整界，不允许几何位移）；实际idle↔农事与连续画面已目视检查。首轮native poses-r002只有walk-east_returns_matching_idle失败（旧walk/run PNG本轮未变），报告保留；所有新农事姿态检查通过，不能以此把全轮记为通过。复验使用同一实际suite、同一observer/validator和真实时钟，仅把显示max-fps60改30以减轻时序/输入采样不稳定，证据新建poses/transitions-r003，不改物理时钟、动作时序或验收条件。原始证据在/private/tmp/coastal-v5-farming-style-{poses,transitions}-r003；首轮失败摘要保存在first-native-attempt-failed.json。

严格世界接触、动态换装和生产发布不在本轮通过范围；未提交、推送或导出。

[原生idle/旧/新对照](adult-v5-farming-style-v1/native-idle-before-after.png) · [验证摘要](adult-v5-farming-style-v1/summary.json) · [原生像素匹配](adult-v5-farming-style-v1/native-pixel-registration.json) · [首轮失败记录](adult-v5-farming-style-v1/first-native-attempt-failed.json)。新r011评审窗口供统一验收。
