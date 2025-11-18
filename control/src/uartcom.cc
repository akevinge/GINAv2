#include "uartcom.h"

#include "configs/uartcom_config.h"
#include "driver/uart.h"
#include "esp_log.h"
#include "lora.h"

static const char* TAG = "UARTCOM";

#ifdef CONFIG_HOME_SENDER
void home_com_monitor_task(void* pvParameters) {
    QueueHandle_t command_queue = static_cast<QueueHandle_t>(pvParameters);
    // UART configuration
    uart_config_t uart_cfg = {.baud_rate = UART_BAUD_RATE,
                            .data_bits = UART_DATA_BITS,
                            .parity = UART_PARITY,
                            .stop_bits = UART_STOP_BITS,
                            .flow_ctrl = UART_FLOW_CTRL};
    
    if (!uart_is_driver_installed(UART_PORT)) {
        uart_driver_install(UART_PORT, UART_RX_BUF_SIZE,
                                      UART_TX_BUF_SIZE, 0, NULL, 0);
    }
    ESP_ERROR_CHECK(uart_param_config(UART_PORT, &uart_cfg));
    ESP_ERROR_CHECK(uart_set_pin(UART_PORT, UART_TX_PIN, UART_RX_PIN,
                               UART_RTS_PIN, UART_CTS_PIN));

    uint8_t buf[256];
    int len = 0;
    int cnt = 0;
    ESP_LOGE(TAG, "Monitor started");

    while (1) {
        // Read bytes from UART0, with a timeout of 100ms
        len = uart_read_bytes(UART_NUM_0, buf, sizeof(buf) - 1,
                            pdMS_TO_TICKS(100));

        if (len > 0) {
            // TODO: Parse command to command_t structure
            command_t command;
            command.target = buf[0];
            command.command_type = buf[1];
            ESP_LOGI(TAG, "Received command from UART: target=%d, type=%d",
                    command.target, command.command_type);
            if(command_queue == NULL) {
                ESP_LOGE(TAG, "Command queue NULL, cannot forward command");
                continue;
            }
            xQueueSendToBack(command_queue, &command, portMAX_DELAY);
        }
    }

    vTaskDelete(NULL);
}
#endif  // CONFIG_HOME_SENDER
