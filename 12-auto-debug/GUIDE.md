# AI 自动调试闭环

## 安全原则
默认 **禁止自动烧录**。只有用户明确允许或项目配置 `allow_flash=true` 才执行 Flash。

## V0.4 固定链路
```text
STM32 工程 / .ioc
      ↓
静态扫描 + 架构/IRQ/DMA/RTOS 检查
      ↓
.ioc ↔ 源码资源一致性检查
      ↓
Build
      ↓
Keil .map + ELF 分析
      ↓
可选 Flash
      ↓
串口 / RTT / SWO / ITM / GDB 采证
      ↓
FreeRTOS Task/Stack/Heap 运行时分析
      ↓
HardFault CFSR/HFSR/BFAR/MMFAR/PC/LR 解码
      ↓
arm-none-eabi-addr2line → 源码文件:行号
      ↓
AI 最小修改
      ↓
重新 Build → 重新采证 → 比较证据
```

## 入口
```bash
python shared/scripts/auto_debug.py plan --workspace .
python shared/scripts/auto_debug.py static --workspace .
python shared/scripts/auto_debug.py diagnose --workspace .
python shared/scripts/auto_debug.py cycle --workspace .
python shared/scripts/auto_debug.py cycle --workspace . --allow-flash
```

## V0.4 自动证据
当工程/日志中存在对应信息时，`cycle` 会自动尝试：

- `ioc_source_consistency.py`：检查 CubeMX 配置与源码漂移；
- `keil_map_analyzer.py`：分析 `.map` 中 Code/RO/RW/ZI、region、组件与符号；
- `elf_analyzer.py`：分析 ELF Section/符号/Flash/RAM；
- `freertos_runtime_analyzer.py`：解析 `@FREERTOS_*` 运行时记录；
- `hardfault_decoder.py`：解码 Cortex-M Fault，并在有 ELF/工具链时 addr2line 定位。

## 故障优先级
P0：HardFault/BusFault/UsageFault/MemManage、IRQ 优先级错误；P1：栈余量过低/栈溢出/Heap/Watchdog/链接区溢出；P2：DMA/UART/I2C/FatFs/死锁/超时；P3：协议与状态机；P4：架构清理。

动态观测可桥接 `zhinkgit/embeddedskills` 的 Keil/GCC/EIDE + J-Link/OpenOCD/probe-rs 工作流；本套件负责项目理解、静态检查、MAP/ELF/串口/RTOS/Fault 结构化证据与 AI 修复决策。
