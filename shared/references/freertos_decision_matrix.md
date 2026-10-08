# FreeRTOS 原语选择矩阵
| 需求 | 推荐原语 |
|---|---|
| 传递结构体/命令 | Queue |
| 一个 Task 等待一个事件 | Task Notification / Thread Flag |
| ISR 唤醒 Task | ISR-safe Notification / Semaphore |
| 保护共享外设 | Mutex |
| 等多个健康状态位 | Event Group / Event Flags |
| 周期短触发 | Software Timer → 通知 Task |
| 大数据帧 | Buffer Pool + 指针 Queue |
| 字节流 | RingBuffer/StreamBuffer + Notification |
