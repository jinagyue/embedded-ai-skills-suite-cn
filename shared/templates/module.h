#ifndef MODULE_H
#define MODULE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef enum {
    MODULE_OK = 0,
    MODULE_EINVAL,
    MODULE_EBUSY,
    MODULE_ETIMEOUT,
    MODULE_EIO,
} module_status_t;

typedef struct {
    uint32_t timeout_ms;
} module_cfg_t;

module_status_t module_init(const module_cfg_t *cfg);
module_status_t module_start(void);
module_status_t module_process(void);
module_status_t module_stop(void);

#endif
