> 历史制作文字记录：所述过程图片、源稿、旧版本与回执已按用户要求清理；现行资源及验证见[独立动画归档](2026-11-02-adult-v5-animation-only.md)。下文路径为历史路径，旧验收结论不作为新闭包回执。

# V5 东西向run头部横向对齐

最新：[最终PNG r009](../../art/characters/parts/body/adult-v5/r009/atlases/) · [评审suite](../../art/characters/reviews/body-pixel-v5-head-align-r001/review.json) · [469文件SHA归档](../../art/characters/parts/body/adult-v5/archive-r006.json)。待用户视觉验收。

上轮r008按原v4姿态保留的前倾横向位移仍不符合用户预期。用户明确要求“让脑袋对齐”，本轮以同方向idle头部中心为水平登记基准，登记完整人物帧，头颈和身体共同保持连接。十二帧保留原源图与完整裁区、统一整帧比例、Y登记、纵向弹跳和时序；其中十一帧X登记改变。没有局部挪动头部或补画像素，没有新Imagegen调用。其余152源姿态逐RGBA一致。

|头中心横向范围（贴图px）|r008|r009|
|---|---:|---:|
|西向run|5|0.5|
|东向run|4.5|0|

[六帧前后对照](adult-v5-run-head-align-v1/head-alignment-before-after.png) · [诊断数据](adult-v5-run-head-align-v1/geometry-before-after.json)。半像素残差来自实际头轮廓宽度奇偶及nearest像素量化；同一帧内未做头部单独变换。皮肤连通域仅辅助识别头中心，经逐帧目视确认，不作ownership或关节模型。

登记追加在style-consistency源目录的registration-r004/packing-r004，已冻结历史文件不变。新prepared source在adult-v5-run-head-align-r001；统一模型模板v5-r006、visible与body-reference配方/构建r006，每套108帧。构建过程中发现配方残留旧prepared引用，被preflight拒绝；修正后重新构建、通过preflight，错误构建移至coastal临时目录且未作为评审证据。默认v4场景/资源/运行基线不变。

## 验证

pack、两套严格build、suite preflight通过。两套build verify通过。原生逐姿态/十循环2316项、1055张PNG，以及96切换595项通过；两份独立输入/时钟回执通过，分别736/742绑定输入。实际2倍原生面板头中心范围：西10→1屏幕px、东9→0，最大相邻帧横跳也降至1/0屏幕px。逐帧目视头颈与身体完整连接；原生循环接缝无此前左右横跳。490人物测试通过（583.831s）；仓库门禁通过71严格配方/65严格构建/9旧配方/2既有接入。旧r008的通过记录不继承为新图验证；严格接触、动态换装、生产发布未授通过。未提交、推送或导出。

[实际原生六帧面板](adult-v5-run-head-align-v1/native-head-alignment.png) · [原生头中心测量](adult-v5-run-head-align-v1/native-head-alignment.json) · [验证摘要](adult-v5-run-head-align-v1/summary.json)。原始观察在 `/private/tmp/coastal-v5-head-align-{poses,transitions}-r002/`。新评审窗口已打开r009。
