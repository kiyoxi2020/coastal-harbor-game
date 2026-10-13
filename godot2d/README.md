# 潮港旧屋 Godot2D · 当前工程

运行基线v0.5.0，Godot4.7.1。启动为标题页，可新游戏或继续进度。默认居中普通窗口，面积约占可用桌面的50%，内部1280×720，地图640×416，镜头2倍。导入project.godot后F5。WASD/方向键移动，E拾取/查看/确认，B或Tab打开/关闭手账，R回路口且保留收获。提示仍用E继续/关闭，不要求Esc。

当前树木assets/tree-set-v4，当前地形/水面assets/environment-v2。新增台阶下低潮沙滩，六个固定拾取点，蛤蜊/海螺/海带各二；右上方显示背包。人物、建筑与树木风格沿用原版，碰撞围绕可通行沙滩更新。

新增24格背包、48格旧屋仓储、个人记录、独立音量设置和单槽自动存档。旧屋东侧小木箱附近E打开仓储。支持拆分、移动、合并、整理和丢弃确认。采集统计不会因存箱或丢弃而减少。当前海产不可直接使用。

存档位于Godot user://coastal-progress，Mac默认为~/Library/Application Support/Godot/app_userdata/潮港旧屋 · 低潮赶海/coastal-progress/。progress.json为当前进度，progress.backup.json为上一份有效备份，settings.cfg单独保存设置。失败提示不会自动退出；强制结束进程仍可能丢失尚未落盘操作。旧版无持久进度，升级后首次从新游戏开始。

最新交付在项目交付与预览/2D/，历史在archive，不进Git。原六组回归260项保留，新增库存、保存及手账测试见tests/test_item_catalog.gd、test_inventory_container.gd、test_inventory_operations.gd、test_save_state.gd、test_journal.gd。使用Godot --headless --log-file /private/tmp/coastal-test.log --path . --script res://tests/相应脚本运行。测试使用临时存档；旧赶海测试故意禁用持久化以检查原始场景，新手账测试覆盖保存恢复。

尚无种植、交易、睡觉、潮汐计时与资源每日刷新；六个点全部领取后不会自动重生，可通过标题页确认新游戏重开。音乐音轨尚未加入。Mac未Apple公证，Windows/Intel未测试。美术、字体及Godot许可沿用原工程。内部nearest过滤与等比非整数适配不变。
