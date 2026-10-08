#ifndef FREERTOS_RUNTIME_PROBE_H
#define FREERTOS_RUNTIME_PROBE_H

#ifdef __cplusplus
extern "C" {
#endif

typedef void (*freertos_runtime_probe_write_fn)(const char *text);

/*
 * 输出两类结构化行：
 * @FREERTOS_SNAPSHOT {...}
 * @FREERTOS_TASK {...}
 *
 * 需要 configUSE_TRACE_FACILITY == 1。
 * 若希望 stack_hwm_words 有效，建议 INCLUDE_uxTaskGetStackHighWaterMark == 1。
 */
void FreeRTOS_RuntimeProbe_Dump(freertos_runtime_probe_write_fn write_fn);

#ifdef __cplusplus
}
#endif

#endif
