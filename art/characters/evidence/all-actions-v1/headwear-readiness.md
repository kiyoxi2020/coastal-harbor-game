# 固定发帽全动作：来源准备审计

范围：24格、84pose，固定hair_hat；本报告不是正式资源登记或原生验收。

**已有20个同posehair/hat来源；其中南/北10pose存在已证实under-hat源缺口；西walk4pose有历史实测锚点；其他walk12pose本轮只做近似轮廓诊断，余48pose仍须实际donor/target投影比较。** 缺登记不等于缺像素，确切新增绘制视图数尚不能诚实给出。

|动作|south|west|east|north|
|---|---|---|---|---|
|idle|同pose基础源；须核under-hat|同pose基础源；须核under-hat|同pose基础源；须核under-hat|同pose基础源；须核under-hat|
|walk|近投影诊断；锚未准入|原idle源＋实测锚候选|近投影诊断；锚未准入|近投影诊断；锚未准入|
|run|投影/注册未证明|投影/注册未证明|同pose基础源；须核under-hat|投影/注册未证明|
|hoe|投影/注册未证明|同pose基础源；须核under-hat|投影/注册未证明|投影/注册未证明|
|water|同pose基础源；须核under-hat|投影/注册未证明|投影/注册未证明|投影/注册未证明|
|harvest|投影/注册未证明|投影/注册未证明|投影/注册未证明|同pose基础源；须核under-hat|

## 已有完整来源与兼容边界

- 东跑/西锄：真实完整hair、独立under_hat、near/far帽均有来源；西锄key2两源选择必须保留，不能只挑前发或用visible mask当源。西锄key1/东idle使用完整hair与真实帽表面形成已记录hair_hat，并非漏图。
- 南浇/北收：完整hair及完整hat atlas、每pose手审ownership、整数耳边锚注册均保留。但Git旧builder把每列0..brim轮廓当作volume擦hair，且实际擦掉了帽面alpha之外的真实发像素；因此旧tucked PNG不能直接准入为完整under_hat源。缺的是适合帽内的压低发冠/翘毛与后发投影，而非补body或重画脸。near/far未拆只是额外接口问题，不单独推导缺图。
- 其他衣装样例仅取有真实语义的头部源；JSON保留父衣装身份。所有来源的face/hand/body禁止复制；南浇/北收ownership显式记录no_old_face_or_hands与手审polygon。

## 逐pose与文件闭包

伴随JSON含84行target、20个完整donor、原始注册锚/画布/尺度/源pose、每个source/ownership/coverage/occlusion/manifest/完整源包及prompt的实际SHA。原pose保持真实身份。

已核sample inputs 469项，SHA不符 0项；共索引657个实际文件。

## 缺口与补图边界

- hoe/south and harvest/south：front crown and bangs under downward pitch; brim top/underside, front opening and temple contact at ready/lift/contact/reach/pluck states。候选：water_south_B_* at farm density; compare before requesting pixels；conditional on actual pitch incompatibility; no target-specific source currently registered。
- hoe/east, water/east, harvest/east：east-facing farm-density temporal hair/ear opening, posterior tuft, down-pitch crown; navy-band cap, brim near/far and underside to match tool/hand pose。候选：only idle_east_0/run_east_* at locomotion density in current adaptation; whole-source normalization needs actual projection proof；unproven count; do not mirror west or resize one part。
- water/west and harvest/west：side crown/temple and compressed fringe under cap for head tilt; rear hair and near/far brim as bending changes projection。候选：hoe_west_key_* at farm density；conditional after ear/skull/eye and brim geometry comparison。
- hoe/north and water/north：rear crown/nape and cap opening/underside in raised-tool/contact/bent posture。候选：harvest_north_B_* at farm density；conditional; behind-head brim must come from painted source surface, not invented occlusion。
- run/south, run/west, run/north：stride-dependent skull/ear pitch, cap opening and tucked nape; no registered run target views in these directions。候选：same-direction idle; west hoe requires density reconciliation；conditional; run south/north B are rejected body witnesses and cannot be promoted via headwear audit。

## 近似投影诊断

西walk沿用已有耳弓锚[292,282]→[293,281]/[293,281]/[292,281]/[294,281]；源注册锚[291,308]。实际source_view_pose均是idle_west_0。

本轮其他walk整数平移后的头部轮廓max：south 3.606–5.831源px，east 5.000–5.657，north 2.236。它们只是图像诊断；south末pose的耳弧ROI支持不足，其他新target也未完成可准入解剖锚登记。不能把这些数当屏幕≤1px或GPU通过，不能靠此宣布不用补图。

## 尚未完成

其余60pose的新注册/全部候选投影比对、原生连续与接触、固定衣装头部接口核验仍未完成；没有新GPT图、配方、构建、播放器或正式资源改动。故本报告可作为来源索引与明确待测表，不可当T01全部投影已证明或确切新增绘制数的完成证据。

## 已证实：南/北under-hat源不能直接沿用

旧builder `379a9bc:art/design/character-motion/adult-standard-v1/headwear-sampling-v1/water-south/build_sample.py`，SHA `8d8e700ec8d2000d6ab54f31109c6987bd7d4706b6f26a1af5da8e56d7f1c692`。它先把每列从画布顶到帽檐轮廓全部填volume，再以此擦hair；这不等于真实绘制帽面的遮挡。完整源实图中发冠/翘毛确实超出帽面，不能把擦除后的旧结果倒称完整部件。

|source pose|擦除但未被实际hat alpha覆盖的hair像素|
|---|---:|
|water_south_B_ready|7029|
|water_south_B_raise|8203|
|water_south_B_pour|9199|
|water_south_B_recovery|9340|
|idle_south_0|454|
|harvest_north_B_ready|22904|
|harvest_north_B_reach|24908|
|harvest_north_B_pluck|23219|
|harvest_north_B_recovery|28365|
|idle_north_0|280|

需要真实兼容压帽发源，重点为南向前发冠/两鬓、北向后脑发冠/翘毛与后发。可先每向一个单侧/投影小样，再凭实际锚点复用；10个受影响pose不等于10次生图。现有东跑/西锄的正确专用帽下发不能按方向名或局部缩放冒充它们。完整原hair、GPT atlas、ownership仍保留，可用于条件参考与来源复核。
