# STM32 平台与 BSP

![STM32 · 配置与 BSP 结构](../docs/assets/skills/04-stm32-platform.png)

## CubeMX 原则
- `.ioc` 是硬件配置的重要事实源，必须版本控制。
- 时钟、PinMux、NVIC、DMA、外设初始化优先让 CubeMX 生成。
- 自定义代码只写入 USER CODE 区或独立模块。
- `main.c`/`freertos.c` 只做启动与装配，不承载产品业务。

## BSP Driver
```text
BSP/Driver/
  bsp_gpio.c
  bsp_uart.c
  bsp_spi.c
  bsp_i2c.c
  bsp_adc.c
  bsp_tim.c
  bsp_dma.c
  bsp_can.c
```
BSP 把 `HAL_*` 和具体句柄封装成板级稳定 API。普通 STM32 单板项目不强制 `port_mcu`；只有跨 MCU/SDK 复用成为真实需求时再增加 Port。

## 自动检查
```bash
python shared/scripts/parse_ioc.py . --json
python shared/scripts/stm32_resource_audit.py .
python shared/scripts/ioc_source_consistency.py . --report .embedded-ai/IOC_SOURCE_CONSISTENCY.md
```

V0.4 要把 `.ioc` 与源码做双向校验，重点发现外设初始化、GPIO label、NVIC 优先级、DMA 与 FreeRTOS 配置漂移。
