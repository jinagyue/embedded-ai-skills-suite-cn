#include "bsp_uart.h"
int bsp_uart_write(const void *p, int n) { return HAL_UART_Transmit(&huart1, (void*)p, n, 100); }
