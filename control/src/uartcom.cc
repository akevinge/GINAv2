#include "uartcom.h"

#include "command_handler.h"
#include "configs/uartcom_config.h"
#include "driver/uart.h"
#include "esp_log.h"
#include "lora.h"

typedef enum {
  STATE_WAITING_FOR_SOP,
  STATE_READING_PAYLOAD,
  STATE_WAITING_FOR_EOP
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
        // Found SOP byte, transition into payload read.
        if (current_byte == SOP_BYTE) {
          current_state = STATE_READING_PAYLOAD;
          bytes_received = 0;
        }
        break;
      }
      case STATE_READING_PAYLOAD: {
        buf[bytes_received] = current_byte;
        bytes_received++;
        // When max buffer is reached, transition to EOP.
        if (bytes_received == sizeof(command_t)) {
          current_state = STATE_WAITING_FOR_EOP;
        }
        break;
      }
      case STATE_WAITING_FOR_EOP: {
        if (current_byte == EOP_BYTE) {
          command_t* command = reinterpret_cast<command_t*>(buf);
          if (xQueueSend(command_queue, command, portMAX_DELAY) != pdPASS) {
            ESP_LOGE(pcTaskGetName(NULL), "Failed to enqueue command");
          }
        } else {
          // Full payload but EOP byte is bad
          ESP_LOGW(pcTaskGetName(NULL), "Packet EOP mismatch, discarding.");
          // Edge case: The byte we just read *might* be the SOP of the *next*
          // packet.
          if (current_byte == SOP_BYTE) {
            current_state = STATE_READING_PAYLOAD;
            bytes_received = 0;
            continue;  // Go back to reading next byte.
          }
        }

        // In both cases, we restart the read and search for SOP.
        current_state = STATE_WAITING_FOR_SOP;
        bytes_received = 0;
        break;
      }
    }
  }

  vTaskDelete(NULL);
}
#endif  // CONFIG_HOME_SENDER