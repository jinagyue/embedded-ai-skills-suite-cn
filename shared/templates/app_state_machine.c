#include "app_state_machine.h"

typedef enum {
    APP_STATE_IDLE = 0,
    APP_STATE_START,
    APP_STATE_WAIT,
    APP_STATE_PROCESS,
    APP_STATE_ERROR,
} app_state_t;

static struct {
    app_state_t state;
    uint32_t start_tick;
} s_ctx;

void app_sm_init(void)
{
    s_ctx.state = APP_STATE_IDLE;
    s_ctx.start_tick = 0U;
}

void app_sm_process(void)
{
    switch (s_ctx.state) {
    case APP_STATE_IDLE:
        break;
    case APP_STATE_START:
        /* call service start */
        s_ctx.state = APP_STATE_WAIT;
        break;
    case APP_STATE_WAIT:
        /* check service result or timeout */
        break;
    case APP_STATE_PROCESS:
        /* orchestrate services */
        s_ctx.state = APP_STATE_IDLE;
        break;
    case APP_STATE_ERROR:
    default:
        /* report/recover */
        s_ctx.state = APP_STATE_IDLE;
        break;
    }
}
