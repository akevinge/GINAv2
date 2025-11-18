#pragma once

#include "configs/valve_config.h"

// Set up underlying valve GPIO pins, pwm timer, GPIO -> channel mapping.
void setup_valves();

// Open valve to configured `open_angle`. See configs/valve_config.h.
void open_valve(Valve valve);

// Close valve to configured `close_angle`. See configs/valve_config.h.
void close_valve(Valve valve);
