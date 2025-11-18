#pragma once

#include <driver/gpio.h>

constexpr gpio_num_t IGNITION_GPIO_NUM = GPIO_NUM_1;
constexpr int IGNITION_RELAY_PULSE_MS = 5000;  // Pulse duration to activate igniter