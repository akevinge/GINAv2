#include "command_handler.h"

#include "configs/valve_config.h"
#include "esp_log.h"
#include "freertos/queue.h"
#include "freertos/task.h"
#include "lora.h"
#include "ra01s.h"
#include "valve.h"

static const char* TAG = "Command";

void close_all_valves() {
  for (int i = 0; i < static_cast<int>(Valve::kValveMax); ++i) {
    close_valve(static_cast<Valve>(i));
  }
}

void run_command(const command_t& command) {
  CommandType command_type = static_cast<CommandType>(command.command_type);
  ESP_LOGI(TAG, "RUNNING COMMAND %d", static_cast<int>(command.command_type));
  switch (command_type) {
    case CommandType::kCloseAllValves: {
      close_all_valves();
      break;
    }
    default:
      break;
  }
}

void command_exe_task(void* pvParameters) {
  QueueHandle_t command_queue = static_cast<QueueHandle_t>(pvParameters);

  command_t command;
  while (1) {
    if (xQueueReceive(command_queue, &command, pdMS_TO_TICKS(10)) == pdPASS) {
      run_command(command);
    }
  }
  vTaskDelete(NULL);
}
