# Compact Cottage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development task-by-task. Follow test-driven-development.

**Goal:** Deliver the approved compact north-entry cottage with generated furnishings and verified natural door crossings.

**Architecture:** Room data owns geometry; door owns front-zone and opening; transition owns motion and visual clipping. Generated asset processing stays deterministic and separate from runtime rendering.

**Tech Stack:** Godot 4 GDScript, Pillow, built-in image generation, macOS exports.

## Global Constraints

- 地板区域设为Rect2(176,112,288,208)，北墙门槛(320,128)，室内安全落点(320,160)。
- 保留E查看/继续/开门、背包、共享仓储、单槽存档、1280×720显示与默认半桌面窗口。
- 保留存档version=2及库存字段，不为改房间丢弃进度。
- 使用之前选定的内置生图服务，不改换外部供应商。
- 不新增料理、睡眠、装修、交易和任务。
- No push, no changes to 3D. Isolate every test save under /private/tmp. Use explicit /private/tmp log-file for Godot.

### Task 1: Compact geometry and reliable north-door transitions

**Files:** Modify godot2d/scripts/{room_data,interactive_door,room_transition,house_session,house_interior,player}.gd and relevant Godot tests. Create godot2d/tests/test_compact_cottage.gd and optional focused door visual shader. Do not modify asset pipeline/furniture art yet.

**Requirements:** Read approved docs/superpowers/specs/2026-10-13-compact-cottage-north-entry-design.md for full geometry, trigger and animation specification. Apply every behavior/save requirement; furniture source replacement belongs Task 2. Keep furniture kind interfaces stable. Add entrance_normal=Vector2.DOWN explicitly, continuous frontal depth0..56/lateral24, obstruction check and collision-safe lateral alignment without retreat. Remove player forced z-order. Implement progressive visual doorway clipping, reset on success/failure/load, separate foreground jamb. Cross until fully hidden before fade. Keep destination emergence natural. Preserve input locks and exit/save safeguards.

**Interfaces:** Room data constants remain FLOOR/SPAWN/DOOR/STORAGE; furniture returns kind/rect. Door can_interact(point:Vector2)->bool remains caller interface. Use doorway visual methods on player or independent helper, not physics scaling. Expose clipping state for behavioral assertions if useful but test actual shader/visual output too.

- [ ] Write a real failing trigger sweep before changes: `for depth in range(57): assert(door.can_interact(door.position + Vector2(0,depth)))`; include both door orientations, lateral boundaries and invalid back/range cases.
- [ ] Run `/Applications/Godot.app/Contents/MacOS/Godot --headless --log-file /private/tmp/compact-red.log --path godot2d --script res://tests/test_compact_cottage.gd` and record expected current near-door failures.
- [ ] Implement geometry and door phases following approved spec. Alignment target keeps player y: `Vector2(door.position.x,player.position.y)`. Door normal determines crossing independently of inside.
- [ ] Update old geometry assertions without removing behavioral coverage. Test valid old320300, invalid320328, furniture collisions, first movement no retreat, blocked alignment, menu and busy exclusion, visibility cleanup, failed target, twenty cycles.
- [ ] Run focused compact, house-save, cottage-runtime and house tests, capture GUI both directions at partial/full/emerging and final room. Report test commands, results and capture paths. Commit only Task1 changes and full report.

### Task 2: Complete generated interior asset integration

**Files:** art/interior/source and processed; tools/prepare_cottage_assets.py; tests/test_prepare_cottage_assets.py; godot2d/assets/house-interior; godot2d/scripts/{cottage_art,house_furniture,house_interior}.gd; asset tests.

**Interfaces:** Preserve pilot.json existing bed/door entries and add entries for nightstand,kitchen,table,chair,chest,shelf,photo,plant,window,rug,bed_rug,wall,floor. Each has source provenance, logical size, floor anchor, collision footprint/interaction metadata as applicable. Runtime furniture keeps kind/rect API from Task1.

- [ ] Parent supplies built-in generated sources; if generation unavailable report honestly, never substitute another provider. Approved existing concept may serve as source if its isolated objects cleanly extract.
- [ ] Add failing manifest completeness and alpha/size/provenance tests before processing/runtime edits. Preserve original sources.
- [ ] Deterministically crop registered atlas cells, clean alpha, nearest resize preserving silhouettes; reuse existing bed/door unchanged. Wall/floor must generated textures, not procedural furniture.
- [ ] Draw all furniture/background from images with correct anchors; ground collisions only physical bases. Ensure visually clear corridor and every inspect/storage point reachable. Release cannot hit missing-art fallback.
- [ ] Run Python unit tests and Godot assets/runtime tests and capture/view final room at game scale. Commit changes and report.

### Task 3: Final visual regression and current release

**Files:** test drivers if needed, export_presets.cfg, latest2D release, docs result, source packaging tool if new asset paths need selection.

- [ ] Before final regression, fix root-observed exterior hair-over-awning defect in /private/tmp/compact-door-stages/harbor-partial.png. Add a real rendered regression that opening-plane actor pixels above the exterior aperture top are occluded. Use explicit door aperture top/world-coordinate clipping or equivalent foreground mask, preserving the art and character pixels below the opening. Keep indoor actor fully visible on floor. Restore this additional mask on every transition/load/failure cleanup. Follow RED/GREEN, capture both doors again. Own scripts/player.gd, doorway_clip.gdshader, interactive_door.gd, room_transition.gd and test_compact_cottage.gd for this fix.
- [ ] Resolve Task1 test minor: explicitly assert FadeOut was observed and transition completed at expected destination. Clarify ignored walk_to duration argument without adding unrelated movement features. Existing distance/72 behavior must remain.
- [ ] Run all existing test suites plus new focused cases with isolated saves. Validate near-door center/lateral, blocked alignment, twenty crossings, old saves, failure cleanup, journal/storage and exit/restart.
- [ ] Capture continuous in/out animation and five phases each; inspect visually for no feet-on-leaf, no sudden premature disappearance, normal destination emergence. Fix visual defects with failing regression first.
- [ ] Export v0.5.4 into staging, run actual app house/journal/restart tests. Verify source ZIP matches current selected files byte-for-byte and ZIP CRC; verify app signature.
- [ ] Move old latest2D recoverably into ignored archive, promote only verified new2D; leave3D untouched. Copy user-facing deliverables to outputs/current-game. Record actual platform/test limits. Commit, no push.
