#include "uartcom.h"

#include "command_handler.h"
#include "configs/uartcom_config.h"
#include "driver/uart.h"
#include "esp_log.h"
#include "lora.h"

typedef enum {
  STATE_WAITING_FOR_SOP,
  STATE_READING_PAYLOAD
} PacketState;

#ifdef CONFIG_HOME_SENDER
void home_com_monitor_task(void* pvParameters) {
  QueueHandle_t command_queue = (QueueHandle_t)pvParameters;

  // UART configuration
  uart_config_t uart_cfg = {.baud_rate = UART_BAUD_RATE,
                            .data_bits = UART_DATA_BITS,
                            .parity = UART_PARITY,
                            .stop_bits = UART_STOP_BITS,
                            .flow_ctrl = UART_FLOW_CTRL};

  ESP_ERROR_CHECK(uart_driver_install(UART_PORT, UART_RX_BUF_SIZE,
                                      UART_TX_BUF_SIZE, 0, NULL, 0));
  ESP_ERROR_CHECK(uart_param_config(UART_PORT, &uart_cfg));
  ESP_ERROR_CHECK(uart_set_pin(UART_PORT, UART_TX_PIN, UART_RX_PIN,
                               UART_RTS_PIN, UART_CTS_PIN));

  PacketState current_state = STATE_WAITING_FOR_SOP;
  unsigned char buf[sizeof(command_t)];
  int bytes_received = 0;
  uint8_t current_byte;

  while (1) {
    // Read bytes from UART0, with a timeout of 100ms
    int bytes_read =
        uart_read_bytes(UART_NUM_0, &current_byte, 1, pdMS_TO_TICKS(100));
    if (bytes_read == 0) {
      continue;
    }

    ESP_LOGI(pcTaskGetName(NULL), "byte: %d", current_byte);

    switch (current_state) {
      case STATE_WAITING_FOR_SOP: {
        ESP_LOGI(pcTaskGetName(NULL), "Waiting for SOP");
        // Found SOP byte, transition into payload read.
        if (current_byte == SOP_BYTE) {
          ESP_LOGI(pcTaskGetName(NULL), "SOP Found");
          current_state = STATE_READING_PAYLOAD;
          bytes_received = 0;
        }
        break;
      }
      case STATE_READING_PAYLOAD: {
        buf[bytes_received] = current_byte;
        bytes_received++;

        if (current_byte == EOP_BYTE) {
          command_t command;
          command.target = buf[0];
          command.command_type = buf[1];
          for (int i = 0; i < 4; i++) {
            command.parameters[i] = buf[2 + i];
          }
          if (xQueueSend(command_queue, &command, portMAX_DELAY) != pdPASS) {
            ESP_LOGI(pcTaskGetName(NULL), "Failed to enqueue command");
          }
          current_state = STATE_WAITING_FOR_SOP;
          bytes_received = 0;
          break;
        }
        else if (bytes_received >= sizeof(command_t)) {
          ESP_LOGW(pcTaskGetName(NULL), "Buffer overflow, resetting state");
          current_state = STATE_WAITING_FOR_SOP;
          bytes_received = 0;
          break;
        }
      }
    }
  }

  vTaskDelete(NULL);
}
#endif  // CONFIG_HOME_SENDER
