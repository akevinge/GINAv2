#pragma once

#include <driver/gpio.h>

enum class Valve {
  kPressurizeFuelTank,
  kPreslugFuel,
  kN2PurgeFuelTankBypass,
  kN2PurgeGox,
  kPreslugGox,
  kGoxRelease,
  kFuelRelease,
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
// 7, 5, 38, 39
constexpr ValveConfig VALVE_CONFIGS[] = {
    ValveConfig{
        .valve = Valve::kPressurizeFuelTank,
        .gpio_num = GPIO_NUM_19,
        .max_angle = 180,
        .close_angle = 180,
        .open_angle = 90,
    },
    ValveConfig{
        .valve = Valve::kPreslugFuel,
        .gpio_num = GPIO_NUM_20,
        .max_angle = 180,
        .close_angle = 180,
        .open_angle = 85,
    },
    ValveConfig{
        .valve = Valve::kN2PurgeFuelTankBypass,
        .gpio_num = GPIO_NUM_21,
        .max_angle = 180,
        .close_angle = 180,
        .open_angle = 85,
    },
    ValveConfig{
        .valve = Valve::kN2PurgeGox,
        .gpio_num = GPIO_NUM_26,
        .max_angle = 180,
        .close_angle = 85,
        .open_angle = 0,
    },
    ValveConfig{
        .valve = Valve::kPreslugGox,
        .gpio_num = GPIO_NUM_48,
        .max_angle = 180,
        .close_angle = 85,
        .open_angle = 0,
    },
    ValveConfig{
        .valve = Valve::kGoxRelease,
        .gpio_num = GPIO_NUM_47,
        .max_angle = 180,
        .close_angle = 85,
        .open_angle = 0,
    },
    ValveConfig{
        .valve = Valve::kFuelRelease,
        .gpio_num = GPIO_NUM_33,
        .max_angle = 180,
        .close_angle = 80,
        .open_angle = 0,
    },

};

constexpr const ValveConfig& get_valve_config(Valve valve) {
  return VALVE_CONFIGS[static_cast<int>(valve)];
}
