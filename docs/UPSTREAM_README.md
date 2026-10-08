# 嵌入式 AI 开发 Skills 套件 V0.4 中文版

面向 **STM32 / ARM Cortex-M / FreeRTOS / CMSIS-RTOS2** 的中文嵌入式 AI 开发与调试工作流。V0.4 的重点是把“工程静态理解”继续推进到“**编译产物 + 运行时 RTOS + CPU Fault + 源码行定位**”。

## V0.4 核心闭环

```text
STM32CubeMX .ioc / 源码
        ↓
工程发现 + FreeRTOS/依赖/IRQ/DMA/架构扫描
        ↓
.ioc ↔ 源码一致性检查
        ↓
人工/AI语义判断 → arch-map.json → 架构门禁
        ↓
Build
        ↓
Keil .map + ELF 资源分析
        ↓
可选 Flash（默认禁止）
        ↓
串口 / RTT / SWO / ITM / GDB
        ↓
FreeRTOS Task / Stack HWM / Heap 运行时证据
        ↓
HardFault / BusFault / UsageFault / MemManage 自动解码
        ↓
arm-none-eabi-addr2line → 函数 + 源码行
        ↓
AI 最小修复 → 重建 → 重测
```

## 中文 Skills

| 目录 | 中文职责 |
|---|---|
| `00-embedded-workflow` | 总工作流编排 |
| `01-embedded-architecture` | 五层架构、依赖和机器化门禁 |
| `02-c99-embedded` | 嵌入式 C99 实现规范 |
| `03-arm-cortexm` | Cortex-M 启动/IRQ/Fault/Cache |
| `04-stm32-platform` | CubeMX/HAL/BSP/STM32 平台 |
| `05-device-service` | Device/Protocol/Service 设计 |
| `06-freertos-design` | FreeRTOS Task/IPC/ISR/栈与运行时水位 |
| `07-embedded-protocols` | UART/RS485/CAN/SPI/I2C/协议 |
| `08-debugging-bringup` | Bring-up、Fault 与在线调试 |
| `09-quality-review-testing` | 代码评审、测试、MAP/ELF 资源门禁 |
| `10-reliability-lowpower` | 可靠性、Watchdog、低功耗 |
| `11-refactor-existing` | 存量 STM32 工程重构 |
| `12-auto-debug` | AI 自动调试闭环 |
| `13-firmware-tools` | 固件分析与工程扫描工具箱 |

## V0.4 新增工具

### 1. Keil `.map` 分析器

```bash
python tools/keil_map_analyzer/keil_map_analyzer.py build/app.map \
  --json-out .embedded-ai/debug/keil_map.json \
  --report .embedded-ai/debug/KEIL_MAP_REPORT.md
```

输出 Code / RO-data / RW-data / ZI-data、估算 Flash/RAM、Execution/Load Region、对象文件贡献、最大函数和数据符号。

### 2. `arm-none-eabi-addr2line` 源码定位

```bash
python tools/addr2line_resolver/addr2line_resolver.py \
  --elf build/app.elf 0x08013A62 0x08002F11
```

也可以直接从 HardFault/串口/GDB 日志中提取地址。

### 3. HardFault 自动解码

```bash
python tools/hardfault_decoder/hardfault_decoder.py \
  --log .embedded-ai/debug/hardfault.log \
  --elf build/app.elf \
  --json-out .embedded-ai/debug/hardfault.json \
  --report .embedded-ai/debug/HARDFAULT_REPORT.md
```

支持 CFSR/HFSR/DFSR、BFAR/MMFAR、EXC_RETURN、xPSR；有 GNU Arm 工具链时继续把 PC/LR 定位到源码行。

### 4. FreeRTOS 运行时 Task / Stack / Heap

固件侧加入：

```text
tools/freertos_runtime/freertos_runtime_probe.c
tools/freertos_runtime/freertos_runtime_probe.h
```

运行时输出 `@FREERTOS_SNAPSHOT` / `@FREERTOS_TASK`，PC 侧分析：

```bash
python tools/freertos_runtime/freertos_runtime_analyzer.py serial.log \
  --json-out .embedded-ai/debug/freertos_runtime.json \
  --report .embedded-ai/debug/FREERTOS_RUNTIME.md
```

重点检查 Task 的 `stack_hwm_words`（历史最少剩余栈深度）、Heap 和 Runtime Counter。

### 5. CubeMX `.ioc` / 源码一致性检查

```bash
python shared/scripts/ioc_source_consistency.py . \
  --output .embedded-ai/debug/ioc_source_consistency.json \
  --report .embedded-ai/debug/IOC_SOURCE_CONSISTENCY.md
```

检查外设初始化、GPIO label、NVIC 优先级、DMA 和 FreeRTOS 配置是否出现漂移。

## 原有工具仍保留

```bash
python tools/serial_monitor/serial_monitor.py --list
python tools/elf_analyzer/elf_analyzer.py build/app.elf --all --json-out .embedded-ai/elf.json
python tools/architecture_checker/architecture_checker.py . --evidence
python tools/skill_validator.py .

python shared/scripts/parse_ioc.py . --json
python shared/scripts/scan_freertos.py . --json
python shared/scripts/include_graph.py .
python shared/scripts/hal_leak_check.py .
python shared/scripts/stm32_resource_audit.py .
python shared/scripts/analyze_project.py .
python shared/scripts/generate_arch_docs.py .
```

## 一键自动调试

```bash
python shared/scripts/auto_debug.py static --workspace .
python shared/scripts/auto_debug.py cycle --workspace .
```

`cycle` 会按配置自动尝试 `.ioc` 一致性检查、Build、MAP/ELF、运行观测、FreeRTOS runtime 与 HardFault 解码。默认不自动烧录；只有显式使用下面命令时才允许：

```bash
python shared/scripts/auto_debug.py cycle --workspace . --allow-flash
```

示例 `.embedded-ai/config.json`：

```json
{
  "schema_version": "0.4",
  "commands": {
    "build": "...",
    "test": null,
    "flash": "...",
    "observe": "..."
  },
  "serial": {
    "port": "COM3",
    "baud": 115200,
    "duration_s": 10,
    "mode": "both"
  },
  "freertos_runtime": {
    "stack_warn_words": 64,
    "stack_critical_words": 24,
    "stack_word_bytes": 4,
    "heap_warn_bytes": null
  },
  "auto_debug": {
    "analyze_map": true,
    "analyze_elf": true,
    "check_ioc_consistency": true,
    "decode_hardfault": true,
    "analyze_freertos_runtime": true,
    "addr2line_tool": null,
    "allow_flash": false
  }
}
```

## 推荐五层目录

```text
L5  App/ + RTOS/
 ↓
L4  Service/
 ↓
L3  Device/ + Protocol/ + BSP/Service + BSP/Board
 ↓
L2  BSP/Driver
 ↓
L1  Core/ + Drivers/      # CubeMX / CMSIS / HAL / LL
```

`Middlewares/Common/Config/Tests` 为横向基础设施。普通 STM32 单板工程不强制 `port_mcu`。

## 安装依赖

```bash
pip install -r requirements-tools.txt
```

Python 工具中只有串口与 ELF 分析需要第三方 Python 包；`addr2line` 需要你本机的 GNU Arm Embedded Toolchain。

## 自检

```bash
python tests/run_smoke_tests.py
```

V0.4 smoke test 会覆盖 CubeMX 解析、架构门禁、Keil MAP、HardFault、FreeRTOS Runtime、addr2line 缺失容错与自动调试静态链路。
