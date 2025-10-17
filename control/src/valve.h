#pragma once

enum class Valve {
  kOxRelease,
  kOxN2Purge,
  kFuelRelease,
  kFuelN2Purge,
  kValveMax
};

void setup_valves();

void open_valve(Valve valve);

void close_valve(Valve valve);
