#include "ignition.h"

#include <driver/gpio.h>

#include "configs/ignition_config.h"

void setup_ignition_relay() {
  gpio_reset_pin(kIgnitionGpio);
  gpio_set_direction(kIgnitionGpio, GPIO_MODE_OUTPUT);
}

void set_ignition_relay_high() { gpio_set_level(kIgnitionGpio, 1); }

void set_ignition_relay_low() { gpio_set_level(kIgnitionGpio, 0); }
