/*
 * Cortex-M + GCC HardFault 采集模板。
 *
 * 集成方式：
 * 1. 将本文件/头文件复制到工程。
 * 2. main.h 必须最终包含对应 Cortex-M CMSIS 定义（SCB、__get_MSP/__get_PSP 等）。
 * 3. 在系统启动后调用 HardFaultCapture_SetWriter() 注册“故障态可工作的”输出回调。
 * 4. 用下方 HardFault_Handler 替换 stm32xxxx_it.c 里 CubeMX 生成的空 Handler。
 *
 * 注意：Fault 环境下 printf/UART DMA/RTOS API 都可能已经不可用。
 * 最可靠做法是先把 hardfault_snapshot 保存到 noinit/备份 SRAM/Flash，重启后再输出。
 * 本模板为了便于 bring-up，提供直接文本输出版本。
 */
#include "hardfault_capture_gcc.h"
#include "main.h"

#include <stdint.h>
#include <stdio.h>

static hardfault_capture_write_fn g_writer = 0;

void HardFaultCapture_SetWriter(hardfault_capture_write_fn writer)
{
    g_writer = writer;
}

static void hf_write_line(const char *line)
{
    if (g_writer != 0) {
        g_writer(line);
    }
}

void HardFault_C_Handler(unsigned int *stack_frame, unsigned int exc_return)
{
    char line[192];
    uint32_t r0   = stack_frame[0];
    uint32_t r1   = stack_frame[1];
    uint32_t r2   = stack_frame[2];
    uint32_t r3   = stack_frame[3];
    uint32_t r12  = stack_frame[4];
    uint32_t lr   = stack_frame[5];
    uint32_t pc   = stack_frame[6];
    uint32_t xpsr = stack_frame[7];

    hf_write_line("HardFault!\r\n");
    (void)snprintf(line, sizeof(line),
                   "CFSR=0x%08lX HFSR=0x%08lX DFSR=0x%08lX MMFAR=0x%08lX BFAR=0x%08lX\r\n",
                   (unsigned long)SCB->CFSR, (unsigned long)SCB->HFSR,
                   (unsigned long)SCB->DFSR, (unsigned long)SCB->MMFAR,
                   (unsigned long)SCB->BFAR);
    hf_write_line(line);

    (void)snprintf(line, sizeof(line),
                   "R0=0x%08lX R1=0x%08lX R2=0x%08lX R3=0x%08lX R12=0x%08lX\r\n",
                   (unsigned long)r0, (unsigned long)r1, (unsigned long)r2,
                   (unsigned long)r3, (unsigned long)r12);
    hf_write_line(line);

    (void)snprintf(line, sizeof(line),
                   "LR=0x%08lX PC=0x%08lX xPSR=0x%08lX EXC_RETURN=0x%08lX MSP=0x%08lX PSP=0x%08lX\r\n",
                   (unsigned long)lr, (unsigned long)pc, (unsigned long)xpsr,
                   (unsigned long)exc_return, (unsigned long)__get_MSP(),
                   (unsigned long)__get_PSP());
    hf_write_line(line);

    __DSB();
    __ISB();
    for (;;) {
        __NOP();
    }
}

/*
 * 如果工程已有 HardFault_Handler，请不要保留两个定义。
 * 用这一实现替换 CubeMX 生成的空 Handler。
 */
__attribute__((naked)) void HardFault_Handler(void)
{
    __asm volatile(
        "tst lr, #4            \n"
        "ite eq                \n"
        "mrseq r0, msp         \n"
        "mrsne r0, psp         \n"
        "mov r1, lr            \n"
        "b HardFault_C_Handler \n"
    );
}
