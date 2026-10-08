# 嵌入式固件工具箱

## 工具清单
| 工具 | 作用 |
|---|---|
| `tools/serial_monitor/serial_monitor.py` | 串口 ASCII/HEX、时间戳、日志、自动重连、限时采集 |
| `tools/keil_map_analyzer/keil_map_analyzer.py` | Keil MAP：Code/RO/RW/ZI、region、组件与最大符号 |
| `tools/elf_analyzer/elf_analyzer.py` | ELF Section/符号、Flash/RAM、最大函数/对象 |
| `tools/addr2line_resolver/addr2line_resolver.py` | `arm-none-eabi-addr2line` 地址→函数→源码行 |
| `tools/hardfault_decoder/hardfault_decoder.py` | CFSR/HFSR/DFSR/BFAR/MMFAR、EXC_RETURN、xPSR 解码 |
| `tools/freertos_runtime/freertos_runtime_analyzer.py` | Task 状态、Stack HWM、Heap、Runtime 运行时分析 |
| `tools/freertos_runtime/freertos_runtime_probe.c/.h` | 固件侧 FreeRTOS 结构化运行时探针 |
| `tools/architecture_checker/architecture_checker.py` | 基于 `arch-map.json` 复核分层和 HAL 泄漏 |
| `tools/skill_validator.py` | 检查 SKILL.md Front Matter 和中文化 |
| `shared/scripts/parse_ioc.py` | CubeMX `.ioc` 解析 |
| `shared/scripts/ioc_source_consistency.py` | `.ioc` 与源码 GPIO/NVIC/DMA/外设/RTOS 漂移检查 |
| `shared/scripts/scan_freertos.py` | 静态 Task/Queue/Mutex/Event/Timer 扫描 |
| `shared/scripts/include_graph.py` | include 依赖图 |
| `shared/scripts/hal_leak_check.py` | HAL/LL 跨层泄漏 |
| `shared/scripts/stm32_resource_audit.py` | Pin/DMA/IRQ/ISR 审计 |
| `shared/scripts/analyze_project.py` | 一键工程模型 |
| `shared/scripts/generate_arch_docs.py` | 自动生成架构/Task/模块文档 |

## 使用顺序
先用静态工具建立事实；再由 AI/工程师做架构语义判断；编译后用 MAP/ELF 验证资源；真机运行后用串口/RTT/GDB 收集证据；出现 Fault 时先解码寄存器和 PC/LR，再修改代码。

**工具负责采证和复核，不替代人的系统语义判断、芯片参考手册或真实硬件测量。**
