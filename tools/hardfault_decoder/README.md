# HardFault 自动解码器

建议固件在 HardFault 中输出至少：

```text
CFSR=0x00008200 HFSR=0x40000000 BFAR=0x20010004
R0=0x00000000 R1=0x20010004 R2=0x00000001 R3=0x00000000
R12=0x00000000 LR=0x08002F11 PC=0x08013A62 xPSR=0x21000000
MSP=0x2001FF00 PSP=0x2000F000
```

解码：

```bash
python tools/hardfault_decoder/hardfault_decoder.py \
  --log hardfault.log \
  --elf build/app.elf \
  --json-out .embedded-ai/debug/hardfault.json \
  --report .embedded-ai/debug/HARDFAULT_REPORT.md
```

工具会解码 CFSR/HFSR/DFSR、EXC_RETURN、xPSR，并在存在 GNU Arm 工具链时调用 `arm-none-eabi-addr2line` 定位 PC/LR 源码行。

## GCC 目标板采集模板

套件额外提供：

```text
shared/templates/hardfault_capture_gcc.c
shared/templates/hardfault_capture_gcc.h
```

它会保存/输出堆栈寄存器、Fault 状态寄存器和 `EXC_RETURN`。如果工程已经有 CubeMX 生成的 `HardFault_Handler`，必须**替换其实现**，不要保留两个同名 Handler。

Fault 环境下 UART DMA、RTOS API、`printf` 都可能失效。产品化项目更建议先把快照保存到 `.noinit`/备份 SRAM，再重启后输出；模板的直接文本输出更适合 bring-up。
