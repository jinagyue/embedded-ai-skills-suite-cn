# V0.4 中文版：架构与自动调试模型

## 固件五层架构
```mermaid
flowchart TB
    APP["L5 APP / RTOS 业务编排"]
    SVC["L4 业务 Service"]
    L3["L3 BSP Service / Device / Protocol / Board"]
    BSP["L2 BSP Driver"]
    VENDOR["L1 Core / CMSIS / HAL / LL / Vendor"]
    HW["MCU + 板级硬件"]
    APP --> SVC --> L3 --> BSP --> VENDOR --> HW
```

横向基础设施：
```text
Middlewares/  FreeRTOS / FatFs / LVGL / lwIP
Common/       CRC / RingBuffer / math / utils
Config/       board/app/feature 配置
Tests/        单元 / 集成 / HIL
```

## AI 工程理解流程
```mermaid
flowchart TB
    P[STM32工程]
    IOC[解析 CubeMX .ioc]
    CONS[.ioc/source 一致性]
    RTOS[扫描 FreeRTOS Task/IPC]
    INC[生成 include 依赖图]
    HAL[检测 HAL/LL 跨层泄漏]
    RES[审计 Pin/DMA/IRQ/ISR]
    MODEL[project_model.json]
    MAP[AI/人工确认 arch-map.json]
    GATE[架构门禁复核]
    DOC[ARCHITECTURE/TASK_DESIGN/MODULE_MAP]
    P --> IOC --> MODEL
    P --> CONS --> MODEL
    P --> RTOS --> MODEL
    P --> INC --> MODEL
    P --> HAL --> MODEL
    P --> RES --> MODEL
    MODEL --> MAP --> GATE --> DOC
```

## V0.4 自动调试闭环
```mermaid
flowchart LR
    A[静态证据] --> B[.ioc/source 一致性]
    B --> C[Build]
    C --> D[Keil MAP + ELF]
    D --> E{允许烧录?}
    E -- 否 --> G[Observe/Serial]
    E -- 是 --> F[Flash]
    F --> G
    G --> H[FreeRTOS Runtime]
    H --> I[HardFault Decoder]
    I --> J[addr2line]
    J --> K[AI故障分类]
    K --> L[最小修改]
    L --> A
```

## 证据层次

```text
静态事实
  .ioc / include / HAL leak / IRQ / DMA / architecture

编译产物
  Build log / Keil MAP / ELF

运行事实
  Serial / RTT / SWO / ITM / GDB
  FreeRTOS Task / Stack HWM / Heap

CPU Fault
  CFSR / HFSR / BFAR / MMFAR / PC / LR / xPSR
  addr2line → source:line
```

安全规则：默认不自动烧录；没有证据时不宣称问题已经定位；工具只负责采证和复核，不替代芯片参考手册与真实硬件测量。
