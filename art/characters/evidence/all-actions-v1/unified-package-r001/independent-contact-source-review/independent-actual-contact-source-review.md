已独立复核12个农事clip的接触候选帧，并补看4向harvest reach，共16姿态/70个实际材料像素。所有完整历史源按已登记整帧平移逐RGBA重建 canonical B；每个候选点在原完整源、canonical和冻结top03 body中RGBA相同。

这些是可见材料证据与静态接触候选：手掌遮住的柄心不可观测；小ROI不是完整归属mask；单点不等于连续轨迹或原生接触通过。未改源图、母版、配方或代码。

| 动作方向/姿态 | 实际可见候选 | 目标/限制 |
|---|---|---|
| hoe_south_key_2 | upper_hand[676, 1127], lower_hand[885, 1329] | 金属刃缘[1147, 1670]，ground候选，非soil已证实 |
| hoe_west_key_2 | lower_hand[505, 1285], upper_hand[740, 1120] | 金属刃缘[240, 1490]，ground候选，非soil已证实 |
| hoe_east_key_2 | upper_hand[837, 1070], lower_hand[1085, 1201] | 金属刃缘[1400, 1530]，ground候选，非soil已证实 |
| hoe_north_key_2 | upper_hand[888, 1130], lower_hand[988, 1230] | 金属刃缘[1222, 1483]，ground候选，非soil已证实 |
| water_south_B_pour | top_hand[720, 1015], top_handle[744, 1020], side_hand[891, 1121], side_handle[873, 1076] | 水花中心[545, 1670]，ground候选，非soil已证实 |
| water_west_B_pour | top_hand[583, 997], top_handle[620, 1025], side_hand[735, 1130], side_handle[697, 1085] | 水花中心[309, 1570]，ground候选，非soil已证实 |
| water_east_B_pour | top_hand[1020, 1080], top_handle[995, 1100] | 水花中心[1350, 1600]，ground候选，非soil已证实 |
| water_north_B_pour | top_hand[538, 1030], top_handle[523, 1076] | 水花中心[367, 1575]，ground候选，非soil已证实 |
| harvest_south_B_pluck | left_hand[660, 1195], right_hand[855, 1203] | crop；萝卜/根须完整可见，无soil遮挡 |
| harvest_west_B_pluck | stem_hand[450, 1065], root_hand[585, 1185] | crop；萝卜/根须完整可见，无soil遮挡 |
| harvest_east_B_pluck | upper_hand[1100, 1075], lower_hand[1070, 1125] | crop；萝卜/根须完整可见，无soil遮挡 |
| harvest_north_B_pluck | visible_hand[575, 1080] | crop；萝卜/根须完整可见，无soil遮挡 |
| harvest_south_B_reach | left_hand[688, 1420], right_hand[820, 1400] | crop；萝卜/根须完整可见，无soil遮挡 |
| harvest_west_B_reach | reaching_hand[280, 1424], other_hand_on_knee[688, 1378] | crop；萝卜/根须完整可见，无soil遮挡 |
| harvest_east_B_reach | lower_hand[1160, 1372], upper_hand[1225, 1340] | crop；萝卜/根须完整可见，无soil遮挡 |
| harvest_north_B_reach | visible_inner_hand[665, 1374], visible_outer_hand[545, 1200] | crop；萝卜/根须完整可见，无soil遮挡 |

重要限制：

- 四向harvest reach和pluck都没有可观察土壤界面；根尖不能当土壤接触点。实际手-叶柄/根球可见，North部分握持被身体/叶片遮挡。
- West harvest reach另一只手位于膝盖，是可见支撑手，不是另一作物握持点。
- North water另一侧握手在身体/壶后不可见，不编精确第二握点。
- Hoe的ground候选位于真实金属刃缘，Water位于真实画出的水流/水花；实际场景中的地表、目标格与投影由root原生验证。候选位置有8源像素局部语义范围，不继承旧metadata uncertainty为通过。
- 旧Westhoe2 butt[816,1118]、Northwater recovery top-handle[583,1057]已知是衣料点，本次未采用。

完整绑定与RGBA：`independent-actual-contact-source-review.json`。实际17×17原生ROI、8×NEAREST点图：`independent-reviewed-contact-points/`。原canonical详细网格/16整帧源平移记录：`independent-actual-canonical-source-bindings.json`。输出仅/private/tmp；未作native或用户认可声明。
