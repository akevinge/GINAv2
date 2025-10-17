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