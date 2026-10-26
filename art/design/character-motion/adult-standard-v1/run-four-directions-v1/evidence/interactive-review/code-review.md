# 走跑换衣对照面板窄只读复查

2026-10-25。范围：character_motion_review.gd/.tscn、character_walk_trial.gd/.tscn面板绑定/C开关/--trial-review接入、四向launcher。未实现、未改项目文件、未重跑测试、未GUI；主代理提供36项真实资源headless已过与原生进行中的背景。

## 实质发现（修复前）

P2：下拉菜单键盘导航可能同时驱动世界角色。character_walk_trial.gd:393–416每物理帧直接读取Input.get_vector，并修改facing、actor位置和phase；新OptionButton也使用同一组物理方向键。UI接受事件并不能使这条全局轮询路径自然消失。原生choose()恰好用physical KEY_DOWN导航，旧测试在选择前后没有比较世界actor/phase/facing，而headless选择是直接调用select_clip且关闭physics，不能覆盖这条实际输入链。建议只在评审Popup可见期间阻止世界移动，面板普通显示时仍允许WASD/Shift；补真实Popup导航前后三项不变的原生检查。已发主代理，主代理确认纳入修复。

主代理另提供原生实证：TextureRect受像素对齐后变为122×183，相比静态121.402×182.103产生尺度误差，将改固定scale的Sprite2D。这是主代理原生发现，不冒称本复查独立测得。旧headless只比较两侧尺寸相等，不能证明实际显示倍率；新版应保留原生实际变换倍率检查。

## 其余静态核对

- 缺B组合：每次refresh先清空实际纹理，再从同衣同向idle取参照；选定动作若能力缺失，动作纹理保持null并显示明确提示，无A或其他方向fallback。合法idle参照保留符合当前测试合同。
- 独立相位：preview_phase_ms仅在面板本地推进/选择/逐帧，不写trial.phase_ms、facing、current_action或actor；隐藏时不推进，C重绑只刷新，不重置相位。
- 暂停换衣：paused仍每process刷新真实trial.garment，保持同preview_phase_ms；合法换衣显示对应同帧，缺动作清空。step先暂停，再跳到下一姿态起始累计时长，支持非均匀时长并回绕。
- UI绑定：Direction/Action下标与枚举一致；Play/Next/Review按钮路径对应场景节点，C/flag/launcher接入完整。子节点_ready先于trial父节点_ready，可在bind_trial时使用onready引用。所有评审按钮focus_mode=0，避免抢走常规WASD焦点。
- 显示合同：两侧同画布、同尺寸、同向同衣；原TextureRect固定最小尺寸仅静态近似，原生像素对齐风险按上项处理。nearest来自trial根texture_filter=1继承。待改Sprite2D后仅复核实际scale与坐标容器布局，不通过修改源图解决。
- 面板使用共享世界上衣状态是当前设计；世界正在运行不支持B的方向时，世界原能力门禁会拒绝B，面板不会私自换装或转向绕过。用户停步后可检查全部已提供组合。

结论：暂停、换衣、缺资源和局部时钟未发现其他实质错误。交付前需主代理完成Popup输入隔离与精确倍率修正；后续修复会另记确认，不把修复前风险抹去。

## 修复后定点只读确认

已按主代理提供的修复点重新读取相关段落，未重跑测试/GUI，未改项目文件。

- 原P2输入路径已在代码层覆盖：movement_input在review_panel.visible且is_selecting()为true时返回Vector2.ZERO；is_selecting直接检查Direction与Action两处Popup.visible，覆盖两个选择器，而不阻止面板普通显示时的世界移动。物理逻辑读取同一movement_input，所以Popup期间方向键不会再进入移动/转向/phase_ms累加路径。
- 原TextureRect倍率风险已在代码层覆盖：两侧纹理节点改为静态Control Slot内的Sprite2D，均显式nearest、centered=false、scale=Vector2(0.2371134,0.2371134)，即138/582；TrialUI CanvasLayer维持Transform2D的2倍。Slot的122×183仅提供布局空间，不再通过容器尺寸计算/拉伸纹理，实际绘制scale不受旧TextureRect像素对齐影响。
- 新headless用例确实弹出真实Direction Popup并Input.action_press(trial_walk_south)后断言movement_input归零，再释放输入/隐藏Popup。主代理报告该用例先FAIL再37项GREEN；本复查只确认测试覆盖代码，没有独立执行。
- 原生helper现在定向Popup.push_input并显式定位focused item；新增Popup可见期间四个physics_frame的实际actor.position、phase_ms、facing不变检查。实际2x断言改读Sprite2D的get_global_transform_with_canvas().get_scale()，不再由TextureRect.size反算。原生复验仍由主代理执行，本报告不提前宣布通过。

定点结论：此前P2与精确倍率问题的原因均已有针对性代码修复，未发现该修复引入新的静态阻塞。原生最终结果及用户视觉认可仍以主代理证据为准。

## 最终按钮选择版定点只读确认

最终实现已移除OptionButton/Popup及其导航逻辑，改为Directions四按钮、Actions三按钮的两个独立ButtonGroup；全部focus_mode=0、toggle_mode=true。原Popup共用物理方向键风险随组件移除关闭，movement_input不再保留Popup门禁是合理的；面板普通显示不妨碍世界WASD移动。

- 绑定顺序与枚举一致：South/West/East/North对应DIRECTIONS，Idle/Walk/Run对应ACTIONS；默认South/Run选中与脚本默认状态一致，两个ButtonGroup分开，不互相取消。
- closure使用每次循环内单独声明的direction/action字符串，回调固定该按钮的枚举值，同时在调用时读取另一维当前review_action/review_direction；没有把循环索引i延后解析为最终值的绑定。未发现闭包串键或方向/动作互换。
- select_clip校验枚举后只更新面板方向/动作、重置本地preview_phase_ms、用set_pressed_no_signal同步按钮状态并刷新。不会反复发pressed形成递归，也不写世界actor/phase/facing。
- 固定Sprite2D倍率、同向同衣idle参照、缺B动作清空、暂停换衣与逐帧语义均保留。
- 新headless末项改检查所有selector的FOCUS_NONE；主代理报告37项通过，本复查没有独立执行。原生helper现在实际点击四方向、Walk/Run并逐次检查世界position/phase/facing不变。当前代码未单独点击Idle按钮；若最终描述要声称“三种动作按钮均已原生点击”，应另补该点击，否则将范围写为四方向及Walk/Run，Idle已有静态与headless选择覆盖。

最终静态结论：此前Popup风险因移除组件关闭，未发现最终按钮版closure绑定或选择逻辑的实质错误；原生最终通过范围仍由主代理据实际运行记录报告。此次只读、不重跑测试/GUI、不改项目文件。
