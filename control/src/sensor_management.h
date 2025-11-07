#ifndef SENSOR_MANAGEMENT_H_
#define SENSOR_MANAGEMENT_H_

typedef struct {
    float pt_readings[6];
    int load_cell_reading;
} sensor_data_t;

#define SENSOR_QUEUE_LENGTH 50
#define SENSOR_SAMPLE_RATE_HZ 100

#endif  // SENSOR_MANAGEMENT_H_