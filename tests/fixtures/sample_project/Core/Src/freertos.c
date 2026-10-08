#include "cmsis_os.h"
osThreadId_t commTaskHandle;
osMessageQueueId_t dataQueueHandle;
const osThreadAttr_t commTask_attributes = {
 .name = "commTask",
 .stack_size = 512 * 4,
 .priority = osPriorityNormal,
};
void CommTask(void *argument) { for (;;) { osDelay(10); } }
void MX_FREERTOS_Init(void) {
  dataQueueHandle = osMessageQueueNew(4, sizeof(int), NULL);
  commTaskHandle = osThreadNew(CommTask, NULL, &commTask_attributes);
}
