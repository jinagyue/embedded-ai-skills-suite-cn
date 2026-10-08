# FreeRTOS 运行时 Task / Stack 采集

V0.4 把“静态扫描”扩展到真实运行时证据。

## 1. 固件侧接入

复制：

```text
freertos_runtime_probe.c
freertos_runtime_probe.h
```

FreeRTOSConfig.h 建议：

```c
#define configUSE_TRACE_FACILITY 1
#define INCLUDE_uxTaskGetStackHighWaterMark 1
```

然后把输出回调接到 UART/RTT，例如：

```c
static void debug_write(const char *s)
{
    HAL_UART_Transmit(&huart1, (uint8_t *)s, strlen(s), 100);
}

FreeRTOS_RuntimeProbe_Dump(debug_write);
```

固件会输出：

```text
@FREERTOS_SNAPSHOT {"tick":12000,"task_count":4,"free_heap":7168,"runtime_total":50000}
@FREERTOS_TASK {"name":"comm","state":"BLOCKED","priority":3,"base_priority":3,"stack_hwm_words":42,"runtime_counter":5100}
```

## 2. PC 侧分析

```bash
python tools/freertos_runtime/freertos_runtime_analyzer.py serial.log \
  --stack-warn-words 64 \
  --stack-critical-words 24 \
  --json-out .embedded-ai/debug/freertos_runtime.json \
  --report .embedded-ai/debug/FREERTOS_RUNTIME.md
```

`stack_hwm_words` 是历史最少剩余栈深度（High Water Mark），不是“当前已用栈”。Cortex-M 常见 `StackType_t=4 B`，但工具允许用 `--stack-word-bytes` 修改。
