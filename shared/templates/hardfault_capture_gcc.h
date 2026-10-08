#ifndef HARDFAULT_CAPTURE_GCC_H
#define HARDFAULT_CAPTURE_GCC_H

#ifdef __cplusplus
extern "C" {
#endif

typedef void (*hardfault_capture_write_fn)(const char *text);

/* 在系统启动时注册一个“尽量简单、无动态内存、无 RTOS 阻塞”的输出函数。 */
void HardFaultCapture_SetWriter(hardfault_capture_write_fn writer);

/* 由 naked HardFault_Handler 跳转进入；通常不要直接调用。 */
void HardFault_C_Handler(unsigned int *stack_frame, unsigned int exc_return);

#ifdef __cplusplus
}
#endif

#endif
