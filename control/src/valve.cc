#include "valve.h"

#include "configs/valve_config.h"
#include "servo.h"

void setup_valves() {
  setup_servo_pwm_timer();
  for (const ValveConfig& valve_config : VALVE_CONFIGS) {
    setup_servo_pin(valve_config.gpio_num);
  }
}

void open_valve(Valve valve) {
  const ValveConfig& config = get_valve_config(valve);
  set_servo_angle(config.gpio_num, config.open_angle, config.max_angle);
}

void close_valve(Valve valve) {
  const ValveConfig& config = get_valve_config(valve);
  set_servo_angle(config.gpio_num, config.close_angle, config.max_angle);
}

void set_valve_position(Valve valve, uint8_t position) {
  const ValveConfig& config = get_valve_config(valve);
  uint8_t angle = (position * config.max_angle) / 100;
  set_servo_angle(config.gpio_num, angle, config.max_angle);
}

void open_all_valves() {
  for (const ValveConfig& valve_config : VALVE_CONFIGS) {
    set_servo_angle(valve_config.gpio_num, valve_config.open_angle, valve_config.max_angle);
  }
}

void close_all_valves() {
  for (const ValveConfig& valve_config : VALVE_CONFIGS) {
    set_servo_angle(valve_config.gpio_num, valve_config.close_angle, valve_config.max_angle);
  }
}

void set_all_valves_position(uint8_t position) {
  for (const ValveConfig& valve_config : VALVE_CONFIGS) {
    uint8_t angle = (position * valve_config.max_angle) / 100;
    set_servo_angle(valve_config.gpio_num, angle, valve_config.max_angle);
  }
}