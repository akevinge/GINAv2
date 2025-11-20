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

    const size_t batch_overhead = sizeof(telemetry_batch_t);
    const size_t max_packets_per_batch = (LORA_MAX_PAYLOAD_SIZE - batch_overhead) / sizeof(sensor_data_t);
    ESP_LOGI(TAG, "Max packets per batch: %d", (int)max_packets_per_batch);
    const size_t telemetry_size = batch_overhead + max_packets_per_batch * sizeof(sensor_data_t);
    uint8_t *telemetry_buffer = static_cast<uint8_t*>(pvPortMalloc(telemetry_size));

    telemetry_batch_t *telemetry = reinterpret_cast<telemetry_batch_t*>(telemetry_buffer);
    
    TickType_t start_time = xTaskGetTickCount();
    int totalSent = 0;
    while (1){
        size_t packets_in_batch = 0;
        telemetry->count = 0;
        telemetry->batch_timestamp = xTaskGetTickCount();
        sensor_data_t sensor_data;

        while(packets_in_batch < max_packets_per_batch && xQueueReceive(sensor_queue, &sensor_data, pdMS_TO_TICKS(10)) == pdPASS){
            UBaseType_t inqueue = uxQueueMessagesWaiting(sensor_queue);
            ESP_LOGE(TAG, "%d in queue", inqueue);
            
            // Copy sensor data into the batch
            telemetry->packets[packets_in_batch] = sensor_data;
            packets_in_batch++;
            telemetry->count = packets_in_batch;
        }

        // If we received any packets, send the batch
        if (packets_in_batch > 0){
            const size_t batch_size = batch_overhead + packets_in_batch * sizeof(sensor_data_t);
            ESP_LOGI(TAG, "Prepared batch with %d packets, total size %d bytes", (int)packets_in_batch, (int)batch_size);

            totalSent+= packets_in_batch;
            if (LoRaSend((uint8_t*)telemetry, batch_size, SX126x_TXMODE_SYNC) == false){
               ESP_LOGE(pcTaskGetName(NULL), "LoRaSend failed");
            }

            int lost = GetPacketLost();
            if (lost != 0){
                ESP_LOGW(pcTaskGetName(NULL), "Packet lost count: %d", lost);
            }

            TickType_t end_time = xTaskGetTickCount();

            if (end_time - start_time > 100){
                ESP_LOGE(TAG, "Total of %d samples sent over last second", totalSent);
                start_time = xTaskGetTickCount();
                totalSent = 0;
            }

            ESP_LOGI(TAG, "Transmission cycle took %lu ms", (end_time - start_time) * portTICK_PERIOD_MS);
        }
    }

    vTaskDelete(NULL);
}
#endif // CONFIG_AWAY_SENDER

#ifdef CONFIG_HOME_RECEIVER
void home_rx_task(void *pvParameters){
    ESP_LOGI(TAG, "Starting LoRa RX task");
    QueueHandle_t home_sensor_queue = static_cast<QueueHandle_t>(pvParameters);
    uint8_t buf[255];
    TickType_t xLastWakeTime = xTaskGetTickCount();

    // Maximum number of sensor packets that can fit into the fixed LoRa payload
    const size_t max_packets_in_fixed_payload = (LORA_PAYLOAD_LENGTH > sizeof(telemetry_batch_t))
        ? (LORA_PAYLOAD_LENGTH - sizeof(telemetry_batch_t)) / sizeof(sensor_data_t)
        : 0;

    while (1){
        uint8_t recLen = LoRaReceive(buf, sizeof(buf));

        if (recLen == LORA_PAYLOAD_LENGTH) {
            // Expected fixed-size payload: parse telemetry and use the embedded count
            telemetry_batch_t* recieved = reinterpret_cast<telemetry_batch_t*>(buf);

            if (recieved->count > max_packets_in_fixed_payload) {
                ESP_LOGE(pcTaskGetName(NULL), "Telemetry count %d exceeds max packets %d for fixed payload",
                         recieved->count, (int)max_packets_in_fixed_payload);
            } else {
                ESP_LOGI(TAG, "Received batch with %d packets (fixed payload)", recieved->count);
                for (uint8_t i = 0; i < recieved->count; ++i){
                    sensor_data_t& data = recieved->packets[i];
                    ESP_LOGI(TAG, "Packet %d - Timestamp: %u, PT Readings: [%d, %d, %d, %d, %d, %d], Load Cell: %d",
                             i,
                             (unsigned)data.timestamp,
                             data.pt_readings[0],
                             data.pt_readings[1],
                             data.pt_readings[2],
                             data.pt_readings[3],
                             data.pt_readings[4],
                             data.pt_readings[5],
                             data.load_cell_reading);
                    if (home_sensor_queue != NULL) {
                        xQueueSendToBack(home_sensor_queue, &data, portMAX_DELAY);
                    } else {
                        ESP_LOGE(TAG, "Home sensor queue NULL, cannot forward received telemetry");
                    }
                }
            }

            int8_t rssi, snr;
            GetPacketStatus(&rssi, &snr);
            ESP_LOGI(pcTaskGetName(NULL), "Received packet of size %d bytes, RSSI: %d dBm, SNR: %d dB", recLen, rssi, snr);

        } else {
            // Ignore or log too-small packets
            ESP_LOGD(pcTaskGetName(NULL), "Received packet too small to be telemetry: %d bytes", recLen);
        }

        vTaskDelayUntil(&xLastWakeTime, pdMS_TO_TICKS(pdMS_TO_TICKS(1000 / LORA_TRANSFER_RATE_HZ)));
    }

    vTaskDelete(NULL);
}
#endif // CONFIG_HOME_RECEIVER

