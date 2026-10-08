# 嵌入式通信与协议

## 推荐链路
```text
APP/Service
  ↓ 语义命令/结果
Protocol
  ↓ 帧/字节
BSP Service / Link
  ↓ 流/消息
BSP Driver
  ↓ HAL
UART/CAN/SPI/I2C/USB
```

## UART 不定长高吞吐
优先 `DMA + IDLE → 环形缓冲区/双缓冲 → Task 通知 → Protocol parser`。回调只记录收到的数据段并通知 Task。

## 协议必须处理
帧界定、长度、CRC、超时、重同步、字节序、版本号、未知命令、缓存上限和异常输入。禁止在 FreeRTOS Task 里到处散落 `strtok/sscanf/strcmp`。
