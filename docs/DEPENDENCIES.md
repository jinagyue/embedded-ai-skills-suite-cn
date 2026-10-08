# 依赖与功能范围

技能说明和大部分静态工具不依赖 MCU 硬件。需要对应能力时再准备相应工具，依赖存在不代表硬件连接或功能验证已经通过。

## Python

建议 Python 3.10 或更高；源码使用 `X | None` 类型语法。

| 包 | 用途 | 声明版本 |
|---|---|---|
| pyserial | 串口扫描、监控、日志、串口交互终端 | >=3.5 |
| pyelftools | ELF 段、符号与资源分析 | >=0.31 |

安装核心依赖：`python -m pip install -r requirements-tools.txt`。

工具后端的额外依赖：EIDE 配置解析需要 PyYAML；CAN 接口、DBC 解码分别需要 python-can、cantools，slcan 使用 pyserial。按需安装：`python -m pip install -r requirements-backends-optional.txt`。

## 本机工具、驱动与工程

| 功能 | 依赖 |
|---|---|
| 纯静态 .ioc/源码/MAP/Fault/RTOS 日志分析 | Python；输入文件 |
| ELF 分析 | Python + pyelftools；真实 ELF |
| 地址定位到源码行 | arm-none-eabi-addr2line；带调试信息的匹配 ELF |
| Keil 构建 | Keil MDK/UV4.exe、对应编译器与芯片支持包 |
| CMake/ARM GCC 构建 | CMake、ARM GNU Toolchain、Ninja 或 Make；匹配工程预设 |
| EIDE 构建 | VS Code EIDE 扩展中的 unify_builder、选定工具链、PyYAML |
| J-Link | SEGGER J-Link Software 与驱动；GDB 功能另需 arm-none-eabi-gdb |
| OpenOCD | OpenOCD、对应探针驱动、匹配 interface/target/board 配置 |
| probe-rs | probe-rs CLI、兼容探针驱动；GDB 功能另需 arm-none-eabi-gdb |
| 串口 | pyserial、USB 转串口驱动；正确 COM、波特率和协议 |
| CAN/CAN-FD | python-can、cantools、适配器厂商驱动或 slcan；匹配总线配置 |
| 网络抓包 | Wireshark 的 tshark；Windows 抓包需要 Npcap |
| SSH/SCP | OpenSSH 客户端；配置好的目标主机和认证 |

环境配置位于各模块 `config.json`，工程参数位于工程的 `.embeddedskills/config.json`。本机绝对路径、凭据和运行状态不提交到仓库。

## FreeRTOS 固件侧运行时采证

离线分析已有日志不需要修改固件。若要使用 `tools/freertos_runtime/freertos_runtime_probe.c/.h` 产生新日志，需要现有工程的 FreeRTOS 头文件/实现和输出回调：

- `configUSE_TRACE_FACILITY=1`，用于 Task 状态快照。
- `INCLUDE_uxTaskGetStackHighWaterMark=1`，用于有效的栈水位。
- 需要 Runtime Counter 时配置 `configGENERATE_RUN_TIME_STATS=1` 及工程时间基准。
- 堆统计需要工程的 heap 实现提供 `xPortGetFreeHeapSize()`。

探针应在目标工程中核对 API、调度与日志开销后构建和验证；禁用的统计字段不能当作实测数据。

## 本机依赖自检

运行 `python shared/scripts/check_dependencies.py --json`。此脚本只读取版本、PATH 和常见安装位置，不打开设备、不改驱动。
