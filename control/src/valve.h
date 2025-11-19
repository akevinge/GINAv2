#pragma once
#include <cstdint>

enum class Valve {
  kOxRelease,
  kOxN2Purge,
  kFuelRelease,
  kFuelN2Purge,
  kValveMax
};

// Set up underlying valve GPIO pins, pwm timer, GPIO -> channel mapping.
void setup_valves();

// Open valve to configured `open_angle`. See configs/valve_config.h.
void open_valve(Valve valve);

// Close valve to configured `close_angle`. See configs/valve_config.h.
void close_valve(Valve valve);

// Set valve to specific position (0-100%).
void set_valve_position(Valve valve, uint8_t position);

// Open all valves.
void open_all_valves();

// Close all valves.
void close_all_valves();

// Set all valves to specific position (0-100%).
void set_all_valves_position(uint8_t position);