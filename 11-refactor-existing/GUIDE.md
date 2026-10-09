# 存量工程渐进式重构

![存量工程 · 渐进重构路径](../docs/assets/skills/11-refactor-existing.png)

## 先盘点，不先搬文件
为每个函数记录：当前文件、职责、HAL 调用、RTOS 调用、协议字符串、共享全局、目标层、调用者/被调用者。

## 推荐顺序
1. 抽出纯 Protocol parser；
2. 抽出业务 Service；
3. 封装 BSP/Device；
4. 让 Task 只负责等待事件和调用 APP/Service；
5. 消除可写 extern 和跨模块句柄；
6. 最后再调整目录。

## 不做“大爆炸重写”
每次只迁移一条可验证纵向链路，旧路径保持可回退。每一步都重新构建、测试和运行静态门禁。
