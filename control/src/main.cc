#include "config.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "valve.h"

extern "C" void app_main() {
  setup_valves();

  vTaskDelay(pdMS_TO_TICKS(1000));  // Wait a second
  open_valve(Valve::kOxRelease);

  vTaskDelay(pdMS_TO_TICKS(1000));  // Wait a second
  close_valve(Valve::kOxRelease);

  vTaskDelay(pdMS_TO_TICKS(1000));  // Wait a second
  open_valve(Valve::kOxN2Purge);

  vTaskDelay(pdMS_TO_TICKS(1000));  // Wait a second
  close_valve(Valve::kOxN2Purge);

  while (1) {
    vTaskDelay(pdMS_TO_TICKS(1000));
  }
}