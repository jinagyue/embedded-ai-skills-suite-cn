#include "cmsis_os.h"
void USART1_IRQHandler(void) { osThreadFlagsSet(commTaskHandle, 1); }
