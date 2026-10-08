# FreeRTOS 系统设计

## Task 不按外设划分
不推荐：`UART1_Task/ADC_Task/GPIO_Task`。优先按独立并发活动：`CommTask/MeasureTask/UITask/StorageTask/HealthTask`。

## IPC 选择
| 需求 | 首选 |
|---|---|
| 传结构体/命令 | Queue |
| 单 Task 事件通知 | Task Notification / Thread Flags |
| 保护共享 SPI/UART 资源 | Mutex |
| ISR 唤醒 Task | Notification / Binary Semaphore |
| 多状态组合等待 | Event Group / Event Flags |
| 周期触发 | Software Timer→通知 Task |
| 大数据帧 | Buffer Pool + 指针 Queue |

## ISR
- 不 `osDelay/vTaskDelay/HAL_Delay`。
- 不做 FatFs、JSON、`printf`、`strtok/sscanf` 等重工作。
- 只使用允许的 ISR API；CMSIS-RTOS2 ISR 发送必须非阻塞。

## 自动扫描
```bash
python shared/scripts/scan_freertos.py . --json
```
输出 Task、优先级、栈、Queue、Mutex、Semaphore、Event、Timer 及 ISR 中 RTOS 调用。

## V0.4 运行时 Stack/Task 证据
静态 `scan_freertos.py` 只能看到“配置了多少栈”，不能证明运行时余量。将 `tools/freertos_runtime/freertos_runtime_probe.c/.h` 接入调试串口或 RTT，周期/按命令输出 `@FREERTOS_SNAPSHOT` 和 `@FREERTOS_TASK`，再运行：

```bash
python tools/freertos_runtime/freertos_runtime_analyzer.py serial.log --report .embedded-ai/FREERTOS_RUNTIME.md
```

重点看 `stack_hwm_words`（历史最少剩余栈深度）而不是只看创建时的 stack size。
