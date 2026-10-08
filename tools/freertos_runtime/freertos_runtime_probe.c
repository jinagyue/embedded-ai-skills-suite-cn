#include "freertos_runtime_probe.h"

#include "FreeRTOS.h"
#include "task.h"

#include <stdio.h>
#include <string.h>

#ifndef FRTOS_RUNTIME_PROBE_MAX_TASKS
#define FRTOS_RUNTIME_PROBE_MAX_TASKS 24U
#endif

static const char *probe_state_name(eTaskState state)
{
    switch (state) {
    case eRunning:   return "RUNNING";
    case eReady:     return "READY";
    case eBlocked:   return "BLOCKED";
    case eSuspended: return "SUSPENDED";
    case eDeleted:   return "DELETED";
    case eInvalid:
    default:         return "INVALID";
    }
}

static void probe_sanitize_name(char *dst, size_t dst_size, const char *src)
{
    size_t i = 0U;
    if ((dst == NULL) || (dst_size == 0U)) {
        return;
    }
    if (src == NULL) {
        dst[0] = '\0';
        return;
    }
    while ((src[i] != '\0') && (i + 1U < dst_size)) {
        char c = src[i];
        if ((c == '"') || (c == '\\') || ((unsigned char)c < 0x20U)) {
            c = '_';
        }
        dst[i] = c;
        ++i;
    }
    dst[i] = '\0';
}

void FreeRTOS_RuntimeProbe_Dump(freertos_runtime_probe_write_fn write_fn)
{
#if (configUSE_TRACE_FACILITY == 1)
    static TaskStatus_t status[FRTOS_RUNTIME_PROBE_MAX_TASKS];
    char line[240];
    UBaseType_t count;
    UBaseType_t i;
    unsigned long total_runtime = 0UL;

    if (write_fn == NULL) {
        return;
    }

    count = uxTaskGetSystemState(status, FRTOS_RUNTIME_PROBE_MAX_TASKS, &total_runtime);
    (void)snprintf(line, sizeof(line),
                   "@FREERTOS_SNAPSHOT {\"tick\":%lu,\"task_count\":%lu,\"free_heap\":%lu,\"runtime_total\":%lu}\r\n",
                   (unsigned long)xTaskGetTickCount(),
                   (unsigned long)count,
                   (unsigned long)xPortGetFreeHeapSize(),
                   total_runtime);
    write_fn(line);

    for (i = 0U; i < count; ++i) {
        char name[configMAX_TASK_NAME_LEN + 1U];
        unsigned long hwm = 0UL;
        unsigned long runtime = 0UL;
        probe_sanitize_name(name, sizeof(name), status[i].pcTaskName);

#if (INCLUDE_uxTaskGetStackHighWaterMark == 1)
        hwm = (unsigned long)uxTaskGetStackHighWaterMark(status[i].xHandle);
#endif
#if (configGENERATE_RUN_TIME_STATS == 1)
        runtime = (unsigned long)status[i].ulRunTimeCounter;
#endif

        (void)snprintf(line, sizeof(line),
                       "@FREERTOS_TASK {\"name\":\"%s\",\"state\":\"%s\",\"priority\":%lu,\"base_priority\":%lu,\"stack_hwm_words\":%lu,\"runtime_counter\":%lu}\r\n",
                       name,
                       probe_state_name(status[i].eCurrentState),
                       (unsigned long)status[i].uxCurrentPriority,
                       (unsigned long)status[i].uxBasePriority,
                       hwm,
                       runtime);
        write_fn(line);
    }
#else
    if (write_fn != NULL) {
        write_fn("@FREERTOS_SNAPSHOT {\"error\":\"configUSE_TRACE_FACILITY must be 1\"}\r\n");
    }
#endif
}
