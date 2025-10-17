#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "ignition.h"
#include "valve.h"

extern "C" void app_main() {
  setup_ignition_relay();
  set_ignition_relay_high();
  vTaskDelay(pdMS_TO_TICKS(10000));  // Wait 10s
  set_ignition_relay_low();

  setup_valves();

  open_valve(Valve::kOxRelease);
  open_valve(Valve::kOxN2Purge);
  open_valve(Valve::kFuelRelease);

  vTaskDelay(pdMS_TO_TICKS(1000));  // Wait a second

  close_valve(Valve::kOxRelease);
  close_valve(Valve::kOxN2Purge);
  close_valve(Valve::kFuelRelease);

  while (1) {
    vTaskDelay(pdMS_TO_TICKS(1000));
  }
}