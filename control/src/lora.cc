#include <cstdint>

#include "esp_log.h"
#include "ra01s.h"

#include "lora.h"
#include "configs/lora_config.h"

static const char *TAG = "LoRa";

#ifdef CONFIG_SENDER
void tx_task(void *pvParameters){
    ESP_LOGI(TAG, "Starting LoRa TX task");
    uint8_t payload[255];
    while (1){
        TickType_t startTick = xTaskGetTickCount();
        int txLen = sprintf((char*)payload, "Hello from LoRa TX at tick %u", (unsigned int)startTick);
        ESP_LOGI(TAG, "Packet of size %d bytes sent", txLen);

        if (LoRaSend(payload, txLen, SX126x_TXMODE_SYNC) == false){
           ESP_LOGE(pcTaskGetName(NULL), "LoRaSend failed"); 
        }

        int lost = GetPacketLost();
        if (lost != 0){
            ESP_LOGW(pcTaskGetName(NULL), "Packet lost count: %d", lost);
        }

        vTaskDelay(pdMS_TO_TICKS(1000));
    }

    vTaskDelete(NULL);
}
#endif // CONFIG_SENDER

#ifndef CONFIG_SENDER
void rx_task(void *pvParameters){
    ESP_LOGI(TAG, "Starting LoRa RX task");
    uint8_t buf[255];
    while (1){
        uint8_t recLen = LoRaReceive(buf, sizeof(buf));
        if (recLen > 0){
            ESP_LOGI(pcTaskGetName(NULL), "Received packet: %.*s", recLen, buf);

            int8_t rssi, snr;
            GetPacketStatus(&rssi, &snr);
            ESP_LOGI(pcTaskGetName(NULL), "Received packet of size %d bytes, RSSI: %d dBm, SNR: %d dB", recLen, rssi, snr);
        }

        vTaskDelay(pdMS_TO_TICKS(1000));
    }

    vTaskDelete(NULL);
}
#endif // !CONFIG_SENDER

void demo_main(){
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

#ifdef CONFIG_SENDER
    ESP_LOGI(TAG, "Creating LoRa TX task");
    xTaskCreate(tx_task, "LoRa_TX_Task", 4096, NULL, 5, NULL);
#endif
#ifndef CONFIG_SENDER
    ESP_LOGI(TAG, "Creating LoRa TX task");
    xTaskCreate(rx_task, "LoRa_RX_Task", 4096, NULL, 5, NULL);
#endif
}