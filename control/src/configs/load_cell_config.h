#pragma once

#include <driver/gpio.h>

// Pin configuration for the HX711 load cell amplifier.
constexpr gpio_num_t HX711_DOUT_GPIO_NUM = GPIO_NUM_48;
constexpr gpio_num_t HX711_PD_SCK_GPIO_NUM = GPIO_NUM_47;
//constexpr hx711_gain_t HX711_GAIN = HX711_GAIN_A_128;

// How long to wait for the HX711 to become ready.
constexpr int HX711_MAX_TIMEOUT_MS = 500;

// Number of samples to average when reading from the HX711.
constexpr int HX711_AVG_SAMPLE_COUNT = 5;