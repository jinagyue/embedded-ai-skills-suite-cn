# V0.4 更新记录

## 版本目标

V0.4 把 V0.3 的“工程理解 + ELF/串口证据”扩展成更完整的 **STM32 真机故障定位闭环**。

## 新增

### Keil `.map` 分析器
新增：

```text
tools/keil_map_analyzer/keil_map_analyzer.py
```

支持：
- Program Size：Code / RO-data / RW-data / ZI-data；
- Flash/RAM 估算；
- Execution / Load Region；
- Image component sizes；
- 最大函数、最大数据符号；
- JSON / Markdown 报告。

### FreeRTOS 运行时 Task / Stack / Heap
新增：

```text
tools/freertos_runtime/freertos_runtime_probe.c
tools/freertos_runtime/freertos_runtime_probe.h
tools/freertos_runtime/freertos_runtime_analyzer.py
```

目标板可输出 `@FREERTOS_SNAPSHOT` / `@FREERTOS_TASK`，PC 侧分析 Task 状态、Stack High Water Mark、Heap 和 Runtime Counter，并按阈值产生风险。

### HardFault 自动解码
新增：

```text
tools/hardfault_decoder/hardfault_decoder.py
```

支持：
- CFSR/HFSR/DFSR；
- BFAR/MMFAR；
- R0-R3/R12/LR/PC/xPSR/MSP/PSP；
- EXC_RETURN；
- 精确/非精确 BusFault 等快捷诊断；
- 可选 ELF 源码定位。

### addr2line 自动源码定位
新增：

```text
tools/addr2line_resolver/addr2line_resolver.py
```

支持直接地址和从日志提取地址，调用 `arm-none-eabi-addr2line` 输出函数、源码文件和行号。

### CubeMX `.ioc` / 源码一致性检查
新增：

```text
shared/scripts/ioc_source_consistency.py
```

检查：
- IOC 外设与源码初始化漂移；
- GPIO label 与 `*_Pin` / `*_GPIO_Port`；
- NVIC 优先级不一致；
- DMA 初始化/绑定证据；
- FreeRTOS 启用但源码缺少 Kernel/Task 初始化。

## 自动调试链路升级

`shared/scripts/auto_debug.py` 升级为 V0.4，新增自动编排：

```text
.ioc/source consistency
→ Build
→ Keil MAP
→ ELF
→ optional Flash
→ Observe/Serial
→ FreeRTOS runtime
→ HardFault decode
→ addr2line
```

仍然保持：**默认禁止自动烧录**。

## 中文 Skills 更新

重点扩展：
- `03-arm-cortexm`：Fault 解码与 addr2line；
- `04-stm32-platform`：`.ioc`/源码一致性；
- `06-freertos-design`：运行时 Stack HWM；
- `08-debugging-bringup`：Fault 闭环；
- `09-quality-review-testing`：Keil MAP 资源门禁；
- `12-auto-debug`：V0.4 自动调试链路；
- `13-firmware-tools`：新增全部工具入口。

## 测试

`tests/run_smoke_tests.py` 增加：
- Keil MAP 解析；
- HardFault CFSR/HFSR/EXC_RETURN；
- FreeRTOS runtime Stack HWM；
- `.ioc` / 源码 NVIC 漂移；
- addr2line 缺失容错；
- V0.4 自动调试静态编排。
