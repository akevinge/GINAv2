#ifndef SENSOR_MANAGEMENT_H_
#define SENSOR_MANAGEMENT_H_

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

typedef struct {
    uint16_t pt_readings[6];
    uint8_t load_cell_reading;
    TickType_t timestamp;
} sensor_data_t;

#ifdef CONFIG_AWAY_SENDER
void poll_sensor_task(void* pvParameters);
#endif //CONFIG_AWAY_SENDER

#define SENSOR_QUEUE_LENGTH 50
#define SENSOR_SAMPLE_RATE_HZ 50
#define SENSOR_SAMPLE_RATE_TICKS (pdMS_TO_TICKS(1000/SENSOR_SAMPLE_RATE_HZ))

#endif  // SENSOR_MANAGEMENT_H_