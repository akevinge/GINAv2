#include "sensor_management.h"

#include <esp_log.h>

#include "configs/pt_config.h"
#include "load_cell.h"
#include "pt.h"

#ifdef CONFIG_AWAY_SENDER
void poll_sensor_task(void* pvParameters) {
  QueueHandle_t sensor_queue = static_cast<QueueHandle_t>(pvParameters);
  TickType_t xLastWakeTime = xTaskGetTickCount();
  while (1) {
    sensor_data_t data;
    for (int i = 0; i < static_cast<int>(Pt::kPtMax); ++i) {
      data.pt_readings[i] = static_cast<uint16_t>(read_pt(static_cast<Pt>(i)));
      if (data.pt_readings[i] > 10) {
        ESP_LOGI("SM", "HIGH HIGH %d reading: %d PSI", i,
                 static_cast<int>(data.pt_readings[i]));
      }
    }
    data.load_cell_reading = 10;
    data.timestamp = xTaskGetTickCount();
    // Send sensor data to the queue
    xQueueSendToFront(
        sensor_queue, &data,
        portMAX_DELAY);  // Send to front, we want to prioritize latest data
    vTaskDelayUntil(&xLastWakeTime, SENSOR_SAMPLE_RATE_TICKS);
  }
}
#endif  // CONFIG_AWAY_SENDER