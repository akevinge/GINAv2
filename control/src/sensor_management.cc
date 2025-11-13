#ifdef CONFIG_AWAY_SENDER
void poll_sensor_task(void* pvParameters) {
  QueueHandle_t sensor_queue = static_cast<QueueHandle_t>(pvParameters);
  TickType_t xLastWakeTime = xTaskGetTickCount();
  while (1) {
    sensor_data_t *data = new sensor_data_t();
    for (int i = 0; i < static_cast<int>(Pt::kPtMax); ++i) {
      //data->pt_readings[i] = read_pt_int(static_cast<Pt>(i));
      data->pt_readings[i] = i;  // Dummy data for testing
    }
    data->load_cell_reading = 0;
    data->timestamp = xTaskGetTickCount();
    // Send sensor data to the queue
    xQueueSendToFront(sensor_queue, data, portMAX_DELAY); // Send to front, we want to prioritize latest data
    vTaskDelayUntil(&xLastWakeTime, SENSOR_SAMPLE_RATE_TICKS);
  }
}
#endif // CONFIG_AWAY_SENDER