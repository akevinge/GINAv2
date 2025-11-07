#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "ignition.h"
#include "pt.h"
#include "pt_adc.h"
#include "valve.h"
#include "lora.h"
#include "sensor_management.h"

static const char *TAG = "MAIN";

#ifdef CONFIG_AWAY_SENDER
void poll_sensor_task(void* pvParameters) {
  QueueHandle_t sensor_queue = static_cast<QueueHandle_t>(pvParameters);
  while (1) {
    sensor_data_t *data = new sensor_data_t();
    for (int i = 0; i < static_cast<int>(Pt::kPtMax); ++i) {
      //data->pt_readings[i] = read_pt_int(static_cast<Pt>(i));
      data->pt_readings[i] = i;  // Dummy data for testing
    }
    ESP_LOGI(TAG, "Polled PT readings");
    data->load_cell_reading = 0;
    data->timestamp = xTaskGetTickCount();
    // Send sensor data to the queue
    xQueueSend(sensor_queue, &data, portMAX_DELAY);

    vTaskDelay(pdMS_TO_TICKS(1000 / SENSOR_SAMPLE_RATE_HZ));  // 100 Hz Sampling Rate
  }
}
#endif // CONFIG_AWAY_SENDER

void setup_lora_tasks(){
  #ifdef CONFIG_AWAY_SENDER
    ESP_LOGI(TAG, "Starting Away Sender Configuration");
    QueueHandle_t sensor_queue;

    sensor_queue = xQueueCreate(50, sizeof(sensor_data_t)); // Queue to hold sensor data

    configure_lora();
    xTaskCreatePinnedToCore(poll_sensor_task, "Poll_Sensor_Task", 4096, (void*)sensor_queue, 5, NULL, tskIDLE_PRIORITY);
    xTaskCreatePinnedToCore(away_tx_task, "LoRa_TX_Task", 8192, (void*)sensor_queue, 5, NULL, 1);
  #endif // CONFIG_AWAY_SENDER
  #ifdef CONFIG_HOME_RECEIVER
    ESP_LOGI(TAG, "Starting Home Receiver Configuration");
    configure_lora();
    xTaskCreatePinnedToCore(home_rx_task, "LoRa_RX_Task", 8192, NULL, 5, NULL, tskNO_AFFINITY);
  #endif // CONFIG_HOME_RECEIVER
  #ifdef CONFIG_AWAY_RECEIVER
    ESP_LOGI(TAG, "Starting Away Receiver Configuration");
    /*
    TODO: Implement receiver task that receives telemetry data and logs it
    */
  #endif // CONFIG_AWAY_RECEIVER
  #ifdef CONFIG_HOME_SENDER
    ESP_LOGI(TAG, "Starting Away Receiver Configuration");
    /*
    TODO: Implement sender task that reads commands from serial and relays to AWAY
    */
  #endif // CONFIG_HOME_SENDER
}

extern "C" void app_main() {
  ESP_LOGI("MAIN", "Starting GINA Control Firmware");
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