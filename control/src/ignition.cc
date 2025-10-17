#include "ignition.h"

#include <driver/gpio.h>

#include "configs/ignition_config.h"

void setup_ignition_relay() {
  gpio_reset_pin(IGNITION_GPIO_NUM);
  gpio_set_direction(IGNITION_GPIO_NUM, GPIO_MODE_OUTPUT);
}

void set_ignition_relay_high() { gpio_set_level(IGNITION_GPIO_NUM, 1); }

void set_ignition_relay_low() { gpio_set_level(IGNITION_GPIO_NUM, 0); }
