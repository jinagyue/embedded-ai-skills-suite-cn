# Device / Protocol / Service 设计

## Device
具体物理器件，例如 W25Q64、ADS8688、MPU6050、Nextion、4G DTU。Device 可依赖 BSP，不负责产品流程。

## Protocol
负责帧格式、编码/解码、CRC、命令码、字节序和边界检查。Protocol 不直接调用 UART HAL，也不决定“什么时候测量”。

## BSP Service
组合多个底层资源形成稳定数据通道，例如 `uart_stream = UART + DMA + IDLE + ringbuffer + notification`。

## Business Service
对 APP 提供“能力”而不是“硬件动作”，例如：
```c
measure_status_t measurement_start(void);
measure_status_t measurement_get_result(measure_result_t *out);
```
APP 不应知道 `huart2`、`hadc1`、DMA stream、GPIO port。
