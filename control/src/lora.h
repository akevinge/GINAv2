#ifndef LORA_H_
#define LORA_H_
#include "pt.h"
#include "sensor_management.h"

typedef struct {
    uint8_t target;
    uint8_t command_type;
    uint8_t parameters[4];
} command_t;

typedef struct {
    uint8_t count;  // Number of telemetry packets in this batch
    TickType_t batch_timestamp;  // Timestamp for the whole batch
    sensor_data_t packets[0];  // Flexible array member - will hold our telemetry packets
} telemetry_batch_t;

void configure_lora();
#ifdef CONFIG_AWAY_SENDER
void away_tx_task(void *pvParameters);
#endif // CONFIG_AWAY_SENDER

#ifdef CONFIG_AWAY_RECEIVER
void away_rx_task(void *pvParameters);
#endif // CONFIG_AWAY_RECEIVER

#ifdef CONFIG_HOME_SENDER
void home_tx_task(void *pvParameters);
#endif // CONFIG_HOME_SENDER

#ifdef CONFIG_HOME_RECEIVER
void home_rx_task(void *pvParameters);
#endif // CONFIG_HOME_RECEIVER

#endif  // LORA_H_