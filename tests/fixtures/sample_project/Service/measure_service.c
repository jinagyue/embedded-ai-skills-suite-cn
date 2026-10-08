#include "measure_service.h"
void measure_service_run(void) { HAL_GPIO_TogglePin(GPIOB, GPIO_PIN_0); }
