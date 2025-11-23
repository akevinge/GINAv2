#include "sensor_management.h"

#include "load_cell.h"
#include "pt.h"
#include "pt_adc.h"

#ifdef CONFIG_AWAY_SENDER
void poll_sensor_task(void* pvParameters) {
  QueueHandle_t sensor_queue = static_cast<QueueHandle_t>(pvParameters);
  TickType_t xLastWakeTime = xTaskGetTickCount();
  while (1) {
    sensor_data_t data;
    for (int i = 0; i < static_cast<int>(Pt::kPtMax) - 1; ++i) {
      // data.pt_readings[i] = read_pt_int(static_cast<Pt>(i));
      data.pt_readings[i] = 10;
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