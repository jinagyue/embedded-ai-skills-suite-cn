# 技能结构图与架构图

一个总入口、14 个专业模块、12 个工具后端，共 27 张图。每张图按照对应说明页整理模块、层级与调用关系。

图中展示推荐设计或工具能力结构；FreeRTOS 等示例关系需按目标工程调整。

提供 PNG 浏览图与可编辑 SVG；[设计说明与提示词](IMAGE_PROMPTS.md)、[可复现图源](diagrams/README.md)、[文件校验清单](IMAGE_MANIFEST.json)。

## 总入口

![单入口架构](assets/skills/embeddedskills.png)

[总入口说明](../SKILL.md) · [SVG 图源](assets/skills/embeddedskills.svg)

## 专业模块

### 嵌入式开发 · 总流程

![嵌入式开发 · 总流程](assets/skills/00-embedded-workflow.png)

[模块说明](../00-embedded-workflow/GUIDE.md) · [SVG 图源](assets/skills/00-embedded-workflow.svg)

### 嵌入式软件 · 五层架构

![嵌入式软件 · 五层架构](assets/skills/01-embedded-architecture.png)

[模块说明](../01-embedded-architecture/GUIDE.md) · [SVG 图源](assets/skills/01-embedded-architecture.svg)

### C99 模块 · 接口与状态结构

![C99 模块 · 接口与状态结构](assets/skills/02-c99-embedded.png)

[模块说明](../02-c99-embedded/GUIDE.md) · [SVG 图源](assets/skills/02-c99-embedded.svg)

### Cortex-M · 启动与异常结构

![Cortex-M · 启动与异常结构](assets/skills/03-arm-cortexm.png)

[模块说明](../03-arm-cortexm/GUIDE.md) · [SVG 图源](assets/skills/03-arm-cortexm.svg)

### STM32 · 配置与 BSP 结构

![STM32 · 配置与 BSP 结构](assets/skills/04-stm32-platform.png)

[模块说明](../04-stm32-platform/GUIDE.md) · [SVG 图源](assets/skills/04-stm32-platform.svg)

### Device / Protocol / Service · 职责结构

![Device / Protocol / Service · 职责结构](assets/skills/05-device-service.png)

[模块说明](../05-device-service/GUIDE.md) · [SVG 图源](assets/skills/05-device-service.svg)

### FreeRTOS · Task 与 IPC 结构

![FreeRTOS · Task 与 IPC 结构](assets/skills/06-freertos-design.png)

[模块说明](../06-freertos-design/GUIDE.md) · [SVG 图源](assets/skills/06-freertos-design.svg)

### 嵌入式通信 · 分层链路

![嵌入式通信 · 分层链路](assets/skills/07-embedded-protocols.png)

[模块说明](../07-embedded-protocols/GUIDE.md) · [SVG 图源](assets/skills/07-embedded-protocols.svg)

### Bring-up · 逐层验证结构

![Bring-up · 逐层验证结构](assets/skills/08-debugging-bringup.png)

[模块说明](../08-debugging-bringup/GUIDE.md) · [SVG 图源](assets/skills/08-debugging-bringup.svg)

### 质量验证 · 测试层级结构

![质量验证 · 测试层级结构](assets/skills/09-quality-review-testing.png)

[模块说明](../09-quality-review-testing/GUIDE.md) · [SVG 图源](assets/skills/09-quality-review-testing.svg)

### 可靠性与低功耗 · 状态结构

![可靠性与低功耗 · 状态结构](assets/skills/10-reliability-lowpower.png)

[模块说明](../10-reliability-lowpower/GUIDE.md) · [SVG 图源](assets/skills/10-reliability-lowpower.svg)

### 存量工程 · 渐进重构路径

![存量工程 · 渐进重构路径](assets/skills/11-refactor-existing.png)

[模块说明](../11-refactor-existing/GUIDE.md) · [SVG 图源](assets/skills/11-refactor-existing.svg)

### AI 自动调试 · 证据闭环

![AI 自动调试 · 证据闭环](assets/skills/12-auto-debug.png)

[模块说明](../12-auto-debug/GUIDE.md) · [SVG 图源](assets/skills/12-auto-debug.svg)

### 固件工具箱 · 输入与分析结构

![固件工具箱 · 输入与分析结构](assets/skills/13-firmware-tools.png)

[模块说明](../13-firmware-tools/GUIDE.md) · [SVG 图源](assets/skills/13-firmware-tools.svg)

## 工具后端

### CAN / CAN-FD · 总线工具结构

![CAN / CAN-FD · 总线工具结构](assets/skills/can.png)

[模块说明](../can/GUIDE.md) · [SVG 图源](assets/skills/can.svg)

### EIDE · 构建后端结构

![EIDE · 构建后端结构](assets/skills/eide.png)

[模块说明](../eide/GUIDE.md) · [SVG 图源](assets/skills/eide.svg)

### CMake / ARM GCC · 构建结构

![CMake / ARM GCC · 构建结构](assets/skills/gcc.png)

[模块说明](../gcc/GUIDE.md) · [SVG 图源](assets/skills/gcc.svg)

### J-Link · 下载与调试结构

![J-Link · 下载与调试结构](assets/skills/jlink.png)

[模块说明](../jlink/GUIDE.md) · [SVG 图源](assets/skills/jlink.svg)

### Keil MDK · 构建后端结构

![Keil MDK · 构建后端结构](assets/skills/keil.png)

[模块说明](../keil/GUIDE.md) · [SVG 图源](assets/skills/keil.svg)

### 网络后端 · 抓包与分析结构

![网络后端 · 抓包与分析结构](assets/skills/net.png)

[模块说明](../net/GUIDE.md) · [SVG 图源](assets/skills/net.svg)

### OpenOCD · 下载与调试结构

![OpenOCD · 下载与调试结构](assets/skills/openocd.png)

[模块说明](../openocd/GUIDE.md) · [SVG 图源](assets/skills/openocd.svg)

### probe-rs · 探针与调试结构

![probe-rs · 探针与调试结构](assets/skills/probe-rs.png)

[模块说明](../probe-rs/GUIDE.md) · [SVG 图源](assets/skills/probe-rs.svg)

### 串口后端 · 收发与日志结构

![串口后端 · 收发与日志结构](assets/skills/serial.png)

[模块说明](../serial/GUIDE.md) · [SVG 图源](assets/skills/serial.svg)

### SSH · 远程操作网关结构

![SSH · 远程操作网关结构](assets/skills/ssh.png)

[模块说明](../ssh/GUIDE.md) · [SVG 图源](assets/skills/ssh.svg)

### 交互终端 · 会话结构

![交互终端 · 会话结构](assets/skills/terminal.png)

[模块说明](../terminal/GUIDE.md) · [SVG 图源](assets/skills/terminal.svg)

### Workflow · 后端编排结构

![Workflow · 后端编排结构](assets/skills/workflow.png)

[模块说明](../workflow/GUIDE.md) · [SVG 图源](assets/skills/workflow.svg)
