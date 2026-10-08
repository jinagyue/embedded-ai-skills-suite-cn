# ARM Cortex-M 平台知识

## 重点
- Reset → 向量表 → `Reset_Handler` → `.data/.bss` → `SystemInit` → `main`。
- Cortex-M 中断优先级数值越小，逻辑优先级越高。
- FreeRTOS 中能调用 RTOS ISR API 的中断优先级必须满足 `configMAX_SYSCALL_INTERRUPT_PRIORITY` 约束。
- HardFault 排查优先保存 R0-R3、R12、LR、PC、xPSR、CFSR、HFSR、BFAR、MMFAR。
- M7/H7 等带 Cache 的平台，DMA 缓冲区必须考虑 Cache clean/invalidate、对齐和内存区域。
- 中断只做采样、清标志、时间戳、投递事件，复杂逻辑推迟到 Task。

## 调试顺序
1. 是否能 SWD 连接；2. Reset reason；3. PC/LR；4. Fault 状态寄存器；5. 栈边界；6. 中断优先级；7. DMA/Cache；8. 再看业务代码。

## V0.4 HardFault 自动定位
建议 Fault 日志固定输出 `CFSR/HFSR/DFSR/MMFAR/BFAR/R0-R3/R12/LR/PC/xPSR/MSP/PSP`。

```bash
python tools/hardfault_decoder/hardfault_decoder.py --log hardfault.log --elf build/app.elf --report .embedded-ai/HARDFAULT_REPORT.md
```

若安装 GNU Arm Embedded Toolchain，工具会继续调用 `arm-none-eabi-addr2line` 把 PC（以及非 EXC_RETURN 的 LR）定位到函数和源码行。对 `IMPRECISERR` 不要盲信堆栈 PC。
