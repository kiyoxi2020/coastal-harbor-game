# 四向行走与站姿评审候选

本轮承接用户“ok 速度可以，继续”：保留75%播放速度，54世界单位/秒；支持四向walk各4帧、四向idle各1帧，以及奶油短袖A/蓝色长袖B。两套上衣共享同姿态身体，裤鞋固定。本目录是同一人体管线的增量动作集，生产主角尚未迁移。2026-10-25用户以“没有问题，继续执行”认可当前试玩，记录见[视觉认可](visual-acceptance.json)。

入口：[港口试玩](launch-game-trial.command)、[左右同步对照](symmetry-review.html)、[双套上衣评审页](review.html)。试玩用WASD/方向键移动、1/2换衣、R回起点；停止显示同朝向站姿，斜向速度归一化，转向和换衣保留动作相位。默认75%，可调50%–100%。入口复用真实港口地形、碰撞、深度排序和镜头，没有存档服务。

## 来源与坐标

GPT built-in image_gen生成/定点编辑，所有提示词在[prompts](prompts)，完整源图及来源哈希在[sources](sources)。西向walk复用前一轮小样部件；其余方向从同一成年母版扩展。2026-10-25根据左右动作不对称反馈，东向walk四帧改用GPT v5：以西向各帧为对应姿态参考，统一步幅、后收腿与近侧摆臂相位；整帧(-8,0)注册，B及隐藏衣身遵循同一整帧变换，不使用运行时镜像。原v2/v3右行姿态退为历史；新增姿态仅去除经检查的独立背景alpha噪点，完整主体保留原alpha及2px边缘，原图保留。

每姿态源画布512×768、根点[256,708]，nearest过滤；世界统一缩放138/582/4、镜头4倍，源图582px人物约显示138渲染像素。Retina实际窗口物理显示尺寸取决于窗口缩放。没有单独挪动、缩放衣物或鞋子。整帧注册见[registration.json](registered/registration.json)。

完整无臂衣身分别保留站姿与各行走姿态源，不能把站姿较低衣摆直接套到步行上；两袖、衣物覆盖目标与前后层序按实际姿态登记。颜色提取只在人工语义区域内执行，B源仅提供衣物，脸手及裤鞋仍取A身体。

## 验证与边界

2026-10-25最终候选artifact：`166c5a0da9249a8da537e86406b12f3889ace5fa150aefc854265608703bd603`。18项分层/注册/对称检查、20项合成器回归、43项原生港口检查通过。已检查40个原生停帧；归档719个连续样本、8段各十循环视频，以及明暗10张诊断板（80个姿态视图）。详见[验证记录](evidence/validation.json)与[证据清单](evidence/summary.json)。明暗板使用原生窗口左上1280×720诊断区域，其余区域仍为港口。

请使用本目录启动器：它显式选择新动作集；直接运行旧体验场景的默认资源仍为历史西向小样。


实际烘焙、自动验证和原生截图/录像结果见[evidence](evidence)；验收绑定实际artifact_digest与源图/脚本/配置哈希。左右对照采用实际west/east纹理与相同近侧相位，细小绘制差异不等于逐像素镜像。原生连续录像为固定世界位置的真实时间播放；港口按键测试另行验证位移、碰撞与停止。两类证据均不能代替严格的支撑脚锁定测量。

[速度认可](speed-acceptance.json)是此前记录；本轮新增[视觉认可](visual-acceptance.json)覆盖当前四向步态、站姿与两套上衣，不扩大为完整人体发布认可。[poses.json](poses.json)记录实际源图人工观察坐标和未冻结项，未知的隐藏关节明确留空；完整关节/接触事件合同与相对批准轨迹的≤1屏幕像素误差尚未通过。新增[接触基线](contact-baseline.json)与[384样本原生测量](evidence/contact-audit-v1/README.md)：帧内相对地面滑动约21.6像素，属于独立锁脚诊断，不能冒充规范中的轨迹误差。

尚未完成run/hoe/water/harvest、动态裤鞋8配方、发帽条件、其他体型及生产迁移。不得把本轮40张合成结果或加载成功称为完整动态可组合人体。未使用玩家存档；未导出、提交或推送。

## 复现

```sh
ROOT=art/design/character-motion/adult-standard-v1/locomotion-v1
python3 "$ROOT/register_sources.py"
python3 "$ROOT/register_pose_observations.py"
python3 "$ROOT/build_parts.py"
python3 -m unittest discover -s "$ROOT" -p 'test_*.py'
python3 "$ROOT/build_review.py"
python3 "$ROOT/build_symmetry_review.py"
"$ROOT/launch-game-trial.command"
```

开发分工：主代理负责GPT源、整帧注册、姿态观察、评审/原生证据与整合；复用gpt-6.1-sol high代理负责既有合成器schema2、四向试玩控制及分层提取。任务按文件独立，避免共同改写同一脚本。
