#ifndef LORA_H_
#define LORA_H_
#include "pt.h"
#include "sensor_management.h"

typedef struct {
    sensor_data_t sensor_data;
    TickType_t timestamp;
} telemetry_t;

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