# 当前住宅像素美术源

本版采用原生像素绘制，不使用额外的烘焙背景图片。可编辑源为 godot2d/scripts/house_interior.gd 和 house_furniture.gd，布局及碰撞为 room_data.gd。后续替换精灵时保留脚底锚点和交互/碰撞边界。

独立门源为现有 godot2d/assets/environment.png：门扇使用源矩形 (348,383,61,81)，原房屋门洞矩形 (347,382,63,84)。house_exterior.gd 排除门洞后绘制房屋剩余四片；interactive_door.gd 复用门扇像素并绘制三种整数宽度，保留原图以便追溯。

当前风格：暖木地板、米白墙、青蓝窗框、海盐绿缝线地毯和碎花被面。建筑、人物、家具各自独立，不以概念图代替游戏对象。
