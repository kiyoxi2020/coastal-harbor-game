# 潮港旧屋 Godot2D · 当前工程

当前试玩版 v0.5.5：旧屋门前 E 开门进入，紧凑室内下方中央门 E 走出。房间地板为288×208，人物尺寸和2倍镜头不变。床、门三态及13项新增室内素材全部使用生成像素图，家具底座与通行路径分别验证。门前0–56单位、横向±24范围连续交互；进屋时人物浅跨门槛8单位后由真实门扇遮挡并切换，出屋时关闭门先显露，再开门向下走出。室内外箱子共享原48格仓储；室内R回下方安全点；在屋内保存可继续回到屋内。

运行版本v0.5.5，Godot4.7.1。启动为标题页，可新游戏或继续进度。默认居中普通窗口，面积约占可用桌面的50%，内部1280×720，室外地图640×416，镜头2倍；室内固定镜头。导入project.godot后F5。WASD/方向键移动，E拾取/查看/开门/确认，B或Tab打开/关闭手账，R回当前场景安全入口且保留收获。提示仍用E继续/关闭，不要求Esc。

当前树木assets/tree-set-v4，当前地形/水面assets/environment-v2。新增台阶下低潮沙滩，六个固定拾取点，蛤蜊/海螺/海带各二；右上方为可点击的像素背包图标。人物、建筑与树木风格沿用原版，碰撞围绕可通行沙滩更新。

新增24格背包、48格旧屋仓储、个人记录、独立音量设置和单槽自动存档。旧屋东侧小木箱附近E打开仓储。支持拆分、移动、合并、整理和丢弃确认。采集统计不会因存箱或丢弃而减少。当前海产不可直接使用。

存档位于Godot user://coastal-progress，Mac默认为~/Library/Application Support/Godot/app_userdata/潮港旧屋 · 低潮赶海/coastal-progress/。progress.json为当前进度，progress.backup.json为上一份有效备份，settings.cfg单独保存设置。失败提示不会自动退出；强制结束进程仍可能丢失尚未落盘操作。新版本读取旧v1并在保存时写v2；旧应用不能读取v2，请勿交替运行。测试使用临时进度，未改玩家真实存档。

项目仅保留当前2D源码；旧交付包及archive已清理，历史通过Git提交追溯。原六组回归260项保留，新增库存、保存及手账测试见tests/test_item_catalog.gd、test_inventory_container.gd、test_inventory_operations.gd、test_save_state.gd、test_journal.gd。使用Godot --headless --log-file /private/tmp/coastal-test.log --path . --script res://tests/相应脚本运行。测试使用临时存档；旧赶海测试故意禁用持久化以检查原始场景，新手账测试覆盖保存恢复。

尚无种植、交易、睡觉、潮汐计时与资源每日刷新；六个点全部领取后不会自动重生，可通过标题页确认新游戏重开。音乐音轨尚未加入。Mac未Apple公证，Windows/Intel未测试。美术、字体及Godot许可沿用原工程。内部nearest过滤与等比非整数适配不变。

2026-10-15 GUI续验：实际编辑器保存发现并修复贴图覆盖丢失、拾取物种类丢失、嵌套玩家丢失三个缺陷。代表性Inspector编辑/保存与独立原生重载28/28，保存往返18项、普通属性审计4297项、场景合同132项、采集49项通过。详见`../docs/superpowers/plans/2026-10-15-editor-gui-acceptance.md`。未重新导出或提交。

编辑器场景迁移源码已于2026-10-15收尾：固定布局可直接编辑场景节点，树与有底座道具的碰撞随所属实例移动。室外场景根的world_bounds/foraging_area控制安全落点、镜头和采集区域；StorageCrates/InteractPoint控制仓储互动。Journal提供标题状态、个人资料与保存失败三个文案模板。新增合同见tests/test_editor_collision_ownership.gd、test_editor_outdoor_sources.gd、test_editor_journal_templates.gd。最终场景合同132/132；仍保留test_world的house_clear_of_header历史44/45例外与Terrain单色阶差1。此次仅更新源码，未重新导出或覆盖v0.5.5；详细验证见../docs/superpowers/plans/2026-10-15-editor-scenes-result.md。
