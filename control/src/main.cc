//#include <hx711.h>
#include <stdio.h>

#include <cstdint>

#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "ignition.h"
#include "load_cell.h"
#include "lora.h"
#include "pt.h"
#include "pt_adc.h"
#include "valve.h"
#include "lora.h"
#include "uartcom.h"
#include "sensor_management.h"
#include <stdio.h>
#include "esp_adc/adc_oneshot.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
#include "command.h"
#include "configs/lora_config.h"

#define SENSOR1_PIN ADC_CHANNEL_3   // Example: GPIO4  (ADC1_CH3)
#define SENSOR2_PIN ADC_CHANNEL_4   // Example: GPIO5  (ADC1_CH4)


static const char *TAG = "MAIN";
static adc_cali_handle_t adc_cali_handle = NULL;

static bool init_adc_calibration(adc_unit_t unit, adc_cali_handle_t *out_handle)
{
    adc_cali_curve_fitting_config_t cali_config = {
        .unit_id = unit,
        .atten = ADC_ATTEN_DB_11,
        .bitwidth = ADC_BITWIDTH_12,
    };
    return (adc_cali_create_scheme_curve_fitting(&cali_config, out_handle) == ESP_OK);
}

// `command_exe_task` is implemented in `command.cc`. Do not define it here
// to avoid multiple-definition linker errors.

