# 西向真实草帽near/far适配

完整原GPT2048×768 atlas来自motion-headwear-sampling-v1-ac71442e，不用旧derived registered图当raw。idle_west_0 crop区域[512,0,1024,768]的真实whole owner嵌回原atlas，统一ratio1；atlas锚[804,282]→canonical[292,282]。源atlas使用image origin[0,0]，没有虚构actor world root。

near/far引用同一个完整raw、source pose、extraction和整体注册，只在canonical source ownership分真实前后表面。两mask不重叠、并集精确重建whole帽；idle每层逐RGBA等于旧交付。四walk只应用实际耳锚delta，无volume或逐列擦hair；保留far/base/under/near真实层序。

仅此五pose有限固定配方候选。完整来源/提示词保留；没有自动切换试玩、用户认可或生产发布。
