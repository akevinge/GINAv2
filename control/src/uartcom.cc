#include "uartcom.h"

#include "configs/uartcom_config.h"
#include "driver/uart.h"
#include "esp_log.h"
#include "lora.h"

static const char* TAG = "UARTCOM";

#ifdef CONFIG_HOME_SENDER
void home_com_monitor_task(void* pvParameters) {
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

  char buf[256];
  int len = 0;

  while (1) {
    // Read bytes from UART0, with a timeout of 100ms
    len = uart_read_bytes(UART_NUM_0, (uint8_t*)buf, sizeof(buf) - 1,
                          pdMS_TO_TICKS(100));

    if (len > 0) {
      buf[len] = '\0';  // Null terminate
      ESP_LOGI(pcTaskGetName(NULL), "Received command: %s", buf);

      // TODO: Parse command to command_t structure
      command_t command;
      command.address = 0x01;       // Example address
      command.target = 0x02;        // Example target
      command.command_type = 0x03;  // Example command type

      // TODO: Send command to LoRa TX task
    }
  }

  vTaskDelete(NULL);
}
#endif  // CONFIG_HOME_SENDER