#ifdef CONFIG_HOME_SENDER
void home_tx_task(void *pvParameters){
    ESP_LOGI(TAG, "Starting HOME TX task");
    QueueHandle_t command_queue = static_cast<QueueHandle_t>(pvParameters);

    if (command_queue == NULL) {
        ESP_LOGE(TAG, "Command queue NULL, killing LoRa TX task");
        vTaskDelete(NULL);
        return;
    }

    while (1){
        command_t command;
        if (xQueueReceive(command_queue, &command, portMAX_DELAY) == pdPASS){
            ESP_LOGI(TAG, "Sending command to target %d, type %d", command.target, command.command_type);
            uint8_t buffer[sizeof(command_t)];
            memcpy(buffer, &command, sizeof(command_t));

            if (LoRaSend(buffer, sizeof(command_t), SX126x_TXMODE_SYNC) == false){
               ESP_LOGE(pcTaskGetName(NULL), "LoRaSend failed");
            } else {
                ESP_LOGI(pcTaskGetName(NULL), "Command sent successfully");
            }
        }
    }

    vTaskDelete(NULL);
}
#endif // CONFIG_HOME_SENDER

#ifdef CONFIG_AWAY_RECEIVER
void away_rx_task(void *pvParameters){
    QueueHandle_t command_queue = static_cast<QueueHandle_t>(pvParameters);

    ESP_LOGI(TAG, "Starting LoRa RX task");
    uint8_t buf[255];
    TickType_t xLastWakeTime = xTaskGetTickCount();
    while (1){
        uint8_t recLen = LoRaReceive(buf, sizeof(buf));
        if (recLen == LORA_PAYLOAD_LENGTH){
            command_t* recieved = reinterpret_cast<command_t*>(buf);
            ESP_LOGI(pcTaskGetName(NULL), "Received command for target %d, type %d", recieved->target, recieved->command_type);
            if (command_queue != NULL) {
                xQueueSendToBack(command_queue, recieved, portMAX_DELAY);
            } else {
                ESP_LOGE(TAG, "Command queue NULL, cannot forward received command");
            }
        } else {
            ESP_LOGE(pcTaskGetName(NULL), "Received packet size mismatch: expected %d bytes but got %d bytes", LORA_PAYLOAD_LENGTH, (int)recLen);
        }
        vTaskDelayUntil(&xLastWakeTime, pdMS_TO_TICKS(pdMS_TO_TICKS(1000 / LORA_TRANSFER_RATE_HZ)));
    }
    vTaskDelete(NULL);
}
#endif // CONFIG_AWAY_RECEIVER

void lora_begin_config(){
    ESP_LOGE(TAG, "Initializing LoRa module...");
    if (LoRaBegin(LORA_FREQUENCY_HZ, LORA_TX_POWER_DBM, LORA_TCXO_VOLTAGE, LORA_USE_REGULATOR_LDO) != 0) {
        ESP_LOGI(TAG, "Module not recognized.");
    } else {
        ESP_LOGE(TAG, "Lora initialized successfully.");
    }
}

void configure_lora(){
    LoRaInit();
    //Driver setup configuration
    lora_begin_config();

    // LoRa transmission configuration - Minimum range + security and maximum rate at 7, 6, 1, 8, 0

    LoRaConfig(LORA_SPREADING_FACTOR, LORA_BANDWIDTH, LORA_CODING_RATE, LORA_PREAMBLE_LENGTH, LORA_PAYLOAD_LENGTH, LORA_CRC_ON, LORA_INVERT_IRQ);
}