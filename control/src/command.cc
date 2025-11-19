#include "valve.h"
#include "ignition.h"
#include "lora.h"
#include "configs/lora_config.h"
#include "configs/ignition_config.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "command.h"

static const char *TAG = "COMMAND_EXE";

void command_exe_task(void *pvParameters){
  QueueHandle_t command_queue = static_cast<QueueHandle_t>(pvParameters);
  
  ESP_LOGI(TAG, "Starting Command Execution Task");
  while (1){
    command_t command;
    if (xQueueReceive(command_queue, &command, portMAX_DELAY) == pdPASS){
        ESP_LOGI(TAG, "Executing command for target %d, type %d", command.target, command.command_type);
        if (command.target == COMMAND_TARGET_SERVO){
            command_servo_execute(command);
        } else if (command.target == COMMAND_TARGET_IGNITER){
            if (command.command_type == COMMAND_ACTION_IGNITER_START){
                ESP_LOGI(TAG, "Starting igniter");
                set_ignition_relay_high();
                vTaskDelay(pdMS_TO_TICKS(IGNITION_RELAY_PULSE_MS));
                set_ignition_relay_low();
            }
        }
    }
  }
}

void command_servo_execute(const command_t command){
    if (command.command_type == COMMAND_ACTION_SERVO_OPEN){
        if (command.parameters[0] == COMMAND_PARAM_SERVO_ALL){
            ESP_LOGI(TAG, "Opening all servos");
            //open_all_valves();
        } else {
            Valve servo_id = static_cast<Valve>(command.parameters[0]);
            ESP_LOGI(TAG, "Opening servo %d", servo_id);
            //open_valve(servo_id);
        }
    } else if (command.command_type == COMMAND_ACTION_SERVO_CLOSE){
        if (command.parameters[0] == COMMAND_PARAM_SERVO_ALL){
            ESP_LOGI(TAG, "Closing all servos");
            //close_all_valves();
        } else {
            Valve servo_id = static_cast<Valve>(command.parameters[0]);
            ESP_LOGI(TAG, "Closing servo %d", servo_id);
            //close_valve(servo_id);
        }
    } else if (command.command_type == COMMAND_ACTION_SERVO_SET){
        if (command.parameters[0] == COMMAND_PARAM_SERVO_ALL){
            uint8_t position = command.parameters[1];
            ESP_LOGI(TAG, "Setting all servos to position %d", position);
            //set_all_valves_position(position);
        } else {
            Valve servo_id = static_cast<Valve>(command.parameters[0]);
            uint8_t position = command.parameters[1];
            ESP_LOGI(TAG, "Setting servo %d to position %d", servo_id, position);
            //set_valve_position(servo_id, position);
        }
    }
}