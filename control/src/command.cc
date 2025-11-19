#include "command.h"

#include "configs/ignition_config.h"
#include "configs/lora_config.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"
#include "ignition.h"
#include "lora.h"
#include "valve.h"

static const char* TAG = "COMMAND_EXE";

void run_ignition_sequence() {
  set_ignition_relay_high();
  open_valve(Valve::kFuelRelease);
  open_valve(Valve::kOxRelease);

  vTaskDelay(pdMS_TO_TICKS(5000));

  set_ignition_relay_low();
  close_valve(Valve::kFuelRelease);
  close_valve(Valve::kOxRelease);
}

void run_command(command_t& command) {
  ESP_LOGI(TAG, "Executing command with action", command.action);
  switch (command.action) {
    case COMMAND_ACTION_CLOSE_ALL_VALVES: {
      close_all_valves();
      break;
    }
    case COMMAND_ACTION_OPEN_ALL_VALVES: {
      open_all_valves();
      break;
    }
    case COMMAND_ACTION_START_IGNITION_SEQUENCE: {
      ESP_LOGI(TAG, "Starting ignition sequence");
      run_ignition_sequence();
      break;
    }
    case COMMAND_ACTION_OPEN_VALVE: {
      Valve valve = static_cast<Valve>(command.parameters[0]);
      open_valve(valve);
      break;
    }
    case COMMAND_ACTION_CLOSE_VALVE: {
      Valve valve = static_cast<Valve>(command.parameters[0]);
      close_valve(valve);
      break;
    }
    default: {
      ESP_LOGW(TAG, "Unknown command action: %d", command.action);
      break;
    }
  }
}

void command_exe_task(void* pvParameters) {
  QueueHandle_t command_queue = static_cast<QueueHandle_t>(pvParameters);

  ESP_LOGI(TAG, "Starting Command Execution Task");
  while (1) {
    command_t command;
    if (xQueueReceive(command_queue, &command, portMAX_DELAY) == pdPASS) {
      run_command(command);
    }
  }
}