# AI 自动调试参考 V0.4

## 证据优先级
1. CPU Fault 上下文：PC/LR/MSP/PSP、CFSR/HFSR/DFSR/BFAR/MMFAR。
2. `addr2line` 解析出的函数与源码行，以及对应 ELF/MAP 构建产物。
3. 编译和链接器诊断，Keil MAP/ELF 的 Flash/RAM/region 变化。
4. FreeRTOS assert、Task Stack High Water Mark、Heap、Watchdog reset reason。
5. RTT/SWO/ITM/串口等运行日志。
6. `.ioc` / 源码资源一致性、IRQ/DMA、静态架构检查。
7. 没有证据的猜测只能作为待验证假设。

## V0.4 自动链路
```text
static audit
  → ioc/source consistency
  → build
  → map + elf
  → optional flash
  → observe
  → FreeRTOS runtime analysis
  → HardFault decode
  → addr2line
  → minimal patch
  → repeat
```

## 后端
| 后端 | 烧录 | GDB崩溃报告 | 运行观测 |
|---|---:|---:|---|
| J-Link | 是 | 是 | RTT/SWO |
| OpenOCD | 是 | 是 | ITM/semihosting/telnet |
| probe-rs | 是 | 是 | RTT |
| Serial | 否 | 否 | UART日志 |

## 停止条件
- 修复后同一复现用例稳定通过；
- 达到最大迭代次数；
- 新一轮没有新增证据；
- 下一步需要危险硬件动作但用户未授权；
- 必须依赖示波器/逻辑分析仪/真实负载等外部测量。
