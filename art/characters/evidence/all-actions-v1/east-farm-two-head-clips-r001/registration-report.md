East water/harvest：各4B＋exact walking idle，strict build/verify PASS。

- recipes/headwear-newfarm-water-east-hair-hat/r001.json SHA 510c77c7b3527645548875efabdf7f8fc878024d2ff10c01f15c7a798f58dbdf；builds/headwear-newfarm-water-east-hair-hat-r001；artifact 83917c2a690e5c13e2cbf1a9bba6209fd8fe09536e6a0719de696ab7ef93c12b；164 inputs复算一致。
- recipes/headwear-newfarm-harvest-east-hair-hat/r001.json SHA 8e1571e84dcec0c96c582ba8c651422de0e58ec53680db8b65eb5c396e1bbde6；builds/headwear-newfarm-harvest-east-hair-hat-r001；artifact 965987007dac3a185bff20cb98c8ff753d3256982b489d07f97c98e608a96288；163 inputs复算一致。

两clip同用真实WaterEastBReady完整新GPT源，整体统一256/187 nearest→1536×1920；真实眼/可见下耳前端midpoint半上取整[834779]→canonical[824745]，全pairδ[-10,-34]，两锚残差[3.5,-7]/[-5,6]。Source pose不改，source anatomy全部排，纯hair/透明外缘保留，四个alpha1白背景点另列非hair。有限帽下可见hair，不claim完整隐藏crown或barehair。

8原iris/同一ear-bowl ROI均0变化，head support外0RGBA变化；idle PNG/RGBA与walking冻结完全相同。新帽再审：手/壶/叶等非暗材质0交叠，自动黑点全为原头轮廓，非foreground。HarReach完整帽α右边恰1536 exclusive，无裁/缩帽/任意挪移。Actual source owner与整源密度在target-envelope检查前已独立固定，不靠此边界擦图。

完整raw/prompt/3引用/source/binary masks/typedclaim/规范source annotation皆入源闭包。两build先/tmp严格构建、verify、actual ROI/closure audit，再原子移入。未验：原生连续8姿态、用户/正式发布；global unit/check交root统一。
