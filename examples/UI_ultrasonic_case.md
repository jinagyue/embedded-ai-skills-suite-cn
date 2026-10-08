# UI_ultrasonic 重构示例
示例工程：`jinagyue/UI_ultrasonic`。

## 典型问题
`freertos.c` 同时承担 Task 创建、UI 状态、FatFs、UART 协议解析、DTU/MQTT、RS485、Watchdog、GPIO/ADC/RTC 等职责，导致“调度层、协议、器件和产品流程”相互耦合。

## 目标映射
```text
BSP/Driver
  bsp_uart / bsp_adc / bsp_encoder / bsp_gpio / bsp_watchdog
BSP/Service
  uart_stream
Device
  dev_nextion / dev_dtu
Protocol
  proto_measure / proto_ui / proto_console
Service
  measurement_service / depth_service / ui_service / storage_service / cloud_service / health_service
App
  app_measure_state_machine / app_system
RTOS
  rtos_objects / rtos_tasks
```

## 第一阶段迁移
1. 先把 `[Data,...]`、`RACK/EACK/ERCK` 和命令格式抽到 `Protocol/`，保持行为不变。
2. 把测量锁、Timeout 和结果生命周期移入 `measurement_service` + APP 状态机。
3. Task 只等待事件并调用 `*_service_process()`，不再直接解析字符串。
4. 将 GPIO/ADC/TIM HAL 调用逐步移到 BSP。
5. 用模块 Context、消息和访问函数替代跨文件可写全局变量。

## 建议 Task
`CommTask`、`MeasureTask`、`UITask`、可选 `StorageTask`、`HealthTask`。不要按 UART/ADC/GPIO 一外设一 Task。