void setup_lora_tasks(){
  #ifdef CONFIG_AWAY_SENDER
    ESP_LOGI(TAG, "Starting Away Sender Configuration");
    
    QueueHandle_t sensor_queue;
    sensor_queue = xQueueCreate(50, sizeof(sensor_data_t)); // Queue to hold sensor data

    configure_lora();
    xTaskCreatePinnedToCore(poll_sensor_task, "Poll_Sensor_Task", 4096, (void*)sensor_queue, 1, NULL, tskNO_AFFINITY);
    xTaskCreatePinnedToCore(away_tx_task, "LoRa_TX_Task", 8192, (void*)sensor_queue, 5, NULL, tskNO_AFFINITY);
  #endif // CONFIG_AWAY_SENDER
  #ifdef CONFIG_HOME_RECEIVER
    ESP_LOGI(TAG, "Starting Home Receiver Configuration");
    
    QueueHandle_t home_sensor_queue;
    home_sensor_queue = xQueueCreate(50, sizeof(sensor_data_t)); // Queue to hold incoming telemetry batches
    
    configure_lora();
    xTaskCreatePinnedToCore(home_rx_task, "LoRa_RX_Task", 8192, (void*)home_sensor_queue, 5, NULL, tskNO_AFFINITY);
    xTaskCreatePinnedToCore(telemetry_uartcom_task, "Telemetry_Uartcom_Task", 8192, (void*)home_sensor_queue, 5, NULL, tskNO_AFFINITY);
    int j = 0;
    while(1){
      j++;
      ESP_LOGE(TAG, "Sending test sensor data to UART task %d", sizeof(sensor_data_t));
        sensor_data_t data;
        data.timestamp = xTaskGetTickCount();
        for (int i = 0; i < 6; i++){
            data.pt_readings[i] = i * 10 + j;  // Dummy data for testing
        }
        data.load_cell_reading = 42;  // Dummy data for testing
        if (xQueueSend(home_sensor_queue, &data, portMAX_DELAY) != pdPASS) {
            ESP_LOGI(TAG, "Failed to enqueue test sensor data");
        }
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
  #endif // CONFIG_HOME_RECEIVER
  #ifdef CONFIG_AWAY_RECEIVER
    ESP_LOGI(TAG, "Starting Away Receiver Configuration");
    
    QueueHandle_t command_queue;
    command_queue = xQueueCreate(20, sizeof(command_t)); // Queue to hold incoming commands

    configure_lora();
    xTaskCreatePinnedToCore(away_rx_task, "Away_RX_Task", 8192, (void*)command_queue, 5, NULL, tskNO_AFFINITY);
    xTaskCreatePinnedToCore(command_exe_task, "Command_Exe_Task", 8192, (void*)command_queue, 5, NULL, tskNO_AFFINITY);
  #endif // CONFIG_AWAY_RECEIVER
  #ifdef CONFIG_HOME_SENDER
    ESP_LOGI(TAG, "Starting Home Sender Configuration");
    
    QueueHandle_t command_queue;
    command_queue = xQueueCreate(20, sizeof(command_t)); // Queue to hold commands from COM

    configure_lora();
    xTaskCreatePinnedToCore(home_tx_task, "Home_TX_Task", 8192, (void*)command_queue, 5, NULL, tskNO_AFFINITY);
    xTaskCreatePinnedToCore(home_com_monitor_task, "Home_Com_Monitor_Task", 4096, (void*)command_queue, 1, NULL, tskNO_AFFINITY);
    command_t cmd;
    cmd.target = COMMAND_TARGET_SERVO;  
    cmd.command_type = COMMAND_ACTION_SERVO_OPEN;
    cmd.parameters[0] = COMMAND_PARAM_SERVO_ALL;
    if (xQueueSend(command_queue, &cmd, portMAX_DELAY) != pdPASS) {
      ESP_LOGI(TAG, "Failed to enqueue initial command");
    }
    cmd.target = COMMAND_TARGET_SERVO;  
    cmd.command_type = COMMAND_ACTION_SERVO_CLOSE;
    cmd.parameters[0] = COMMAND_PARAM_SERVO_ALL;
    if (xQueueSend(command_queue, &cmd, portMAX_DELAY) != pdPASS) {
      ESP_LOGI(TAG, "Failed to enqueue initial command");
    }
    cmd.target = COMMAND_TARGET_SERVO;  
    cmd.command_type = COMMAND_ACTION_SERVO_CLOSE;
    cmd.parameters[0] = 1;
    if (xQueueSend(command_queue, &cmd, portMAX_DELAY) != pdPASS) {
      ESP_LOGI(TAG, "Failed to enqueue initial command");
    }
    cmd.target = COMMAND_TARGET_IGNITER;  
    cmd.command_type = COMMAND_ACTION_IGNITER_START;
    if (xQueueSend(command_queue, &cmd, portMAX_DELAY) != pdPASS) {
      ESP_LOGI(TAG, "Failed to enqueue initial command");
    }
    #endif // CONFIG_HOME_SENDER
}

extern "C" void app_main() {
  ESP_LOGI("MAIN", "Starting GINA Control Firmware");
  setup_valves();
  setup_lora_tasks();
  // setup_ignition_relay();
  // set_ignition_relay_high();
  // vTaskDelay(pdMS_TO_TICKS(10000));  // Wait 10s
  // set_ignition_relay_low();

  // setup_valves();

  // open_valve(Valve::kOxRelease);
  // open_valve(Valve::kOxN2Purge);
  // open_valve(Valve::kFuelRelease);

  // vTaskDelay(pdMS_TO_TICKS(1000));  // Wait a second

  // close_valve(Valve::kOxRelease);
  // close_valve(Valve::kOxRelease);
  // close_valve(Valve::kOxN2Purge);
  // close_valve(Valve::kFuelRelease);

  /*
  init_pt_adc_spi();
  while (1) {
    // int64_t start = esp_timer_get_time();
    float psi_chamber = read_pt(Pt::kChamber);
    ESP_LOGI("PT", "Chamber Pressure: %.2f psi", psi_chamber);
    // float psi_eth_line = read_pt(Pt::kEthLine);
    // float psi_eth_n2 = read_pt(Pt::kEthN2Reg);
    // float psi_gox = read_pt(Pt::kGoxLine);
    // float psi_gox_reg = read_pt(Pt::kGoxReg);
    // float psi_ing_eth = read_pt(Pt::kInjectorEth);
    // float psi_inj_gox = read_pt(Pt::kInjectorGox);
    // int64_t end = esp_timer_get_time();
    // int64_t elapsed_us = end - start;
    // printf("Function took %lld us\n", elapsed_us);

    vTaskDelay(pdMS_TO_TICKS(1500));
  }*/
}