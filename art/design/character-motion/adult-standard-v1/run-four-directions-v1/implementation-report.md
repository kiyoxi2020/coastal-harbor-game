# Task 1 实施报告

执行者：`run_directions`，实际模型`gpt-6.1-sol/high`；受主代理委派，复杂姿态/身份与分层判断。使用`imagegen`技能、built-in GPT image_gen；后续按`systematic-debugging`技能追查北向B归属/alpha缺陷。没有API fallback、子代理、GUI、提交或共享文件修改。只写本新目录；主代理独占`archive_native_evidence.py`和`evidence/native/`。

## 交付与未完成范围

四向A共16完整帧已按既有candidate合同登记，具备技术加载条件；西A复制原认可纹理，东A/B在实际对称条件检查后整帧反射。B有效能力仅west/east，真实分层及可见身体像素与西向现行结果一致。北A四帧真实分层全RGBA还原；北B有真实GPT完整衣身和袖层、coverage与occlusion，但未通过接口质量门禁。南B两轮完整源姿态失败，未拆层/未启用。详见`review.html`、`run-garments.json`、`evidence/garment-quality.json`。

**南北A身份比例未通过。** 初看大图时仅判断动作完整及接触/腾空轮换，缩略目视不足以冻结比例；整理同密度证据后测得明显头部带宽差。已向主代理报告并显著标在review与README。不得宣称任务的“四向run美术合格”完成。此处不把全身运动投影当作头宽一致的解释。

量测：registered坐标ROI `[0,0,512,345]`，alpha≥128，取其bbox宽，**包含耳朵，不是分离头骨或冻结关节量测**。同向批准idle：south257、north256源像素；run south289/290/290/290，north282/280/283/282。约12.5–12.8%与9.4–10.5%宽差。输出/引用哈希及全部bbox在`evidence/geometry-audit.json`；原生同向idle明暗对照由主代理验。需要复审，可能完整源稿返工，未缩放任何头部/肢体。

## 生成与源检查

实际查看active_revision眉毛v3完整母版、已认可西run v4完整源、south/north/east已批准walk、west B样式；输入文件及SHA在`evidence/source-index.json`。共10次built-in GPT生成，原图全部原分辨率保存，完整提示词在`prompts/`。

- South A v1腾空1/3腿姿态重复；v2完整第四格更换消除重复腿，但第二格同侧手腿前伸；v3只在同一源尺度完整重绘第二格为反侧摆臂。没有程序移动肢体。
- North A v1两腾空格同侧手腿后摆；v2完整重绘两腾空格手臂，保留左右交替支撑/腾空。source gate的比例风险在后续同尺度量测中单独暴露，不继承动作轮换的通过结论。
- South B v1头/领口较A上移约9–13源像素而脚未同移；不能整帧平移修。第二轮加入明确源坐标后，第三格胸前手消失、双臂下垂，动作模板变了；停止该方向B，不继续批量衣身。
- North B保留原四姿态，另GPT生成A/B完整无臂衣身；不是程序补色或从脸手裁拼新母版。拆层时发现肩部cream残留，定位为semantic ROI未覆盖真实肩帽，扩大到实际衣物总范围后A仍全RGBA还原。随后更严格闭合alpha检查发现未过的问题，未以新mask或源alpha涂抹填洞。

北B可复现：运行`check_garments.py`，四帧alpha<128且与画布外部不连通的衣物带孔数9/9/68/86，共172；其中alpha0为4/6/40/78。总范围x55:455、y335:550，四邻域flood，保留原PNGalpha。源码和mask不是全部缺像素：点(306,495)是A棕暗裤腰(53,47,35,253)误归torso，B源同点棕色(91,80,60,253)被cloth排除；点(217,347)A颈黑边误归衣物，B颈轮廓不同；点(331,433)B腋下源alpha119、完整衣身alpha252，当前A投影遮挡压住，尚未证明改变occlusion符合真实前后关系。记录逐层数据后保留拒绝；不盲改mask、挪衣鞋或补颜色。

## 命令与结果

在项目根执行：

```sh
python3 art/design/character-motion/adult-standard-v1/run-four-directions-v1/build_candidate.py
python3 art/design/character-motion/adult-standard-v1/run-four-directions-v1/test_candidate.py
python3 art/design/character-motion/adult-standard-v1/run-four-directions-v1/build_parts.py
python3 art/design/character-motion/adult-standard-v1/run-four-directions-v1/check_garments.py
python3 art/design/character-motion/adult-standard-v1/run-four-directions-v1/build_garment_manifest.py
python3 art/design/character-motion/adult-standard-v1/run-four-directions-v1/test_parts.py
python3 art/design/character-motion/adult-standard-v1/run-four-directions-v1/write_source_index.py
python3 art/design/character-motion/adult-standard-v1/run-four-directions-v1/audit_geometry.py
python3 art/design/character-motion/adult-standard-v1/run-four-directions-v1/build_review.py
```

完整帧8项、分层7项通过；后者包括拒绝真实失败能力。A实际12个分层姿态逐RGBA还原；B西复制原源、东整帧反射；层合成与所有bakes一致；北B非可编辑区的脸/颈/裤鞋及手像素不变。`node --check /private/tmp/coastal-run-four-review.js`通过（从生成review的script标签提取）。子代理未运行Godot、未碰玩家存档，也没有以headless代替原生。

过程中第一版candidate漏既有必需`walk_artifact_digest`，主代理原生加载因此拒绝、尚未播放；补入当前walk digest并增加直接绑定当前walk清单的测试。注册纹理没有变化。初版东向逆反射“全字节”测试因alpha0的原x0列隐藏RGB截去而失败；查明整列alpha恒0后改为同时验证alpha全相等、x≥1所有RGBA相等、丢弃列alpha恒0，未放宽可见像素或alpha标准。

## 冻结与哈希

`candidate.json` SHA256：`07578d9cc37f8dc5565ee9035103dfd6c444a57869a384ec24279cc20f982b00`。主代理收到冻结后，本代理不再改candidate/registered；原生证据必须绑定此hash。

`parts-manifest.json`记录输入/部件/输出各SHA；其`artifact_digest`为`203c3158f3a748c7886184f0c5cb55e39d3cb058b4e3fc61ed3081b652fa33e9`。`run-garments.json`按有效方向记录实际PNG、真实层/mask与西向来源哈希；不把南北B加入能力。源图与提示词逐SHA、原始生成路径与实际参考角色分别在`evidence/source-index.json`；原图2048×768、单格512×768、原生画布约121.40×182.10屏幕像素，scale0.2371134021，nearest。

完整文件SHA256：`parts-manifest.json`=`855893c28e5e892cc7bd3c6dd1b0b62dac8d1f039e549ab36752aa5f06f7d1ea`；`run-garments.json`=`02fab94ae1b8a8ccb9226b2292fceb71cdbcc83e52e93da5511c0ee52381a01e`。分项状态及对应输入哈希在`evidence/review.json`，与主代理原生技术证据分开记录。

## 交接限制

原生连续十循环、走跑/转向/idle换衣与明暗/idle比例对照由主代理串行执行并归档；本报告不提前声明这些已过。精确隐藏关节、批准接触轨迹、完整裸身体、完整四向B、独立裤鞋/发帽、8配方、生产接入及用户认可均未完成。source、registration、static reconstruction、technical playback和用户认可保持独立，后续改变实际依赖时对应证据失效。
