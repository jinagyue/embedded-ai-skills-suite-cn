# V0.4 工具契约

所有脚本都是**证据采集/复核工具**，不替代 CubeMX、编译器、链接器、FreeRTOS 官方定义、芯片参考手册和真实硬件测量。

- `parse_ioc.py`：提取 MCU、外设、Pin、NVIC、DMA 和 Middleware 配置。
- `ioc_source_consistency.py`：比较 `.ioc` 与源码中的外设初始化、GPIO label、NVIC、DMA 和 RTOS 证据；低置信度提示需要人工确认。
- `scan_freertos.py`：静态识别 Task、Queue、Mutex、Semaphore、Event、Timer 和 ISR 中 RTOS 调用。
- `freertos_runtime_probe.c/.h`：目标板侧输出结构化 Task/Stack/Heap 证据；需用户显式接入调试输出。
- `freertos_runtime_analyzer.py`：解析 `@FREERTOS_*`，检查 Stack High Water Mark 与 Heap 阈值。
- `include_graph.py`：生成 include 图并寻找低层依赖高层。
- `hal_leak_check.py`：寻找 App/Service/Protocol 中 HAL/LL/句柄泄漏。
- `stm32_resource_audit.py`：检查 Pin、DMA、IRQ、ISR 重操作和 FreeRTOS 中断优先级。
- `analyze_project.py`：聚合静态结果为 `.embedded-ai/project_model.json`。
- `generate_arch_docs.py`：生成架构、Task 和模块映射报告。
- `architecture_checker.py`：基于人工确认的 `arch-map.json` 做分层门禁。
- `serial_monitor.py`：运行期串口证据采集。
- `keil_map_analyzer.py`：解析 armlink `.map` 的 Code/RO/RW/ZI、region、组件和符号；不同 Keil 版本格式差异可能导致部分字段缺失。
- `elf_analyzer.py`：固件 ELF/Flash/RAM/符号证据采集。
- `addr2line_resolver.py`：调用外部 `arm-none-eabi-addr2line`，自身不包含 GNU 工具链。
- `hardfault_decoder.py`：解码 Cortex-M 常见 Fault 状态位；具体位是否实现取决于内核型号。
- `auto_debug.py`：只编排证据链，默认禁止自动烧录。
