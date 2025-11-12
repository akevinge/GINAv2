#ifndef SENSOR_MANAGEMENT_H_
#define SENSOR_MANAGEMENT_H_

typedef struct {
    uint16_t pt_readings[6];
    uint8_t load_cell_reading;
    TickType_t timestamp;
} sensor_data_t;

#define SENSOR_QUEUE_LENGTH 50
#define SENSOR_SAMPLE_RATE_HZ 50
#define SENSOR_SAMPLE_RATE_TICKS (pdMS_TO_TICKS(1000/SENSOR_SAMPLE_RATE_HZ))

#endif  // SENSOR_MANAGEMENT_H_