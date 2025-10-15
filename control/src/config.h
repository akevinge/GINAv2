#pragma once

#include <driver/gpio.h>

enum class Valve {
  kOxRelease,
  kOxN2Purge,
  kFuelRelease,
  kFuelN2Purge,
  kValveMax
};

struct ValveConfig {
  Valve valve;
  gpio_num_t gpio_num;
  int max_angle;
  int close_angle;
  int open_angle;
};

// Configuration for various servo motors.
// !!!! READ BEFORE MODIFYING !!!!
// Ensure the valve type is in the same order as Valve enum variants.
// Valve enum variants are used to index this array. See get_servo_config.
constexpr ValveConfig kValveConfigs[] = {
    ValveConfig{
        .valve = Valve::kOxRelease,
        .gpio_num = GPIO_NUM_20,
        .max_angle = 180,
        .close_angle = 7,
        .open_angle = 85,
    },
    ValveConfig{
        .valve = Valve::kOxN2Purge,
        .gpio_num = GPIO_NUM_19,
        .max_angle = 270,
        .close_angle = 0,
        .open_angle = 90,
    },
};

constexpr const ValveConfig& get_valve_config(Valve valve) {
  return kValveConfigs[static_cast<int>(valve)];
}

constexpr int kValveConfigCount =
    sizeof(kValveConfigs) / sizeof(kValveConfigs[0]);