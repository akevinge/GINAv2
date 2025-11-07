#include <cstdint>
#include <cmath>

#include "esp_log.h"
#include "ra01s.h"

#include "lora.h"
#include "configs/lora_config.h"

static const char *TAG = "LoRa";

#ifdef CONFIG_AWAY_SENDER
void away_tx_task(void *pvParameters){
    ESP_LOGI(TAG, "Starting LoRa TX task");

    QueueHandle_t sensor_queue = static_cast<QueueHandle_t>(pvParameters);
    if (sensor_queue == NULL) {
        ESP_LOGE(TAG, "Sensor queue NULL, killing LoRa TX task");
        vTaskDelete(NULL);
        return;
    }

    while (1){
        sensor_data_t sensor_data;

        // Block until at least one item is available
        if (xQueueReceive(sensor_queue, &sensor_data, portMAX_DELAY) != pdTRUE){
            ESP_LOGE(pcTaskGetName(NULL), "Failed to receive from sensor queue");
            continue;
        }

        size_t sent_this_cycle = 0;

        // Process the first item we just received, then drain the rest with non-blocking receives
        do {
            telemetry_t telemetry = {
                .sensor_data = sensor_data,
                .timestamp = xTaskGetTickCount()
            };
            ESP_LOGI(TAG, "Sending packet of size %d bytes", (int)sizeof(telemetry));

            if (LoRaSend((uint8_t*)&telemetry, sizeof(telemetry), SX126x_TXMODE_SYNC) == false){
               ESP_LOGE(pcTaskGetName(NULL), "LoRaSend failed");
            }

            int lost = GetPacketLost();
            if (lost != 0){
                ESP_LOGW(pcTaskGetName(NULL), "Packet lost count: %d", lost);
            }

            sent_this_cycle++;
            // If we've reached the safety cap, stop draining further this cycle
            if (sent_this_cycle >= MAX_DRAIN_PER_CYCLE) {
                ESP_LOGW(TAG, "Drained %d packets this cycle (cap reached). Will continue on next cycle.", (int)sent_this_cycle);
                break;
            }

            // Radio duty-cycle interrupt
            if (INTER_PACKET_DELAY_TICKS > 0) {
                vTaskDelay(INTER_PACKET_DELAY_TICKS);
            } else {
                taskYIELD();
            }

            // Try pull next item without blocking
        } while (xQueueReceive(sensor_queue, &sensor_data, 0) == pdTRUE);

        vTaskDelay(1000 / LORA_TRANSFER_RATE_HZ);
    }

    vTaskDelete(NULL);
}
#endif // CONFIG_AWAY_SENDER

#ifdef CONFIG_HOME_RECEIVER
void home_rx_task(void *pvParameters){
    ESP_LOGI(TAG, "Starting LoRa RX task");
    uint8_t buf[255];
    while (1){
        uint8_t recLen = LoRaReceive(buf, sizeof(buf));
        if (recLen > 0){
            ESP_LOGI(pcTaskGetName(NULL), "Received packet");
            telemetry_t recieved;
            memcpy(&recieved, buf, sizeof(telemetry_t));

            ESP_LOGI(TAG, "Telemetry Data - Timestamp: %u, PT Readings: [%.2f, %.2f, %.2f, %.2f, %.2f, %.2f], Load Cell: %d",
                     recieved.timestamp,
                     recieved.sensor_data.pt_readings[0],
                     recieved.sensor_data.pt_readings[1],
                     recieved.sensor_data.pt_readings[2],
                     recieved.sensor_data.pt_readings[3],
                     recieved.sensor_data.pt_readings[4],
                     recieved.sensor_data.pt_readings[5],
                     recieved.sensor_data.load_cell_reading);

            int8_t rssi, snr;
            GetPacketStatus(&rssi, &snr);
            ESP_LOGI(pcTaskGetName(NULL), "Received packet of size %d bytes, RSSI: %d dBm, SNR: %d dB", recLen, rssi, snr);
        }

        vTaskDelay(pdMS_TO_TICKS(1000));
    }

    vTaskDelete(NULL);
}
#endif // CONFIG_HOME_RECEIVER

void configure_lora(){
    LoRaInit();
    //Driver setup configuration
    int8_t txPowerInDbm = 22;
    int32_t frequencyInHz = 433000000;
    float tcxoVoltage = 3.3;
    bool useRegulatorLDO = true;

    ESP_LOGE(TAG, "Initializing LoRa module...");
    if (LoRaBegin(frequencyInHz, txPowerInDbm, tcxoVoltage, useRegulatorLDO) != 0) {
        ESP_LOGI(TAG, "Module not recognized.");
    } else {
        ESP_LOGE(TAG, "Lora initialized successfully.");
    }

    // LoRa transmission configuration
    uint8_t spreadingFactor = 7;
    uint8_t bandwidth = 4;
    uint8_t codingRate = 1;
    uint16_t preambleLength = 8;
    uint8_t payloadLen = 0;
    bool crcOn = true;
    bool invertIrq = false;

    LoRaConfig(spreadingFactor, bandwidth, codingRate, preambleLength, payloadLen, crcOn, invertIrq);
}