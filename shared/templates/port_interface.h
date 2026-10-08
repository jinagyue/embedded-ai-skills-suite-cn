#ifndef PORT_INTERFACE_H
#define PORT_INTERFACE_H

#include <stddef.h>
#include <stdint.h>

typedef struct {
    int (*write)(const uint8_t *data, size_t len, uint32_t timeout_ms);
    uint32_t (*tick_ms)(void);
} io_port_t;

#endif
